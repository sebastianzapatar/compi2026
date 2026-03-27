# =============================================================================
# evaluator.py — Evaluador del AST (Tree-Walking Interpreter)
#
# El Evaluador recorre el AST nodo por nodo y ejecuta el programa.
# Es un "evaluador por recorrido del árbol" (tree-walking interpreter):
# no compila a bytecode ni a código máquina, sino que interpreta
# directamente los nodos del AST.
#
# Función principal: evaluate(node, env)
#   - node: cualquier nodo del AST (Program, LetStatement, InfixExpression…)
#   - env:  el Environment actual (tabla de variables vigentes)
#   - Retorna: un Object del sistema de objetos (Integer, String, Boolean…)
#
# Manejo de control de flujo especial:
#   - 'return': se propaga como ReturnValue hasta salir de la función.
#   - Errores: se propagan como Error hasta el nivel más alto.
#   - 'break'/'continue': se señalizan con objetos especiales internos.
# =============================================================================

from typing import List, Optional

from laurasefue import ast
from laurasefue.object_system import (
    Object, ObjectType, Environment,
    Integer, Float, String, Boolean, Null, ReturnValue, Error, Function,
    TRUE, FALSE, NULL
)


# ─────────────────────────────────────────────────────────────────────────────
# SEÑALES INTERNAS DE CONTROL DE FLUJO
# Estas clases no son parte del sistema de objetos del usuario; son solo
# señales que el evaluador usa para propagar break y continue entre funciones.
# ─────────────────────────────────────────────────────────────────────────────

class _BreakSignal(Object):
    """Señal interna para propagar 'break' fuera de un bucle."""
    def object_type(self): return ObjectType.NULL
    def inspect(self): return 'break'

class _ContinueSignal(Object):
    """Señal interna para propagar 'continue' al siguiente ciclo."""
    def object_type(self): return ObjectType.NULL
    def inspect(self): return 'continue'

