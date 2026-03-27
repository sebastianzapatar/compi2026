# =============================================================================
# ast.py — Árbol Sintáctico Abstracto (AST)
#
# El AST es la representación intermedia del programa.
# El Parser toma la secuencia de tokens producida por el Lexer y construye
# este árbol. Luego el Evaluador recorre el árbol para ejecutar el programa.
#
# Jerarquía de clases:
#   Node
#   ├── Statement (sentencias: declaraciones, control de flujo)
#   │   ├── Program              ← nodo raíz de todo el programa
#   │   ├── LetStatement         ← let x = expr;
#   │   ├── ReturnStatement      ← return expr;
#   │   ├── ExpressionStatement  ← expr;  (una expresión usada como sentencia)
#   │   ├── BlockStatement       ← { stmt; stmt; ... }
#   │   ├── WhileStatement       ← while (cond) { ... }
#   │   └── ForStatement         ← for (init; cond; update) { ... }
#   │
#   └── Expression (expresiones: producen un valor)
#       ├── Identifier           ← nombre de variable
#       ├── IntegerLiteral       ← 42
#       ├── FloatLiteral         ← 3.14
#       ├── StringLiteral        ← "hola"
#       ├── BooleanLiteral       ← true / false
#       ├── PrefixExpression     ← !expr  o  -expr
#       ├── InfixExpression      ← expr OP expr
#       ├── IfExpression         ← if (cond) { } elseif (c) { } else { }
#       ├── FunctionLiteral      ← function(params) { body }
#       └── CallExpression       ← función(args)
# =============================================================================

from abc import ABC, abstractmethod  # Para definir clases abstractas
from typing import List, Optional    # Tipos genéricos de Python


# ─────────────────────────────────────────────────────────────────────────────
# CLASES BASE
# ─────────────────────────────────────────────────────────────────────────────

class Node(ABC):
    """
    Clase base de todos los nodos del AST.

    Cada nodo debe implementar token_literal() (retorna el literal del token
    que lo originó, útil para debug) y __str__ (representación legible).
    """

    @abstractmethod
    def token_literal(self) -> str:
        """Retorna el literal del token principal de este nodo."""
        pass

    @abstractmethod
    def __str__(self) -> str:
        """Representación en string del nodo (para debug e impresión)."""
        pass


class Statement(Node):
    """
    Nodo base para SENTENCIAS.

    Las sentencias NO producen un valor por sí mismas; ejecutan una acción.
    Ejemplos: let x = 5;  return x;  while (...) { ... }
    """
    pass


class Expression(Node):
    """
    Nodo base para EXPRESIONES.

    Las expresiones SÍ producen un valor.
    Ejemplos: 5 + 3,  miFuncion(x),  x == y
    """
    pass


# ─────────────────────────────────────────────────────────────────────────────
# NODO RAÍZ
# ─────────────────────────────────────────────────────────────────────────────

class Program(Node):
    """
    Nodo raíz del AST. Representa el programa completo.

    Contiene una lista de sentencias de alto nivel.
    El evaluador recorre esta lista de sentencias en orden.
    """

    def __init__(self) -> None:
        # Lista de todas las sentencias del programa
        self.statements: List[Statement] = []

    def token_literal(self) -> str:
        """Retorna el literal del primer token del programa."""
        if self.statements:
            return self.statements[0].token_literal()
        return ''

    def __str__(self) -> str:
        """Concatena la representación de todas las sentencias."""
        return '\n'.join(str(s) for s in self.statements)


# ─────────────────────────────────────────────────────────────────────────────
# SENTENCIAS (Statements)
# ─────────────────────────────────────────────────────────────────────────────

class LetStatement(Statement):
    """
    Nodo para declaración de variable: let <nombre> = <valor>;

    Ejemplo de código fuente: let resultado = 10 + 5;
    ┌─────────────────────┐
    │ LetStatement        │
    │   name: Identifier  │← 'resultado'
    │   value: Expression │← InfixExpression(10 + 5)
    └─────────────────────┘
    """

    def __init__(self, token, name: 'Identifier', value: Optional[Expression]) -> None:
        self.token = token           # El token LET ('let')
        self.name = name             # El identificador (nombre de la variable)
        self.value = value           # La expresión asignada al identificador

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        value_str = str(self.value) if self.value else ''
        return f'let {self.name} = {value_str};'


class ReturnStatement(Statement):
    """
    Nodo para sentencia de retorno: return <valor>;

    Ejemplo: return x + 1;
    """

    def __init__(self, token, return_value: Optional[Expression]) -> None:
        self.token = token                   # El token RETURN ('return')
        self.return_value = return_value     # La expresión a retornar

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        value_str = str(self.return_value) if self.return_value else ''
        return f'return {value_str};'


