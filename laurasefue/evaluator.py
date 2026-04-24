# =============================================================================
# evaluator.py — Evaluador del Intérprete (Tree-Walking Interpreter)
#
# El Evaluador es el corazón del intérprete. Recorre el AST de arriba a abajo
# (tree-walking) y ejecuta cada nodo según su tipo.
#
# Flujo completo:
#   Código fuente
#     ↓  Lexer
#   Tokens
#     ↓  Parser
#   AST
#     ↓  Evaluator   ← este módulo
#   Resultado (Object)
#
# Operaciones soportadas:
#   Aritméticas : +  -  *  /  %  ^  (y prefijo -)
#   Comparación : ==  !=  <  <=  >  >=
#   Agrupamiento: (expresiones entre paréntesis, manejadas por el parser)
#   Lógicas     : and  or  ! (NOT prefijo)
#   Strings     : + (concatenación)
#   Control     : if/elseif/else · while · for · break · continue · return
#   Variables   : let · identificadores
#   Funciones   : definición · llamada · closures · recursión
#   Salida      : print
# =============================================================================

from typing import List, Optional

from laurasefue import ast
from laurasefue.object_system import (
    Object, ObjectType,
    Integer, Float, Boolean, String, Null, Error,
    ReturnValue, Function,
    BreakSignal, ContinueSignal,
    TRUE, FALSE, NULL, BREAK_SIGNAL, CONTINUE_SIGNAL,
)
from laurasefue.environment import Environment, new_enclosed_environment


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL DE EVALUACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def evaluate(node: ast.Node, env: Environment) -> Object:
    """
    Punto de entrada del evaluador.

    Despacha la evaluación al handler correcto según el tipo de nodo.
    Implementa el patrón visitor sin clases: una gran función de despacho.

    Parámetros:
      node  → nodo del AST a evaluar
      env   → entorno de ejecución actual (variables accesibles)

    Retorna un Object: el resultado de evaluar el nodo.
    """

    # ── Nodo raíz ─────────────────────────────────────────────────────────────
    if isinstance(node, ast.Program):
        return _eval_program(node, env)

    # ── Sentencias ────────────────────────────────────────────────────────────
    if isinstance(node, ast.ExpressionStatement):
        return evaluate(node.expression, env)

    if isinstance(node, ast.BlockStatement):
        return _eval_block_statement(node, env)

    if isinstance(node, ast.LetStatement):
        return _eval_let_statement(node, env)

    if isinstance(node, ast.ReturnStatement):
        return _eval_return_statement(node, env)

    if isinstance(node, ast.PrintStatement):
        return _eval_print_statement(node, env)

    if isinstance(node, ast.WhileStatement):
        return _eval_while_statement(node, env)

    if isinstance(node, ast.ForStatement):
        return _eval_for_statement(node, env)

    if isinstance(node, ast.BreakStatement):
        return BREAK_SIGNAL

    if isinstance(node, ast.ContinueStatement):
        return CONTINUE_SIGNAL

    # ── Literales ─────────────────────────────────────────────────────────────
    if isinstance(node, ast.IntegerLiteral):
        return Integer(node.value)

    if isinstance(node, ast.FloatLiteral):
        return Float(node.value)

    if isinstance(node, ast.StringLiteral):
        return String(node.value)

    if isinstance(node, ast.BooleanLiteral):
        # Reutilizar singletons para no crear objetos redundantes
        return TRUE if node.value else FALSE

    # ── Expresiones compuestas ────────────────────────────────────────────────
    if isinstance(node, ast.PrefixExpression):
        right = evaluate(node.right, env)
        if _is_error(right):
            return right
        return _eval_prefix_expression(node.operator, right)

    if isinstance(node, ast.InfixExpression):
        left = evaluate(node.left, env)
        if _is_error(left):
            return left
        right = evaluate(node.right, env)
        if _is_error(right):
            return right
        return _eval_infix_expression(node.operator, left, right)

    if isinstance(node, ast.IfExpression):
        return _eval_if_expression(node, env)

    # ── Identificadores ───────────────────────────────────────────────────────
    if isinstance(node, ast.Identifier):
        return _eval_identifier(node, env)

    # ── Funciones ─────────────────────────────────────────────────────────────
    if isinstance(node, ast.FunctionLiteral):
        return Function(
            parameters=node.parameters,
            body=node.body,
            env=env,
            name=node.name,
        )

    if isinstance(node, ast.CallExpression):
        return _eval_call_expression(node, env)

    # Nodo no reconocido
    return _new_error(f'nodo no soportado: {type(node).__name__}')