# Instancias únicas (singletons) para eficiencia
_BREAK    = _BreakSignal()
_CONTINUE = _ContinueSignal()


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(node: ast.Node, env: Environment) -> Optional[Object]:
    """
    Evalúa un nodo del AST en el contexto del entorno dado y retorna un Object.

    Este es el punto de entrada recursivo del evaluador. Cada tipo de nodo
    tiene su propia lógica de evaluación.

    Parámetros:
      node: el nodo del AST a evaluar
      env:  el entorno de ejecución actual (variables, funciones)

    Retorna:
      Un Object con el resultado de la evaluación,
      o None si el nodo no produce valor (raro, solo en casos de error).
    """

    # ── Nodo raíz: el programa completo ──────────────────────────────────────
    if isinstance(node, ast.Program):
        return _evaluate_program(node, env)

    # ── Bloque de sentencias: { stmt; stmt; ... } ─────────────────────────────
    if isinstance(node, ast.BlockStatement):
        return _evaluate_block_statement(node, env)

    # ── Sentencia de expresión: expr; ────────────────────────────────────────
    if isinstance(node, ast.ExpressionStatement):
        return evaluate(node.expression, env)

    # ── Declaración de variable: let x = expr; ───────────────────────────────
    if isinstance(node, ast.LetStatement):
        return _evaluate_let_statement(node, env)

    # ── Retorno de valor: return expr; ───────────────────────────────────────
    if isinstance(node, ast.ReturnStatement):
        val = evaluate(node.return_value, env)
        if _is_error(val):
            return val
        return ReturnValue(val)   # Envuelve el valor para propagarlo

    # ── Sentencia print: print(expr); ────────────────────────────────────────
    if isinstance(node, ast.PrintStatement):
        val = evaluate(node.value, env)
        if _is_error(val):
            return val
        print(val.inspect())     # Imprime el valor en la consola del sistema
        return NULL

    # ── Sentencia while ───────────────────────────────────────────────────────
    if isinstance(node, ast.WhileStatement):
        return _evaluate_while_statement(node, env)

    # ── Sentencia for ─────────────────────────────────────────────────────────
    if isinstance(node, ast.ForStatement):
        return _evaluate_for_statement(node, env)

    # ── Break: interrumpe el bucle más cercano ────────────────────────────────
    if isinstance(node, ast.BreakStatement):
        return _BREAK

    # ── Continue: salta al siguiente ciclo del bucle ──────────────────────────
    if isinstance(node, ast.ContinueStatement):
        return _CONTINUE


    # ── Literales ─────────────────────────────────────────────────────────────
    if isinstance(node, ast.IntegerLiteral):
        return Integer(node.value)

    if isinstance(node, ast.FloatLiteral):
        return Float(node.value)

    if isinstance(node, ast.StringLiteral):
        return String(node.value)

    if isinstance(node, ast.BooleanLiteral):
        # Reutilizamos los singletons TRUE y FALSE para eficiencia
        return TRUE if node.value else FALSE

    # ── Identificador (nombre de variable) ────────────────────────────────────
    if isinstance(node, ast.Identifier):
        return _evaluate_identifier(node, env)

    # ── Expresión prefija: !expr  o  -expr ────────────────────────────────────
    if isinstance(node, ast.PrefixExpression):
        right = evaluate(node.right, env)
        if _is_error(right):
            return right
        return _evaluate_prefix_expression(node.operator, right)

    # ── Expresión infija: left OP right ───────────────────────────────────────
    if isinstance(node, ast.InfixExpression):
        left = evaluate(node.left, env)
        if _is_error(left):
            return left
        right = evaluate(node.right, env)
        if _is_error(right):
            return right
        return _evaluate_infix_expression(node.operator, left, right)

    # ── Condicional: if (...) { } elseif (...) { } else { } ─────────────────
    if isinstance(node, ast.IfExpression):
        return _evaluate_if_expression(node, env)

    # ── Definición de función: function(params) { body } ─────────────────────
    if isinstance(node, ast.FunctionLiteral):
        # Crea un objeto Function capturando el entorno actual (closure)
        fn = Function(
            parameters=node.parameters,
            body=node.body,
            env=env,
            name=node.name
        )
        # Si la función tiene nombre, la registramos en su propio entorno
        # para que pueda llamarse a sí misma recursivamente.
        if node.name:
            env.set(node.name, fn)
        return fn

    # ── Llamada a función: func(args) ─────────────────────────────────────────
    if isinstance(node, ast.CallExpression):
        return _evaluate_call_expression(node, env)

    # ── Si el nodo no es reconocido, retorna NULL ─────────────────────────────
    return NULL


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIÓN DEL PROGRAMA Y BLOQUES
# ─────────────────────────────────────────────────────────────────────────────

def _evaluate_program(program: ast.Program, env: Environment) -> Optional[Object]:
    """
    Evalúa todas las sentencias del programa en orden.

    Si alguna sentencia produce un ReturnValue, interrumpe la ejecución
    y desenvuelve el valor interno (return a nivel global).
    Si produce un Error, lo propaga inmediatamente.
    De lo contrario, continúa con la siguiente sentencia.
    """
    result: Optional[Object] = None

    for statement in program.statements:
        result = evaluate(statement, env)

        # Si la sentencia produjo un retorno → extrae el valor y para
        if isinstance(result, ReturnValue):
            return result.value

        # Si hubo un error → para inmediatamente
        if isinstance(result, Error):
            return result

    return result


def _evaluate_block_statement(block: ast.BlockStatement, env: Environment) -> Optional[Object]:
    """
    Evalúa un bloque { ... } pero SIN desenvolver el ReturnValue.

    A diferencia de _evaluate_program, aquí propagamos el ReturnValue
    hacia arriba sin desempaquetarlo, para que el evaluador de la llamada
    a función pueda detectarlo y detener la ejecución.
    """
    result: Optional[Object] = None

    for statement in block.statements:
        result = evaluate(statement, env)

        if result is not None:
            rt = result.object_type()
            # Si es ReturnValue o Error, lo propagamos sin seguir evaluando
            if rt == ObjectType.RETURN_VALUE or rt == ObjectType.ERROR:
                return result
            # Señales de control de flujo (break / continue)
            if isinstance(result, (_BreakSignal, _ContinueSignal)):
                return result

    return result


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIÓN DE SENTENCIAS ESPECÍFICAS
# ─────────────────────────────────────────────────────────────────────────────