class ExpressionStatement(Statement):
    """
    Nodo para una expresión usada como sentencia completa.

    Cuando una expresión aparece sola en una línea (e.g. una llamada
    a función que no se asigna a nadie), se envuelve en este nodo.

    Ejemplo:  miFuncion(x);
    """

    def __init__(self, token, expression: Optional[Expression] = None) -> None:
        self.token = token               # El primer token de la expresión
        self.expression = expression     # La expresión en sí

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return str(self.expression) if self.expression else ''


class BlockStatement(Statement):
    """
    Nodo para un bloque de sentencias delimitado por llaves: { stmt; stmt; }

    Los bloques se usan en if, while, for y funciones.
    """

    def __init__(self, token) -> None:
        self.token = token                       # El token '{' que abre el bloque
        self.statements: List[Statement] = []    # Sentencias dentro del bloque

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        stmts = '\n'.join(f'  {s}' for s in self.statements)
        return f'{{\n{stmts}\n}}'


class WhileStatement(Statement):
    """
    Nodo para bucle while: while (<condición>) { <cuerpo> }

    Ejemplo:
        while (x < 10) {
            let x = x + 1;
        }
    """

    def __init__(self, token, condition: Expression, body: BlockStatement) -> None:
        self.token = token           # El token WHILE ('while')
        self.condition = condition   # Expresión que se evalúa en cada iteración
        self.body = body             # Bloque de sentencias del cuerpo

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f'while ({self.condition}) {self.body}'


class ForStatement(Statement):
    """
    Nodo para bucle for: for (<init>; <condición>; <actualización>) { <cuerpo> }

    Ejemplo:
        for (let i = 0; i < 10; let i = i + 1) {
            print(i);
        }

    Componentes:
      init       → sentencia de inicialización (let i = 0)
      condition  → condición de continuación   (i < 10)
      update     → sentencia de actualización  (let i = i + 1)
      body       → bloque de código a ejecutar
    """

    def __init__(
        self,
        token,
        init: Optional[Statement],
        condition: Optional[Expression],
        update: Optional[Statement],
        body: BlockStatement
    ) -> None:
        self.token = token           # El token FOR ('for')
        self.init = init             # Inicialización (puede ser None)
        self.condition = condition   # Condición (puede ser None → bucle infinito)
        self.update = update         # Actualización (puede ser None)
        self.body = body             # Cuerpo del bucle

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return (
            f'for ({self.init}; {self.condition}; {self.update}) '
            f'{self.body}'
        )



class BreakStatement(Statement):
    """
    Nodo para la sentencia break.

    Interrumpe inmediatamente el bucle más cercano (while o for).
    Ejemplo: break;
    """

    def __init__(self, token) -> None:
        self.token = token   # El token BREAK ('break')

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return 'break;'


class ContinueStatement(Statement):
    """
    Nodo para la sentencia continue.

    Salta el resto del cuerpo del bucle y pasa a la siguiente iteración.
    En el for, también evalúa el update antes de re-evaluar la condición.
    Ejemplo: continue;
    """

    def __init__(self, token) -> None:
        self.token = token   # El token CONTINUE ('continue')

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return 'continue;'


# ─────────────────────────────────────────────────────────────────────────────
# EXPRESIONES (Expressions)
# ─────────────────────────────────────────────────────────────────────────────


class Identifier(Expression):
    """
    Nodo para un nombre de variable o función.

    Ejemplo: x,  resultado,  miFuncion
    """

    def __init__(self, token, value: str) -> None:
        self.token = token   # El token IDENTIFIER
        self.value = value   # El nombre como string

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return self.value


class IntegerLiteral(Expression):
    """
    Nodo para un número entero.

    Ejemplo: 42,  0,  -7 (el signo negativo se maneja como PrefixExpression)
    """

    def __init__(self, token, value: int) -> None:
        self.token = token   # El token INTEGER
        self.value = value   # El valor entero ya convertido (int)

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return str(self.value)


class FloatLiteral(Expression):
    """
    Nodo para un número decimal (flotante).

    Ejemplo: 3.14,  2.0,  0.5
    """

    def __init__(self, token, value: float) -> None:
        self.token = token   # El token FLOAT
        self.value = value   # El valor flotante ya convertido (float)

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return str(self.value)


class StringLiteral(Expression):
    """
    Nodo para una cadena de texto.

    Ejemplo: "hola mundo",  "resultado: "
    """

    def __init__(self, token, value: str) -> None:
        self.token = token   # El token STRING
        self.value = value   # El contenido del string (sin comillas)

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f'"{self.value}"'


