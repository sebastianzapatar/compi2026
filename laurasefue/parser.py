# =============================================================================
# parser.py — Analizador Sintáctico (Parser)
#
# El Parser es la segunda etapa del intérprete. Toma la secuencia de tokens
# producida por el Lexer y construye un Árbol Sintáctico Abstracto (AST).
#
# Utiliza el algoritmo de Pratt Parsing (Top-Down Operator Precedence),
# que permite manejar la precedencia de operadores de forma elegante
# asociando funciones de parseo (prefix y infix) a cada tipo de token.
#
# Flujo general:
#   Código fuente → [Lexer] → Tokens → [Parser] → AST → [Evaluador]
#
# Ejemplo:
#   Entrada: "let x = 5 + 3;"
#   Resultado:
#     Program
#     └── LetStatement
#         ├── name: Identifier("x")
#         └── value: InfixExpression
#             ├── left: IntegerLiteral(5)
#             ├── operator: "+"
#             └── right: IntegerLiteral(3)
# =============================================================================

from enum import IntEnum
from typing import (
    Callable,
    Dict,
    List,
    Optional
)
from laurasefue.tokens import Token, TokenType
from laurasefue.lexer import Lexer
from laurasefue import ast


# ─────────────────────────────────────────────────────────────────────────────
# TABLA DE PRECEDENCIAS
# ─────────────────────────────────────────────────────────────────────────────

class Precedences(IntEnum):
    """
    Niveles de precedencia de operadores, de menor a mayor.

    La precedencia determina el orden de evaluación cuando hay operadores
    mezclados sin paréntesis. Por ejemplo, en "2 + 3 * 4":
      - PRODUCT > SUM, así que primero se evalúa 3 * 4 = 12, luego 2 + 12 = 14.

    Orden (de menor a mayor prioridad):
      LOWEST      → Base mínima, usada como punto de partida
      OR          → Operador lógico 'or'
      AND         → Operador lógico 'and'
      EQUALS      → == y !=
      LESSGREATER → <, <=, >, >=
      SUM         → + y -
      PRODUCT     → *, / y %
      PREFIX      → Operadores unarios: -X, !X
      POWER       → Potencia ^
      CALL        → Llamada a función: f(x)
    """
    LOWEST = 1
    OR = 2
    AND = 3
    EQUALS = 4       # == , !=
    LESSGREATER = 5  # > , < , >= , <=
    SUM = 6          # + , -
    PRODUCT = 7      # * , / , %
    PREFIX = 8       # -X , !X
    POWER = 9        # ^
    CALL = 10        # myFunction(X)


# Mapeo de tipo de token → nivel de precedencia
# El parser consulta esta tabla para decidir qué operador "gana" al competir
PRECEDENCES: Dict[TokenType, Precedences] = {
    TokenType.OR:       Precedences.OR,
    TokenType.AND:      Precedences.AND,
    TokenType.EQ:       Precedences.EQUALS,
    TokenType.DIF:      Precedences.EQUALS,
    TokenType.LT:       Precedences.LESSGREATER,
    TokenType.LTE:      Precedences.LESSGREATER,
    TokenType.GT:       Precedences.LESSGREATER,
    TokenType.GTE:      Precedences.LESSGREATER,
    TokenType.PLUS:     Precedences.SUM,
    TokenType.MINUS:    Precedences.SUM,
    TokenType.MULTIPLY: Precedences.PRODUCT,
    TokenType.DIVISION: Precedences.PRODUCT,
    TokenType.MOD:      Precedences.PRODUCT,
    TokenType.POW:      Precedences.POWER,
    TokenType.LPAREN:   Precedences.CALL,
}


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE FUNCIONES DE PARSEO (Pratt Parsing)
# ─────────────────────────────────────────────────────────────────────────────

# Función prefix: se invoca cuando el token aparece al INICIO de una expresión
# Ejemplo: -5, !true, un identificador, un literal
PrefixParseFn = Callable[[], ast.Expression]

# Función infix: se invoca cuando el token aparece EN MEDIO de dos expresiones
# Recibe la expresión izquierda ya parseada como argumento
# Ejemplo: 5 + 3, función(args)
InfixParseFn = Callable[[ast.Expression], ast.Expression]