def _evaluate_let_statement(node: ast.LetStatement, env: Environment) -> Optional[Object]:
    """
    Evalúa: let <nombre> = <expresión>;

    Evalúa la expresión del lado derecho y guarda el resultado en el entorno
    con el nombre de la variable.
    """
    val = evaluate(node.value, env)
    if _is_error(val):
        return val
    env.set(node.name.value, val)
    return NULL


def _evaluate_identifier(node: ast.Identifier, env: Environment) -> Object:
    """
    Evalúa un identificador buscándolo en el entorno.

    Si no existe en el entorno, verifica si es 'break' o 'continue'
    (señales especiales de control de flujo).
    Si no se encuentra, retorna un Error.
    """
    # Señales especiales de control de flujo
    if node.value == 'break':
        return _BREAK
    if node.value == 'continue':
        return _CONTINUE

    # Busca la variable en el entorno (y en entornos padre)
    val = env.get(node.value)
    if val is not None:
        return val

    return Error(f'variable no definida: "{node.value}"')


def _evaluate_while_statement(node: ast.WhileStatement, env: Environment) -> Object:
    """
    Evalúa: while (<condición>) { <cuerpo> }

    En cada iteración:
      1. Evalúa la condición.
      2. Si es verdadera, evalúa el cuerpo.
      3. Si el cuerpo produce break → sale del bucle.
      4. Si produce continue → salta al inicio del bucle.
      5. Si produce return o error → lo propaga.
    """
    while True:
        # Evalúa la condición del bucle
        condition = evaluate(node.condition, env)
        if _is_error(condition):
            return condition

        # Si la condición es falsa, termina el bucle
        if not _is_truthy(condition):
            break

        # Evalúa el cuerpo del bucle
        result = _evaluate_block_statement(node.body, env)

        if result is not None:
            # Break: sale del bucle
            if isinstance(result, _BreakSignal):
                break
            # Continue: salta al inicio del bucle (la condición se re-evalúa)
            if isinstance(result, _ContinueSignal):
                continue
            # Return o error: propaga hacia arriba
            if (result.object_type() == ObjectType.RETURN_VALUE or
                    result.object_type() == ObjectType.ERROR):
                return result

    return NULL


def _evaluate_for_statement(node: ast.ForStatement, env: Environment) -> Object:
    """
    Evalúa: for (<init>; <condición>; <actualización>) { <cuerpo> }

    El init se evalúa UNA sola vez antes del bucle.
    La condición y el update se evalúan en cada iteración.
    """
    # Crea un entorno local para el for (para que let i sea local al bucle)
    for_env = Environment.new_enclosed(env)

    # Evalúa la inicialización (e.g. let i = 0)
    if node.init is not None:
        result = evaluate(node.init, for_env)
        if _is_error(result):
            return result

    while True:
        # Evalúa la condición (si no hay, es bucle infinito)
        if node.condition is not None:
            condition = evaluate(node.condition, for_env)
            if _is_error(condition):
                return condition
            if not _is_truthy(condition):
                break   # Condición falsa: termina el bucle

        # Evalúa el cuerpo
        result = _evaluate_block_statement(node.body, for_env)

        if result is not None:
            if isinstance(result, _BreakSignal):
                break
            if isinstance(result, _ContinueSignal):
                pass   # "continue" va directo al update
            elif (result.object_type() == ObjectType.RETURN_VALUE or
                  result.object_type() == ObjectType.ERROR):
                return result

        # Evalúa la actualización (e.g. let i = i + 1)
        if node.update is not None:
            upd = evaluate(node.update, for_env)
            if _is_error(upd):
                return upd

    return NULL