# ─────────────────────────────────────────────────────────────────────────────
# HANDLERS DE SENTENCIAS
# ─────────────────────────────────────────────────────────────────────────────

def _eval_program(program: ast.Program, env: Environment) -> Object:
    """
    Evalúa todas las sentencias del programa de arriba a abajo.

    Detiene la ejecución si encuentra un ReturnValue (return de alto nivel)
    o un Error. Retorna el resultado de la última sentencia evaluada.
    """
    result: Object = NULL

    for statement in program.statements:
        result = evaluate(statement, env)

        # Propagar return (desenvolver el valor real)
        if isinstance(result, ReturnValue):
            return result.value

        # Propagar errores inmediatamente
        if isinstance(result, Error):
            return result

    return result


def _eval_block_statement(block: ast.BlockStatement, env: Environment) -> Object:
    """
    Evalúa las sentencias de un bloque { ... }.

    A diferencia de _eval_program, NO desenvuelve ReturnValue:
    lo propaga hacia arriba para que el llamador de la función lo capture.
    También propaga BreakSignal y ContinueSignal para los bucles.
    """
    result: Object = NULL

    for statement in block.statements:
        result = evaluate(statement, env)

        if result is not None:
            rt = result.type
            # Detener el bloque ante señales de control o errores
            if rt in (
                ObjectType.RETURN,
                ObjectType.ERROR,
                ObjectType.BREAK,
                ObjectType.CONTINUE,
            ):
                return result

    return result


def _eval_let_statement(node: ast.LetStatement, env: Environment) -> Object:
    """
    Evalúa `let <nombre> = <expresión>;`

    Evalúa la expresión del lado derecho y la asigna en el entorno actual.
    Retorna NULL (la declaración no produce un valor visible).
    """
    value = evaluate(node.value, env)
    if _is_error(value):
        return value

    env.set(node.name.value, value)
    return NULL


def _eval_return_statement(node: ast.ReturnStatement, env: Environment) -> Object:
    """
    Evalúa `return <expresión>;`

    Envuelve el valor evaluado en un ReturnValue para que pueda propagarse
    hacia arriba del call stack hasta salir de la función.
    """
    value = evaluate(node.return_value, env)
    if _is_error(value):
        return value
    return ReturnValue(value)


def _eval_print_statement(node: ast.PrintStatement, env: Environment) -> Object:
    """
    Evalúa `print(<expresión>);`

    Imprime el resultado directamente en la salida estándar.
    Retorna NULL (la sentencia no produce un valor).
    """
    value = evaluate(node.value, env)
    if _is_error(value):
        return value
    print(value.inspect())
    return NULL


def _eval_while_statement(node: ast.WhileStatement, env: Environment) -> Object:
    """
    Evalúa `while (<condición>) { <cuerpo> }`

    En cada iteración:
      1. Evalúa la condición.
      2. Si es truthy, ejecuta el cuerpo.
      3. Si el cuerpo retorna break → salir del bucle.
         Si retorna continue → saltar al inicio (siguiente iteración).
         Si retorna return / error → propagar hacia arriba.
    """
    result: Object = NULL

    while True:
        condition = evaluate(node.condition, env)
        if _is_error(condition):
            return condition

        if not _is_truthy(condition):
            break

        result = evaluate(node.body, env)

        if isinstance(result, BreakSignal):
            return NULL
        if isinstance(result, ContinueSignal):
            continue
        if isinstance(result, (ReturnValue, Error)):
            return result

    return result if not isinstance(result, (BreakSignal, ContinueSignal)) else NULL


def _eval_for_statement(node: ast.ForStatement, env: Environment) -> Object:
    """
    Evalúa `for (<init>; <condición>; <update>) { <cuerpo> }`

    1. Evalúa init una sola vez en el entorno actual.
    2. En cada iteración: evalúa condición → ejecuta cuerpo → evalúa update.
    3. Respeta break / continue / return / error.

    NOTA: Se usa el mismo entorno `env` para init, condición, update y cuerpo,
    de forma que las variables declaradas con `let` fuera del for sean
    accesibles y modificables dentro del bucle.
    """
    # ── Inicialización ────────────────────────────────────────────────────────
    if node.init is not None:
        init_result = evaluate(node.init, env)
        if _is_error(init_result):
            return init_result

    result: Object = NULL

    # ── Ciclo ─────────────────────────────────────────────────────────────────
    while True:
        # Evaluar condición (si existe)
        if node.condition is not None:
            condition = evaluate(node.condition, env)
            if _is_error(condition):
                return condition
            if not _is_truthy(condition):
                break

        # Ejecutar cuerpo
        result = evaluate(node.body, env)

        if isinstance(result, BreakSignal):
            return NULL
        if isinstance(result, ContinueSignal):
            # Aún ejecutar el update antes de re-evaluar la condición
            pass
        elif isinstance(result, (ReturnValue, Error)):
            return result

        # Evaluar update (si existe)
        if node.update is not None:
            update_result = evaluate(node.update, env)
            if _is_error(update_result):
                return update_result

    return NULL