class BooleanLiteral(Expression):
    """
    Nodo para los literales booleanos: true o false.
    """

    def __init__(self, token, value: bool) -> None:
        self.token = token   # El token TRUE o FALSE
        self.value = value   # True o False (Python bool)

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return 'true' if self.value else 'false'


class PrefixExpression(Expression):
    """
    Nodo para expresiones con operador PREFIJO: <operador><expresión>

    Ejemplos:
      !verdadero   →  PrefixExpression(operator='!', right=BooleanLiteral(true))
      -5           →  PrefixExpression(operator='-', right=IntegerLiteral(5))
    """

    def __init__(self, token, operator: str, right: Optional[Expression] = None) -> None:
        self.token = token           # El token del operador ('!' o '-')
        self.operator = operator     # El símbolo del operador como string
        self.right = right           # La expresión a la derecha del operador

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f'({self.operator}{self.right})'


class InfixExpression(Expression):
    """
    Nodo para expresiones con operador INFIJO: <izquierda> <operador> <derecha>

    Ejemplos:
      5 + 3     →  InfixExpression(left=5, operator='+', right=3)
      x == y    →  InfixExpression(left=x, operator='==', right=y)
      a and b   →  InfixExpression(left=a, operator='and', right=b)
    """

    def __init__(
        self,
        token,
        left: Expression,
        operator: str,
        right: Optional[Expression] = None
    ) -> None:
        self.token = token       # El token del operador
        self.left = left         # Expresión del lado izquierdo
        self.operator = operator # El símbolo del operador como string
        self.right = right       # Expresión del lado derecho

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f'({self.left} {self.operator} {self.right})'


class IfExpression(Expression):
    """
    Nodo para condicionales: if (...) { } elseif (...) { } else { }

    Soporta múltiples ramas elseif como lista de pares (condición, bloque).

    Ejemplo:
        if (x > 0) {
            print("positivo");
        } elseif (x == 0) {
            print("cero");
        } else {
            print("negativo");
        }
    """

    def __init__(
        self,
        token,
        condition: Expression,
        consequence: BlockStatement,
        alternatives: Optional[List[tuple]] = None,  # lista de (condicion, bloque)
        else_block: Optional[BlockStatement] = None
    ) -> None:
        self.token = token                   # El token IF ('if')
        self.condition = condition           # Condición del if principal
        self.consequence = consequence       # Bloque si la condición es verdadera
        self.alternatives = alternatives or []  # Lista de ramas elseif
        self.else_block = else_block         # Bloque else final (opcional)

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        result = f'if ({self.condition}) {self.consequence}'
        for cond, block in self.alternatives:
            result += f' elseif ({cond}) {block}'
        if self.else_block:
            result += f' else {self.else_block}'
        return result


class FunctionLiteral(Expression):
    """
    Nodo para la DEFINICIÓN de una función: function(<parámetros>) { <cuerpo> }

    Ejemplo:
        function(x, y) {
            return x + y;
        }

    Las funciones en este lenguaje son valores de primera clase:
    se pueden asignar a variables, pasar como argumentos, etc.
    La recursión funciona porque el entorno (Environment) guarda
    la referencia al propio objeto función.
    """

    def __init__(
        self,
        token,
        parameters: List[Identifier],
        body: BlockStatement,
        name: str = ''
    ) -> None:
        self.token = token             # El token FUNCTION ('function')
        self.parameters = parameters   # Lista de Identifier (parámetros formales)
        self.body = body               # Bloque de sentencias del cuerpo
        self.name = name               # Nombre (si fue asignada con let)

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        params = ', '.join(str(p) for p in self.parameters)
        name_str = f' {self.name}' if self.name else ''
        return f'function{name_str}({params}) {self.body}'


class CallExpression(Expression):
    """
    Nodo para la LLAMADA a una función: <función>(<argumentos>)

    Ejemplo:
        factorial(5)
        suma(x, y + 1)

    La función puede ser un identificador (nombre) o una expresión
    que produce una función (e.g. una lambda inmediata).
    """

    def __init__(
        self,
        token,
        function: Expression,
        arguments: List[Expression]
    ) -> None:
        self.token = token           # El token '(' de la llamada
        self.function = function     # La función (Identifier o FunctionLiteral)
        self.arguments = arguments   # Lista de expresiones (argumentos reales)

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        args = ', '.join(str(a) for a in self.arguments)
        return f'{self.function}({args})'


class PrintStatement(Statement):
    """
    Nodo para la sentencia de impresión: print(<expresión>);

    Ejemplo: print(x + 1);
    """

    def __init__(self, token, value: Expression) -> None:
        self.token = token   # El token PRINT ('print')
        self.value = value   # La expresión a imprimir

    def token_literal(self) -> str:
        return self.token.literal

    def __str__(self) -> str:
        return f'print({self.value});'