# ─────────────────────────────────────────────────────────────────────────────
# EVALUACIÓN DE EXPRESIONES
# ─────────────────────────────────────────────────────────────────────────────

def _evaluate_prefix_expression(operator: str, right: Object) -> Object:
    """
    Evalúa una expresión prefija: !expr  o  -expr

    Operadores:
      '!'  → aplica negación booleana
      '-'  → cambia el signo de un número
    """
    match operator:
        case '!':
            return _evaluate_bang_operator(right)
        case '-':
            return _evaluate_minus_prefix_operator(right)
        case _:
            return Error(f'Operador prefijo desconocido: {operator}')


def _evaluate_bang_operator(right: Object) -> Boolean:
    """
    Evalúa el operador de negación !.

    Reglas de truthiness:
      !false  → true
      !null   → true
      !todo_lo_demás → false  (incluyendo 0, "", true)
    """
    if right is FALSE:
        return TRUE
    if right is NULL:
        return TRUE
    return FALSE


def _evaluate_minus_prefix_operator(right: Object) -> Object:
    """
    Evalúa el operador unario de cambio de signo -.

    Solo aplica a números. Ejemplo: -5 → Integer(-5)
    """
    if isinstance(right, Integer):
        return Integer(-right.value)
    if isinstance(right, Float):
        return Float(-right.value)
    return Error(
        f'Operador "-" no soportado para el tipo {right.object_type().value}'
    )


def _evaluate_infix_expression(operator: str, left: Object, right: Object) -> Object:
    """
    Evalúa una expresión infija: left OP right

    Delega según los tipos de left y right para manejar la aritmética,
    la concatenación de strings, las comparaciones y los operadores lógicos.
    """
    # ── Operaciones entre dos enteros ─────────────────────────────────────────
    if isinstance(left, Integer) and isinstance(right, Integer):
        return _evaluate_integer_infix(operator, left, right)

    # ── Operaciones con flotantes (o mixto int+float) ─────────────────────────
    if isinstance(left, (Integer, Float)) and isinstance(right, (Integer, Float)):
        return _evaluate_float_infix(
            operator,
            Float(float(left.value)),
            Float(float(right.value))
        )

    # ── Operaciones con strings ────────────────────────────────────────────────
    if isinstance(left, String) and isinstance(right, String):
        return _evaluate_string_infix(operator, left, right)

    # ── Comparación de booleanos (== y !=) ────────────────────────────────────
    if operator == '==':
        return _python_bool_to_boolean(left is right)
    if operator == '!=':
        return _python_bool_to_boolean(left is not right)

    # ── Operadores lógicos 'and' y 'or' (short-circuit) ──────────────────────
    if operator == 'and':
        # Retorna False si el izquierdo es falsy; si no, el valor derecho
        if not _is_truthy(left):
            return FALSE
        return TRUE if _is_truthy(right) else FALSE

    if operator == 'or':
        # Retorna True si cualquiera es truthy
        if _is_truthy(left):
            return TRUE
        return TRUE if _is_truthy(right) else FALSE

    # ── Tipos incompatibles ────────────────────────────────────────────────────
    if left.object_type() != right.object_type():
        return Error(
            f'Tipos incompatibles: '
            f'{left.object_type().value} {operator} {right.object_type().value}'
        )

    return Error(
        f'Operador "{operator}" no soportado entre '
        f'{left.object_type().value} y {right.object_type().value}'
    )