# ─────────────────────────────────────────────────────────────────────────────
# HANDLERS DE EXPRESIONES
# ─────────────────────────────────────────────────────────────────────────────

def _eval_identifier(node: ast.Identifier, env: Environment) -> Object:
    """
    Busca el valor de una variable en el entorno.

    Si no existe, retorna un Error de variable no definida.
    """
    value = env.get(node.value)
    if value is None:
        return _new_error(f"variable no definida: '{node.value}'")
    return value


def _eval_if_expression(node: ast.IfExpression, env: Environment) -> Object:
    """
    Evalúa `if (cond) { } elseif (c) { } else { }`

    1. Evalúa la condición del if principal.
    2. Si es truthy, ejecuta el bloque consequence.
    3. Si no, prueba cada rama elseif en orden.
    4. Si ninguna condición es verdadera, ejecuta el else (si existe).
    5. Si no hay else, retorna NULL.
    """
    condition = evaluate(node.condition, env)
    if _is_error(condition):
        return condition

    if _is_truthy(condition):
        return evaluate(node.consequence, env)

    # Probar ramas elseif
    for alt_condition, alt_block in node.alternatives:
        alt_cond_val = evaluate(alt_condition, env)
        if _is_error(alt_cond_val):
            return alt_cond_val
        if _is_truthy(alt_cond_val):
            return evaluate(alt_block, env)

    # Bloque else
    if node.else_block is not None:
        return evaluate(node.else_block, env)

    return NULL


def _eval_call_expression(node: ast.CallExpression, env: Environment) -> Object:
    """
    Evalúa una llamada a función: `función(arg1, arg2, ...)`

    1. Evalúa la expresión que produce la función.
    2. Evalúa cada argumento de izquierda a derecha.
    3. Crea un entorno hijo con los parámetros enlazados a los argumentos.
    4. Ejecuta el cuerpo de la función en ese nuevo entorno.
    5. Desenvuelve el ReturnValue si existe.
    """
    function = evaluate(node.function, env)
    if _is_error(function):
        return function

    if not isinstance(function, Function):
        return _new_error(
            f"'{node.function}' no es una función, es {function.type.name}"
        )

    # Evaluar argumentos
    args = _eval_expressions(node.arguments, env)
    if len(args) == 1 and _is_error(args[0]):
        return args[0]

    # Verificar número de argumentos
    if len(args) != len(function.parameters):
        return _new_error(
            f"número de argumentos incorrecto: esperados {len(function.parameters)}, "
            f"recibidos {len(args)}"
        )

    # Crear entorno de ejecución de la función
    func_env = _extend_function_env(function, args)

    # Ejecutar el cuerpo
    evaluated = evaluate(function.body, func_env)

    # Desenvolver el valor de retorno
    return _unwrap_return_value(evaluated)


def _eval_expressions(
    expressions: List[ast.Expression],
    env: Environment
) -> List[Object]:
    """
    Evalúa una lista de expresiones (argumentos de una llamada a función).

    Si alguna expresión produce un error, retorna inmediatamente una lista
    con solo ese error.
    """
    result: List[Object] = []

    for expression in expressions:
        evaluated = evaluate(expression, env)
        if _is_error(evaluated):
            return [evaluated]
        result.append(evaluated)

    return result


def _extend_function_env(function: Function, args: List[Object]) -> Environment:
    """
    Crea un nuevo entorno hijo del entorno léxico de la función,
    con cada parámetro formal enlazado al argumento correspondiente.
    """
    env = new_enclosed_environment(function.env)

    for param, arg in zip(function.parameters, args):
        env.set(param.value, arg)

    return env


def _unwrap_return_value(obj: Object) -> Object:
    """
    Si el objeto es un ReturnValue, desenvuelve el valor real.

    Esto evita que un `return` de una función interna burbujee más allá
    de la función que lo emitió.
    """
    if isinstance(obj, ReturnValue):
        return obj.value
    return obj


# ─────────────────────────────────────────────────────────────────────────────
# OPERADORES PREFIJOS
# ─────────────────────────────────────────────────────────────────────────────