# ─────────────────────────────────────────────────────────────────────────────
# CLASE PRINCIPAL DEL PARSER
# ─────────────────────────────────────────────────────────────────────────────

class Parser:
    """
    Analizador sintáctico basado en Pratt Parsing.

    Convierte una secuencia de tokens (del Lexer) en un AST (Árbol Sintáctico
    Abstracto). El AST puede luego ser recorrido por un evaluador para
    ejecutar el programa.

    Atributos internos:
      _lexer          → Instancia del lexer que produce tokens
      _errors         → Lista de errores encontrados durante el parseo
      _current_token  → El token que se está procesando ahora
      _peek_token     → El siguiente token (look-ahead de 1)
      _prefix_parse_fns → Funciones de parseo para tokens en posición prefix
      _infix_parse_fns  → Funciones de parseo para tokens en posición infix
    """

    def __init__(self, lexer: Lexer) -> None:
        """
        Inicializa el parser con un lexer.

        Registra todas las funciones de parseo (prefix e infix) y avanza
        dos veces para llenar _current_token y _peek_token.
        """
        self._lexer = lexer

        # Lista para acumular errores de parseo (no lanza excepciones)
        self._errors: List[str] = []

        # Doble buffer de tokens: actual y siguiente (look-ahead)
        self._current_token: Optional[Token] = None
        self._peek_token: Optional[Token] = None

        # ─── Registro de funciones PREFIX ────────────────────────────────
        # Cada entrada asocia un tipo de token con la función que sabe
        # cómo parsear una expresión que EMPIEZA con ese token
        self._prefix_parse_fns: Dict[TokenType, PrefixParseFn] = {
            TokenType.IDENTIFIER: self._parse_identifier,
            TokenType.INTEGER:    self._parse_integer_literal,
            TokenType.FLOAT:      self._parse_float_literal,
            TokenType.STRING:     self._parse_string_literal,
            TokenType.TRUE:       self._parse_boolean_literal,
            TokenType.FALSE:      self._parse_boolean_literal,
            TokenType.MINUS:      self._parse_prefix_expression,
            TokenType.NEGATION:   self._parse_prefix_expression,
            TokenType.LPAREN:     self._parse_grouped_expression,
            TokenType.IF:         self._parse_if_expression,
            TokenType.FUNCTION:   self._parse_function_literal,
        }

        # ─── Registro de funciones INFIX ─────────────────────────────────
        # Cada entrada asocia un tipo de token con la función que sabe
        # cómo parsear una expresión donde ese token aparece ENTRE dos operandos
        self._infix_parse_fns: Dict[TokenType, InfixParseFn] = {
            TokenType.PLUS:     self._parse_infix_expression,
            TokenType.MINUS:    self._parse_infix_expression,
            TokenType.MULTIPLY: self._parse_infix_expression,
            TokenType.DIVISION: self._parse_infix_expression,
            TokenType.MOD:      self._parse_infix_expression,
            TokenType.POW:      self._parse_infix_expression,
            TokenType.EQ:       self._parse_infix_expression,
            TokenType.DIF:      self._parse_infix_expression,
            TokenType.LT:       self._parse_infix_expression,
            TokenType.LTE:      self._parse_infix_expression,
            TokenType.GT:       self._parse_infix_expression,
            TokenType.GTE:      self._parse_infix_expression,
            TokenType.AND:      self._parse_infix_expression,
            TokenType.OR:       self._parse_infix_expression,
            TokenType.LPAREN:   self._parse_call_expression,
        }

        # Avanza dos veces para inicializar ambos buffers de tokens
        self._advance_tokens()
        self._advance_tokens()

    # ─────────────────────────────────────────────────────────────────────────
    # PROPIEDADES PÚBLICAS
    # ─────────────────────────────────────────────────────────────────────────

    @property
    def errors(self) -> List[str]:
        """Retorna la lista de errores de parseo encontrados."""
        return self._errors

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODO PRINCIPAL: PARSEAR PROGRAMA
    # ─────────────────────────────────────────────────────────────────────────

    def parse_program(self) -> ast.Program:
        """
        Parsea el programa completo y retorna el nodo raíz del AST.

        Itera sobre todos los tokens, parseando sentencia por sentencia,
        hasta encontrar el token EOF (fin de archivo).

        Retorna:
            ast.Program con la lista de sentencias del programa.
        """
        program = ast.Program()

        # Mientras no hayamos llegado al fin del archivo
        while self._current_token is not None and \
              self._current_token.token_type != TokenType.EOF:
            statement = self._parse_statement()
            if statement is not None:
                program.statements.append(statement)
            self._advance_tokens()

        return program

    # ─────────────────────────────────────────────────────────────────────────
    # PARSEO DE SENTENCIAS (Statements)
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_statement(self) -> Optional[ast.Statement]:
        """
        Determina qué tipo de sentencia parsear según el token actual.

        Despacha al método correspondiente:
          LET      → _parse_let_statement
          RETURN   → _parse_return_statement
          PRINT    → _parse_print_statement
          WHILE    → _parse_while_statement
          FOR      → _parse_for_statement
          BREAK    → _parse_break_statement
          CONTINUE → _parse_continue_statement
          otro     → _parse_expression_statement (expresión como sentencia)
        """
        assert self._current_token is not None

        match self._current_token.token_type:
            case TokenType.LET:
                return self._parse_let_statement()
            case TokenType.RETURN:
                return self._parse_return_statement()
            case TokenType.PRINT:
                return self._parse_print_statement()
            case TokenType.WHILE:
                return self._parse_while_statement()
            case TokenType.FOR:
                return self._parse_for_statement()
            case TokenType.BREAK:
                return self._parse_break_statement()
            case TokenType.CONTINUE:
                return self._parse_continue_statement()
            case _:
                return self._parse_expression_statement()

    def _parse_let_statement(self) -> Optional[ast.LetStatement]:
        """
        Parsea una sentencia LET: let <nombre> = <expresión>;

        Estructura esperada de tokens:
          LET  IDENTIFIER  ASSIGN  <expresión>  SEMICOLON

        Ejemplo:
          let resultado = 10 + 5;

        Retorna None si hay un error de sintaxis.
        """
        assert self._current_token is not None
        token = self._current_token  # Guarda el token LET

        # Espera un identificador después de 'let'
        if not self._expected_token(TokenType.IDENTIFIER):
            return None

        # Crea el nodo Identifier con el nombre de la variable
        assert self._current_token is not None
        name = ast.Identifier(
            token=self._current_token,
            value=self._current_token.literal
        )

        # Espera el signo '='
        if not self._expected_token(TokenType.ASSIGN):
            return None

        # Avanza al inicio de la expresión del valor
        self._advance_tokens()

        # Parsea la expresión del valor (e.g. 10 + 5)
        value = self._parse_expression(Precedences.LOWEST)

        # Si es una función, le asignamos el nombre de la variable
        # Esto permite la recursión: let factorial = function(n) { ... }
        if isinstance(value, ast.FunctionLiteral):
            value.name = name.value

        # Consume el punto y coma opcional al final
        if self._peek_token_is(TokenType.SEMICOLON):
            self._advance_tokens()

        return ast.LetStatement(token=token, name=name, value=value)

    def _parse_return_statement(self) -> Optional[ast.ReturnStatement]:
        """
        Parsea una sentencia RETURN: return <expresión>;

        Estructura esperada:
          RETURN  <expresión>  SEMICOLON

        Ejemplo:
          return x + 1;
        """
        assert self._current_token is not None
        token = self._current_token  # Guarda el token RETURN

        # Avanza más allá de 'return' hacia la expresión
        self._advance_tokens()

        # Parsea la expresión a retornar
        return_value = self._parse_expression(Precedences.LOWEST)

        # Consume el punto y coma opcional
        if self._peek_token_is(TokenType.SEMICOLON):
            self._advance_tokens()

        return ast.ReturnStatement(token=token, return_value=return_value)

    def _parse_print_statement(self) -> Optional[ast.PrintStatement]:
        """
        Parsea una sentencia PRINT: print(<expresión>);

        Estructura esperada:
          PRINT  LPAREN  <expresión>  RPAREN  SEMICOLON

        Ejemplo:
          print(x + 1);
        """
        assert self._current_token is not None
        token = self._current_token  # Guarda el token PRINT

        # Espera '(' después de 'print'
        if not self._expected_token(TokenType.LPAREN):
            return None

        # Avanza al inicio de la expresión
        self._advance_tokens()

        # Parsea la expresión a imprimir
        value = self._parse_expression(Precedences.LOWEST)

        # Espera ')' cerrando la llamada a print
        if not self._expected_token(TokenType.RPAREN):
            return None

        # Consume el punto y coma opcional
        if self._peek_token_is(TokenType.SEMICOLON):
            self._advance_tokens()

        assert value is not None
        return ast.PrintStatement(token=token, value=value)

    def _parse_while_statement(self) -> Optional[ast.WhileStatement]:
        """
        Parsea una sentencia WHILE: while (<condición>) { <cuerpo> }

        Estructura esperada:
          WHILE  LPAREN  <expresión>  RPAREN  LBRACE  <sentencias>  RBRACE

        Ejemplo:
          while (x < 10) {
              let x = x + 1;
          }
        """
        assert self._current_token is not None
        token = self._current_token  # Guarda el token WHILE

        # Espera '(' después de 'while'
        if not self._expected_token(TokenType.LPAREN):
            return None

        # Avanza al inicio de la condición
        self._advance_tokens()

        # Parsea la condición
        condition = self._parse_expression(Precedences.LOWEST)

        # Espera ')' cerrando la condición
        if not self._expected_token(TokenType.RPAREN):
            return None

        # Espera '{' abriendo el cuerpo del while
        if not self._expected_token(TokenType.LBRACE):
            return None

        # Parsea el bloque de sentencias del cuerpo
        body = self._parse_block_statement()

        assert condition is not None
        return ast.WhileStatement(token=token, condition=condition, body=body)

    def _parse_for_statement(self) -> Optional[ast.ForStatement]:
        """
        Parsea una sentencia FOR: for (<init>; <cond>; <update>) { <cuerpo> }

        Estructura esperada:
          FOR  LPAREN  <init_stmt>  SEMICOLON  <cond_expr>  SEMICOLON
          <update_stmt>  RPAREN  LBRACE  <sentencias>  RBRACE

        Ejemplo:
          for (let i = 0; i < 10; let i = i + 1) {
              print(i);
          }
        """
        assert self._current_token is not None
        token = self._current_token  # Guarda el token FOR

        # Espera '(' después de 'for'
        if not self._expected_token(TokenType.LPAREN):
            return None

        # ── Parsea la inicialización ─────────────────────────────────────
        self._advance_tokens()
        init: Optional[ast.Statement] = None
        if not self._current_token_is(TokenType.SEMICOLON):
            init = self._parse_statement()

        # Espera ';' separando init de condición
        if not self._current_token_is(TokenType.SEMICOLON):
            if not self._expected_token(TokenType.SEMICOLON):
                return None
        else:
            # Ya estamos en el ';', avanzamos
            pass

        # ── Parsea la condición de continuación ──────────────────────────
        self._advance_tokens()
        condition: Optional[ast.Expression] = None
        if not self._current_token_is(TokenType.SEMICOLON):
            condition = self._parse_expression(Precedences.LOWEST)

        # Espera ';' separando condición de actualización
        if not self._expected_token(TokenType.SEMICOLON):
            return None

        # ── Parsea la actualización ──────────────────────────────────────
        self._advance_tokens()
        update: Optional[ast.Statement] = None
        if not self._current_token_is(TokenType.RPAREN):
            update = self._parse_statement()

        # Espera ')' cerrando la cláusula del for
        if not self._current_token_is(TokenType.RPAREN):
            if not self._expected_token(TokenType.RPAREN):
                return None

        # Espera '{' abriendo el cuerpo del for
        if not self._expected_token(TokenType.LBRACE):
            return None

        # Parsea el bloque del cuerpo
        body = self._parse_block_statement()

        return ast.ForStatement(
            token=token,
            init=init,
            condition=condition,
            update=update,
            body=body
        )

    def _parse_break_statement(self) -> ast.BreakStatement:
        """
        Parsea una sentencia BREAK: break;

        Simplemente consume el token BREAK y el punto y coma opcional.
        """
        assert self._current_token is not None
        token = self._current_token

        # Consume el punto y coma opcional
        if self._peek_token_is(TokenType.SEMICOLON):
            self._advance_tokens()

        return ast.BreakStatement(token=token)

    def _parse_continue_statement(self) -> ast.ContinueStatement:
        """
        Parsea una sentencia CONTINUE: continue;

        Simplemente consume el token CONTINUE y el punto y coma opcional.
        """
        assert self._current_token is not None
        token = self._current_token

        # Consume el punto y coma opcional
        if self._peek_token_is(TokenType.SEMICOLON):
            self._advance_tokens()

        return ast.ContinueStatement(token=token)

    def _parse_expression_statement(self) -> Optional[ast.ExpressionStatement]:
        """
        Parsea una expresión usada como sentencia completa.

        Cuando una expresión aparece sola en una línea (e.g. una llamada
        a función sin asignar su resultado), se envuelve en ExpressionStatement.

        Ejemplo:
          miFuncion(x);  ← esto es una ExpressionStatement
        """
        assert self._current_token is not None
        token = self._current_token

        # Parsea la expresión con la precedencia más baja
        expression = self._parse_expression(Precedences.LOWEST)

        # Consume el punto y coma opcional
        if self._peek_token_is(TokenType.SEMICOLON):
            self._advance_tokens()

        return ast.ExpressionStatement(token=token, expression=expression)

    # ─────────────────────────────────────────────────────────────────────────
    # PARSEO DE BLOQUES
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_block_statement(self) -> ast.BlockStatement:
        """
        Parsea un bloque de sentencias: { stmt1; stmt2; ... }

        Se asume que _current_token ya apunta al token '{'.
        Parsea sentencias hasta encontrar '}' o EOF.

        Retorna un BlockStatement con la lista de sentencias internas.
        """
        assert self._current_token is not None
        block = ast.BlockStatement(token=self._current_token)

        # Avanza más allá del '{'
        self._advance_tokens()

        # Parsea sentencias hasta encontrar '}' o llegar a EOF
        while not self._current_token_is(TokenType.RBRACE) and \
              not self._current_token_is(TokenType.EOF):
            statement = self._parse_statement()
            if statement is not None:
                block.statements.append(statement)
            self._advance_tokens()

        return block

    # ─────────────────────────────────────────────────────────────────────────
    # PARSEO DE EXPRESIONES (Pratt Parsing)
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_expression(self, precedence: Precedences) -> Optional[ast.Expression]:
        """
        Corazón del Pratt Parser: parsea una expresión respetando la precedencia.

        Algoritmo:
          1. Busca una función prefix para el token actual. Si no existe → error.
          2. Llama a la función prefix para obtener la expresión izquierda.
          3. Mientras el siguiente token tenga mayor precedencia que la actual:
             a. Busca una función infix para el siguiente token.
             b. Avanza al siguiente token.
             c. Llama a la función infix pasándole la expresión izquierda.
             d. El resultado se convierte en la nueva expresión izquierda.
          4. Retorna la expresión acumulada.

        Parámetros:
          precedence → Nivel mínimo de precedencia. Solo los operadores con
                       precedencia MAYOR se "pegan" a esta expresión.
        """
        assert self._current_token is not None

        # Paso 1: Buscar función prefix
        prefix_fn = self._prefix_parse_fns.get(self._current_token.token_type)

        if prefix_fn is None:
            self._errors.append(
                f'No se encontró función de parseo prefix para '
                f'{self._current_token.token_type.name}'
            )
            return None

        # Paso 2: Ejecutar función prefix → obtener expresión izquierda
        left_expression = prefix_fn()

        # Paso 3: Mientras haya operadores infix con mayor precedencia
        while not self._peek_token_is(TokenType.SEMICOLON) and \
              precedence < self._peek_precedence():

            assert self._peek_token is not None
            infix_fn = self._infix_parse_fns.get(self._peek_token.token_type)

            if infix_fn is None:
                return left_expression

            # Avanza al token del operador infix
            self._advance_tokens()

            # Ejecuta la función infix con la expresión izquierda
            assert left_expression is not None
            left_expression = infix_fn(left_expression)

        return left_expression

    # ─────────────────────────────────────────────────────────────────────────
    # FUNCIONES PREFIX (parsean tokens al inicio de una expresión)
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_identifier(self) -> ast.Identifier:
        """
        Parsea un identificador (nombre de variable o función).

        Simplemente crea un nodo Identifier con el token actual.
        Ejemplo: 'x', 'resultado', 'miFuncion'
        """
        assert self._current_token is not None
        return ast.Identifier(
            token=self._current_token,
            value=self._current_token.literal
        )

    def _parse_integer_literal(self) -> Optional[ast.IntegerLiteral]:
        """
        Parsea un literal entero.

        Convierte el texto del token a int. Si falla → registra error.
        Ejemplo: '42' → IntegerLiteral(value=42)
        """
        assert self._current_token is not None

        try:
            value = int(self._current_token.literal)
        except ValueError:
            self._errors.append(
                f'No se pudo parsear "{self._current_token.literal}" como entero'
            )
            return None

        return ast.IntegerLiteral(token=self._current_token, value=value)

    def _parse_float_literal(self) -> Optional[ast.FloatLiteral]:
        """
        Parsea un literal flotante (decimal).

        Convierte el texto del token a float. Si falla → registra error.
        Ejemplo: '3.14' → FloatLiteral(value=3.14)
        """
        assert self._current_token is not None

        try:
            value = float(self._current_token.literal)
        except ValueError:
            self._errors.append(
                f'No se pudo parsear "{self._current_token.literal}" como flotante'
            )
            return None

        return ast.FloatLiteral(token=self._current_token, value=value)

    def _parse_string_literal(self) -> ast.StringLiteral:
        """
        Parsea un literal de cadena de texto.

        El lexer ya extrajo el contenido sin comillas.
        Ejemplo: Token(STRING, 'hola mundo') → StringLiteral(value='hola mundo')
        """
        assert self._current_token is not None
        return ast.StringLiteral(
            token=self._current_token,
            value=self._current_token.literal
        )

    def _parse_boolean_literal(self) -> ast.BooleanLiteral:
        """
        Parsea un literal booleano: true o false.

        Determina el valor Python (True/False) según el tipo de token.
        """
        assert self._current_token is not None
        return ast.BooleanLiteral(
            token=self._current_token,
            value=self._current_token.token_type == TokenType.TRUE
        )

    def _parse_prefix_expression(self) -> ast.PrefixExpression:
        """
        Parsea una expresión con operador prefijo: <operador><expresión>

        Operadores soportados: '-' (negación numérica), '!' (negación lógica)

        Ejemplo:
          -5     → PrefixExpression(operator='-', right=IntegerLiteral(5))
          !true  → PrefixExpression(operator='!', right=BooleanLiteral(true))
        """
        assert self._current_token is not None
        token = self._current_token
        operator = self._current_token.literal

        # Avanza al operando (la expresión a la derecha del operador)
        self._advance_tokens()

        # Parsea el operando con precedencia PREFIX (alta)
        right = self._parse_expression(Precedences.PREFIX)

        return ast.PrefixExpression(token=token, operator=operator, right=right)

    def _parse_grouped_expression(self) -> Optional[ast.Expression]:
        """
        Parsea una expresión agrupada entre paréntesis: ( <expresión> )

        Los paréntesis sirven para alterar la precedencia de operadores.
        Ejemplo: (5 + 3) * 2

        Retorna la expresión interna sin los paréntesis (no crea nodo especial).
        """
        # Avanza más allá del '('
        self._advance_tokens()

        # Parsea la expresión interna con la menor precedencia
        expression = self._parse_expression(Precedences.LOWEST)

        # Espera ')' cerrando el grupo
        if not self._expected_token(TokenType.RPAREN):
            return None

        return expression

    def _parse_if_expression(self) -> Optional[ast.IfExpression]:
        """
        Parsea una expresión condicional: if (...) { } elseif (...) { } else { }

        Soporta:
          - Un bloque if principal con condición
          - Cero o más bloques elseif con condición
          - Un bloque else opcional sin condición

        Ejemplo:
          if (x > 0) {
              print("positivo");
          } elseif (x == 0) {
              print("cero");
          } else {
              print("negativo");
          }
        """
        assert self._current_token is not None
        token = self._current_token  # Guarda el token IF

        # ── Parsea la condición del if principal ─────────────────────────
        if not self._expected_token(TokenType.LPAREN):
            return None

        self._advance_tokens()
        condition = self._parse_expression(Precedences.LOWEST)

        if not self._expected_token(TokenType.RPAREN):
            return None

        # ── Parsea el bloque consecuencia ────────────────────────────────
        if not self._expected_token(TokenType.LBRACE):
            return None

        consequence = self._parse_block_statement()

        # ── Parsea ramas elseif (puede haber 0 o más) ───────────────────
        alternatives: List[tuple] = []

        while self._peek_token_is(TokenType.ELSEIF):
            self._advance_tokens()  # consume 'elseif'

            # Parsea condición del elseif
            if not self._expected_token(TokenType.LPAREN):
                return None

            self._advance_tokens()
            alt_condition = self._parse_expression(Precedences.LOWEST)

            if not self._expected_token(TokenType.RPAREN):
                return None

            # Parsea bloque del elseif
            if not self._expected_token(TokenType.LBRACE):
                return None

            alt_block = self._parse_block_statement()
            alternatives.append((alt_condition, alt_block))

        # ── Parsea bloque else (opcional) ────────────────────────────────
        else_block: Optional[ast.BlockStatement] = None

        if self._peek_token_is(TokenType.ELSE):
            self._advance_tokens()  # consume 'else'

            if not self._expected_token(TokenType.LBRACE):
                return None

            else_block = self._parse_block_statement()

        assert condition is not None
        return ast.IfExpression(
            token=token,
            condition=condition,
            consequence=consequence,
            alternatives=alternatives,
            else_block=else_block
        )

    def _parse_function_literal(self) -> Optional[ast.FunctionLiteral]:
        """
        Parsea la definición de una función: function(<params>) { <cuerpo> }

        Ejemplo:
          function(x, y) {
              return x + y;
          }

        Las funciones son valores de primera clase: se pueden asignar a
        variables, pasar como argumentos, retornar desde otras funciones.
        """
        assert self._current_token is not None
        token = self._current_token  # Guarda el token FUNCTION

        # Espera '(' abriendo la lista de parámetros
        if not self._expected_token(TokenType.LPAREN):
            return None

        # Parsea la lista de parámetros
        parameters = self._parse_function_parameters()

        # Espera '{' abriendo el cuerpo de la función
        if not self._expected_token(TokenType.LBRACE):
            return None

        # Parsea el cuerpo de la función
        body = self._parse_block_statement()

        return ast.FunctionLiteral(
            token=token,
            parameters=parameters,
            body=body
        )

    def _parse_function_parameters(self) -> List[ast.Identifier]:
        """
        Parsea la lista de parámetros de una función.

        Formato: (param1, param2, param3)
        Se asume que _current_token apunta al '(' de apertura.

        Retorna lista de Identifier. Puede estar vacía si no hay parámetros.
        """
        parameters: List[ast.Identifier] = []

        # Caso: función sin parámetros → function()
        if self._peek_token_is(TokenType.RPAREN):
            self._advance_tokens()  # consume ')'
            return parameters

        # Avanza al primer parámetro
        self._advance_tokens()

        # Parsea el primer parámetro
        assert self._current_token is not None
        parameters.append(ast.Identifier(
            token=self._current_token,
            value=self._current_token.literal
        ))

        # Parsea parámetros adicionales separados por coma
        while self._peek_token_is(TokenType.COMMA):
            self._advance_tokens()  # consume ','
            self._advance_tokens()  # avanza al siguiente parámetro

            assert self._current_token is not None
            parameters.append(ast.Identifier(
                token=self._current_token,
                value=self._current_token.literal
            ))

        # Espera ')' cerrando la lista de parámetros
        if not self._expected_token(TokenType.RPAREN):
            return []

        return parameters

    # ─────────────────────────────────────────────────────────────────────────
    # FUNCIONES INFIX (parsean tokens en medio de dos expresiones)
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_infix_expression(self, left: ast.Expression) -> ast.InfixExpression:
        """
        Parsea una expresión infija: <izquierda> <operador> <derecha>

        Recibe la expresión izquierda (ya parseada) como parámetro.
        El _current_token apunta al operador.

        Ejemplo:
          Para "5 + 3":
            left = IntegerLiteral(5)
            _current_token = Token(PLUS, '+')
            → parsea 3 como right
            → InfixExpression(left=5, op='+', right=3)
        """
        assert self._current_token is not None
        token = self._current_token
        operator = self._current_token.literal

        # Obtiene la precedencia del operador actual
        precedence = self._current_precedence()

        # Avanza al operando derecho
        self._advance_tokens()

        # Parsea la expresión derecha con la misma precedencia
        # (esto hace que los operadores del mismo nivel sean left-associative)
        right = self._parse_expression(precedence)

        return ast.InfixExpression(
            token=token,
            left=left,
            operator=operator,
            right=right
        )

    def _parse_call_expression(self, function: ast.Expression) -> ast.CallExpression:
        """
        Parsea una llamada a función: <función>(<argumentos>)

        Recibe la expresión de la función (ya parseada) como parámetro.
        El _current_token apunta al '(' de la llamada.

        Ejemplo:
          Para "suma(1, 2)":
            function = Identifier("suma")
            _current_token = Token(LPAREN, '(')
            → parsea [1, 2] como argumentos
            → CallExpression(function="suma", arguments=[1, 2])
        """
        assert self._current_token is not None
        token = self._current_token

        # Parsea la lista de argumentos
        arguments = self._parse_call_arguments()

        return ast.CallExpression(
            token=token,
            function=function,
            arguments=arguments
        )

    def _parse_call_arguments(self) -> List[ast.Expression]:
        """
        Parsea la lista de argumentos de una llamada a función.

        Formato: (arg1, arg2, arg3)
        Se asume que _current_token apunta al '(' de apertura.

        Retorna lista de Expression. Puede estar vacía si hay llamada sin args.
        """
        arguments: List[ast.Expression] = []

        # Caso: llamada sin argumentos → f()
        if self._peek_token_is(TokenType.RPAREN):
            self._advance_tokens()  # consume ')'
            return arguments

        # Avanza al primer argumento
        self._advance_tokens()

        # Parsea el primer argumento
        arg = self._parse_expression(Precedences.LOWEST)
        if arg is not None:
            arguments.append(arg)

        # Parsea argumentos adicionales separados por coma
        while self._peek_token_is(TokenType.COMMA):
            self._advance_tokens()  # consume ','
            self._advance_tokens()  # avanza al siguiente argumento

            arg = self._parse_expression(Precedences.LOWEST)
            if arg is not None:
                arguments.append(arg)

        # Espera ')' cerrando la lista de argumentos
        if not self._expected_token(TokenType.RPAREN):
            return []

        return arguments

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODOS AUXILIARES DE TOKENS
    # ─────────────────────────────────────────────────────────────────────────

    def _advance_tokens(self) -> None:
        """
        Avanza al siguiente token.

        El token actual pasa a _current_token y se lee el siguiente
        del lexer en _peek_token (look-ahead de 1).
        """
        self._current_token = self._peek_token
        self._peek_token = self._lexer.next_token()

    def _current_token_is(self, token_type: TokenType) -> bool:
        """Verifica si el token actual es del tipo indicado."""
        assert self._current_token is not None
        return self._current_token.token_type == token_type

    def _peek_token_is(self, token_type: TokenType) -> bool:
        """Verifica si el siguiente token (peek) es del tipo indicado."""
        assert self._peek_token is not None
        return self._peek_token.token_type == token_type

    def _expected_token(self, token_type: TokenType) -> bool:
        """
        Verifica que el siguiente token sea del tipo esperado y avanza.

        Si el peek token coincide con el tipo esperado:
          → Avanza al siguiente token y retorna True.
        Si no coincide:
          → Registra un error descriptivo y retorna False.

        Este método se usa para tokens obligatorios en la gramática.
        Ejemplo: después de 'let x' debe venir '='.
        """
        if self._peek_token_is(token_type):
            self._advance_tokens()
            return True

        # Registra un error con información útil para debug
        assert self._peek_token is not None
        self._errors.append(
            f'Se esperaba {token_type.name}, '
            f'pero se obtuvo {self._peek_token.token_type.name}'
        )
        return False

    def _current_precedence(self) -> Precedences:
        """
        Retorna la precedencia del token actual.

        Busca en la tabla PRECEDENCES. Si no lo encuentra (e.g. un ';'),
        retorna LOWEST como valor por defecto.
        """
        assert self._current_token is not None
        return PRECEDENCES.get(
            self._current_token.token_type,
            Precedences.LOWEST
        )

    def _peek_precedence(self) -> Precedences:
        """
        Retorna la precedencia del siguiente token (peek).

        Se usa en el bucle principal de _parse_expression para decidir
        si el siguiente operador "captura" la expresión actual.
        """
        assert self._peek_token is not None
        return PRECEDENCES.get(
            self._peek_token.token_type,
            Precedences.LOWEST
        )