def _evaluate_integer_infix(operator: str, left: Integer, right: Integer) -> Object:
    """
    Evalúa operaciones entre dos enteros.

    Soporta: +, -, *, /, %, ^ y comparaciones.
    La división por cero se detecta y genera un Error.
    La potencia (^) retorna entero si el exponente es positivo,
    float si es negativo.
    """
    lv, rv = left.value, right.value

    match operator:
        case '+':  return Integer(lv + rv)
        case '-':  return Integer(lv - rv)
        case '*':  return Integer(lv * rv)
        case '/':
            if rv == 0:
                return Error('División por cero')
            return Float(lv / rv)   # La división siempre produce float
        case '%':
            if rv == 0:
                return Error('Módulo por cero')
            return Integer(lv % rv)
        case '^':  return Integer(lv ** rv) if rv >= 0 else Float(lv ** rv)
        case '<':  return _python_bool_to_boolean(lv <  rv)
        case '<=': return _python_bool_to_boolean(lv <= rv)
        case '>':  return _python_bool_to_boolean(lv >  rv)
        case '>=': return _python_bool_to_boolean(lv >= rv)
        case '==': return _python_bool_to_boolean(lv == rv)
        case '!=': return _python_bool_to_boolean(lv != rv)
        case _:    return Error(f'Operador desconocido para enteros: {operator}')


def _evaluate_float_infix(operator: str, left: Float, right: Float) -> Object:
    """
    Evalúa operaciones entre dos flotantes (o int+float mixtos).
    """
    lv, rv = left.value, right.value

    match operator:
        case '+':  return Float(lv + rv)
        case '-':  return Float(lv - rv)
        case '*':  return Float(lv * rv)
        case '/':
            if rv == 0.0:
                return Error('División por cero')
            return Float(lv / rv)
        case '%':  return Float(lv % rv)
        case '^':  return Float(lv ** rv)
        case '<':  return _python_bool_to_boolean(lv <  rv)
        case '<=': return _python_bool_to_boolean(lv <= rv)
        case '>':  return _python_bool_to_boolean(lv >  rv)
        case '>=': return _python_bool_to_boolean(lv >= rv)
        case '==': return _python_bool_to_boolean(lv == rv)
        case '!=': return _python_bool_to_boolean(lv != rv)
        case _:    return Error(f'Operador desconocido para flotantes: {operator}')


def _evaluate_string_infix(operator: str, left: String, right: String) -> Object:
    """
    Evalúa operaciones entre dos strings.

    Soporta:
      +   → concatenación
      ==  → comparación de igualdad
      !=  → comparación de diferencia
    """
    match operator:
        case '+':  return String(left.value + right.value)
        case '==': return _python_bool_to_boolean(left.value == right.value)
        case '!=': return _python_bool_to_boolean(left.value != right.value)
        case _:
            return Error(
                f'Operador "{operator}" no soportado entre strings'
            )


def _evaluate_if_expression(node: ast.IfExpression, env: Environment) -> Object:
    """
    Evalúa: if (...) { } elseif (...) { } else { }

    Evalúa la condición principal; si es verdadera, evalúa el bloque if.
    Luego revisa cada rama elseif en orden.
    Si ninguna condición es verdadera, evalúa el bloque else (si existe).
    """
    condition = evaluate(node.condition, env)
    if _is_error(condition):
        return condition

    # Condición principal es verdadera
    if _is_truthy(condition):
        return _evaluate_block_statement(node.consequence, env)

    # Revisar ramas elseif en orden
    for alt_condition, alt_block in node.alternatives:
        alt_val = evaluate(alt_condition, env)
        if _is_error(alt_val):
            return alt_val
        if _is_truthy(alt_val):
            return _evaluate_block_statement(alt_block, env)

    # Bloque else final
    if node.else_block is not None:
        return _evaluate_block_statement(node.else_block, env)

    return NULL