def _eval_prefix_expression(operator: str, right: Object) -> Object:
    """
    Despacha la evaluación de un operador prefijo.

    Operadores soportados:
      !  → negación lógica (NOT)
      -  → negación aritmética (cambia signo)
    """
    if operator == '!':
        return _eval_bang_operator(right)
    if operator == '-':
        return _eval_minus_prefix_operator(right)
    return _new_error(f"operador prefijo desconocido: '{operator}'")


def _eval_bang_operator(right: Object) -> Object:
    """
    Evalúa el operador de negación lógica `!`.

    Reglas de truthiness:
      !true       → false
      !false      → true
      !null       → true   (null es falsy)
      !0 / !0.0   → true   (cero numérico es falsy)
      !""         → true   (string vacío es falsy)
      !<cualquier otro valor> → false  (todo lo demás es truthy)
    """
    # Usar _is_truthy centraliza la lógica de falsiness
    return FALSE if _is_truthy(right) else TRUE


def _eval_minus_prefix_operator(right: Object) -> Object:
    """
    Evalúa el operador de negación aritmética `-`.

    Soporta:  -Integer  y  -Float
    """
    if isinstance(right, Integer):
        return Integer(-right.value)
    if isinstance(right, Float):
        return Float(-right.value)
    return _new_error(
        f"operador '-' no soportado para {right.type.name}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# OPERADORES INFIJOS
# ─────────────────────────────────────────────────────────────────────────────

def _eval_infix_expression(operator: str, left: Object, right: Object) -> Object:
    """
    Despacha la evaluación de un operador infijo según los tipos de operandos.

    Prioridad de despacho:
      1. Ambos Integer → aritmética/comparación entera
      2. Ambos Float, o mezcla Integer+Float → aritmética flotante
      3. Operadores lógicos (and, or) → evaluados con truthiness
      4. Operadores de igualdad (==, !=) → comparan cualquier tipo
      5. Ambos String → operaciones de string
      6. Tipo no soportado → error
    """

    # ── Ambos enteros ─────────────────────────────────────────────────────────
    if isinstance(left, Integer) and isinstance(right, Integer):
        return _eval_integer_infix_expression(operator, left, right)

    # ── Aritmética de punto flotante (incluye mezcla int/float) ───────────────
    if isinstance(left, (Integer, Float)) and isinstance(right, (Integer, Float)):
        left_val = float(left.value)
        right_val = float(right.value)
        return _eval_float_infix_expression(operator, left_val, right_val)

    # ── Operadores lógicos (and, or) ──────────────────────────────────────────
    if operator == 'and':
        return _native_bool_to_boolean_object(_is_truthy(left) and _is_truthy(right))
    if operator == 'or':
        return _native_bool_to_boolean_object(_is_truthy(left) or _is_truthy(right))

    # ── Operadores de igualdad: cualquier tipo ─────────────────────────────────
    if operator == '==':
        return _native_bool_to_boolean_object(_objects_are_equal(left, right))
    if operator == '!=':
        return _native_bool_to_boolean_object(not _objects_are_equal(left, right))

    # ── Strings ───────────────────────────────────────────────────────────────
    if isinstance(left, String) and isinstance(right, String):
        return _eval_string_infix_expression(operator, left, right)

    # ── Tipos incompatibles ────────────────────────────────────────────────────
    if left.type != right.type:
        return _new_error(
            f"tipos incompatibles: {left.type.name} {operator} {right.type.name}"
        )

    return _new_error(
        f"operador '{operator}' no soportado entre {left.type.name} y {right.type.name}"
    )


def _eval_integer_infix_expression(
    operator: str, left: Integer, right: Integer
) -> Object:
    """
    Evalúa operaciones entre dos enteros.

    Operaciones aritméticas: + - * / % ^
    Operaciones de comparación: == != < <= > >=
    """
    lv = left.value
    rv = right.value

    # ── Aritméticas ───────────────────────────────────────────────────────────
    if operator == '+':
        return Integer(lv + rv)
    if operator == '-':
        return Integer(lv - rv)
    if operator == '*':
        return Integer(lv * rv)
    if operator == '/':
        if rv == 0:
            return _new_error('división por cero')
        # División entera si el resultado es exacto, flotante si no
        result = lv / rv
        return Integer(int(result)) if result == int(result) else Float(result)
    if operator == '%':
        if rv == 0:
            return _new_error('módulo por cero')
        return Integer(lv % rv)
    if operator == '^':
        if rv < 0:
            # Potencia negativa → resultado flotante
            return Float(lv ** rv)
        return Integer(lv ** rv)

    # ── Comparación ───────────────────────────────────────────────────────────
    if operator == '==':
        return _native_bool_to_boolean_object(lv == rv)
    if operator == '!=':
        return _native_bool_to_boolean_object(lv != rv)
    if operator == '<':
        return _native_bool_to_boolean_object(lv < rv)
    if operator == '<=':
        return _native_bool_to_boolean_object(lv <= rv)
    if operator == '>':
        return _native_bool_to_boolean_object(lv > rv)
    if operator == '>=':
        return _native_bool_to_boolean_object(lv >= rv)

    return _new_error(f"operador '{operator}' no soportado entre enteros")


def _eval_float_infix_expression(
    operator: str, lv: float, rv: float
) -> Object:
    """
    Evalúa operaciones aritméticas y de comparación entre flotantes
    (también aplica cuando se mezcla int con float).
    """

    # ── Aritméticas ───────────────────────────────────────────────────────────
    if operator == '+':
        return Float(lv + rv)
    if operator == '-':
        return Float(lv - rv)
    if operator == '*':
        return Float(lv * rv)
    if operator == '/':
        if rv == 0.0:
            return _new_error('división por cero')
        return Float(lv / rv)
    if operator == '%':
        if rv == 0.0:
            return _new_error('módulo por cero')
        return Float(lv % rv)
    if operator == '^':
        return Float(lv ** rv)

    # ── Comparación ───────────────────────────────────────────────────────────
    if operator == '==':
        return _native_bool_to_boolean_object(lv == rv)
    if operator == '!=':
        return _native_bool_to_boolean_object(lv != rv)
    if operator == '<':
        return _native_bool_to_boolean_object(lv < rv)
    if operator == '<=':
        return _native_bool_to_boolean_object(lv <= rv)
    if operator == '>':
        return _native_bool_to_boolean_object(lv > rv)
    if operator == '>=':
        return _native_bool_to_boolean_object(lv >= rv)

    return _new_error(f"operador '{operator}' no soportado entre flotantes")


def _eval_string_infix_expression(
    operator: str, left: String, right: String
) -> Object:
    """
    Evalúa operaciones entre strings.

    Operaciones soportadas:
      + → concatenación
      == / != → comparación de igualdad
    """
    if operator == '+':
        return String(left.value + right.value)
    if operator == '==':
        return _native_bool_to_boolean_object(left.value == right.value)
    if operator == '!=':
        return _native_bool_to_boolean_object(left.value != right.value)

    return _new_error(
        f"operador '{operator}' no soportado entre strings"
    )


# ─────────────────────────────────────────────────────────────────────────────
# UTILIDADES INTERNAS
# ─────────────────────────────────────────────────────────────────────────────

def _is_truthy(obj: Object) -> bool:
    """
    Determina si un objeto es 'truthy' (verdadero en un contexto booleano).

    Reglas:
      null  → False
      false → False
      true  → True
      0     → False  (entero cero)
      0.0   → False  (flotante cero)
      ""    → False  (string vacío)
      <cualquier otro valor> → True
    """
    if obj is NULL:
        return False
    if obj is FALSE:
        return False
    if obj is TRUE:
        return True
    if isinstance(obj, Integer):
        return obj.value != 0
    if isinstance(obj, Float):
        return obj.value != 0.0
    if isinstance(obj, String):
        return len(obj.value) > 0
    return True


def _objects_are_equal(left: Object, right: Object) -> bool:
    """
    Compara dos objetos por valor (igualdad semántica).

    - Boolean: compara identidad (usan singletons TRUE/FALSE)
    - Integer/Float: compara valor numérico
    - String: compara texto
    - Null: son siempre iguales entre sí
    - Tipos distintos: siempre False
    """
    if left.type != right.type:
        # Excepción: int y float pueden compararse numéricamente
        if isinstance(left, (Integer, Float)) and isinstance(right, (Integer, Float)):
            return left.value == right.value
        return False

    if isinstance(left, Boolean):
        return left is right  # Singletons → identidad es suficiente

    if isinstance(left, (Integer, Float)):
        return left.value == right.value

    if isinstance(left, String):
        return left.value == right.value

    if isinstance(left, Null):
        return True  # null == null

    return left is right


def _native_bool_to_boolean_object(value: bool) -> Boolean:
    """
    Convierte un bool de Python al singleton Boolean del lenguaje.
    """
    return TRUE if value else FALSE


def _is_error(obj: Object) -> bool:
    """Retorna True si el objeto es un Error de ejecución."""
    return isinstance(obj, Error)


def _new_error(message: str) -> Error:
    """Crea un nuevo objeto Error con el mensaje dado."""
    return Error(message)