def _evaluate_call_expression(node: ast.CallExpression, env: Environment) -> Object:
    """
    Evalúa una llamada a función: func(args)

    Proceso:
      1. Evalúa la expresión función (puede ser un Identifier o FunctionLiteral).
      2. Evalúa cada argumento real.
      3. Crea un entorno nuevo extendido del entorno capturado por la función.
      4. Enlaza cada parámetro formal con su argumento real.
      5. Evalúa el cuerpo de la función en ese entorno.
      6. Desenvuelve el ReturnValue si lo hay.

    La recursión funciona porque:
      - La función guarda su propio entorno (closure).
      - Al llamarse, se crea un nuevo entorno hijo con los nuevos parámetros.
      - La función puede encontrar su propio nombre en el entorno padre.
    """
    # Paso 1: evalúa la función
    function = evaluate(node.function, env)
    if _is_error(function):
        return function

    if not isinstance(function, Function):
        return Error(
            f'"{node.function}" no es una función '
            f'(es {function.object_type().value})'
        )

    # Paso 2: evalúa los argumentos reales
    args = _evaluate_expressions(node.arguments, env)
    if len(args) == 1 and _is_error(args[0]):
        return args[0]

    # Paso 3: crea un entorno nuevo enlazado al entorno de la función (closure)
    extended_env = _extend_function_env(function, args)
    if isinstance(extended_env, Error):
        return extended_env

    # Paso 4 (ya hecho en _extend_function_env): parámetros enlazados

    # Si la función tiene nombre, la registramos en el entorno extendido
    # para que pueda llamarse a sí misma (soporte de recursión explícito)
    if function.name:
        extended_env.set(function.name, function)

    # Paso 5: evalúa el cuerpo de la función
    evaluated = _evaluate_block_statement(function.body, extended_env)

    # Paso 6: desenvuelve el ReturnValue
    if isinstance(evaluated, ReturnValue):
        return evaluated.value

    return evaluated if evaluated is not None else NULL


def _evaluate_expressions(
    expressions: List[ast.Expression],
    env: Environment
) -> List[Object]:
    """
    Evalúa una lista de expresiones (argumentos de una función) en orden.

    Si alguna expresión produce un error, detiene la evaluación y retorna
    una lista con solo ese error.
    """
    result: List[Object] = []

    for expr in expressions:
        evaluated = evaluate(expr, env)
        if _is_error(evaluated):
            return [evaluated]   # Retorna solo el error
        result.append(evaluated)

    return result


def _extend_function_env(function: Function, args: List[Object]) -> Environment:
    """
    Crea un nuevo entorno para la ejecución de una función.

    Extiende el entorno capturado por la función (closure) y enlaza
    cada parámetro formal con el argumento real correspondiente.

    Ejemplo:
      función: function(x, y) { ... }   con entorno_global
      args: [Integer(3), Integer(5)]
      → nuevo entorno con outer=entorno_global, x=3, y=5
    """
    env = Environment.new_enclosed(function.env)

    if len(args) != len(function.parameters):
        return Error(
            f'Número incorrecto de argumentos: '
            f'se esperaban {len(function.parameters)}, '
            f'se recibieron {len(args)}'
        )

    # Enlaza cada parámetro formal con su argumento real
    for param, arg in zip(function.parameters, args):
        env.set(param.value, arg)

    return env


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────

def _is_truthy(obj: Object) -> bool:
    """
    Determina si un objeto es "verdadero" (truthy) para condicionales y bucles.

    Reglas:
      - null  → False
      - false → False
      - 0     → False (entero cero)
      - 0.0   → False (flotante cero)
      - ""    → False (string vacío)
      - todo lo demás → True
    """
    if obj is NULL:
        return False
    if obj is FALSE:
        return False
    if isinstance(obj, Integer) and obj.value == 0:
        return False
    if isinstance(obj, Float) and obj.value == 0.0:
        return False
    if isinstance(obj, String) and obj.value == '':
        return False
    return True


def _is_error(obj: Optional[Object]) -> bool:
    """
    Verifica si un objeto es un Error.

    Se usa en cada paso del evaluador para propagar errores inmediatamente
    sin continuar evaluando el resto de la expresión.
    """
    return obj is not None and obj.object_type() == ObjectType.ERROR


def _python_bool_to_boolean(value: bool) -> Boolean:
    """
    Convierte un bool de Python a los singletons TRUE o FALSE del lenguaje.

    Usar singletons garantiza que `true == true` funcione por identidad (is)
    en lugar de tener que comparar atributos .value.
    """
    return TRUE if value else FALSE
