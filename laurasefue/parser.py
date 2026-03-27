# =============================================================================
# parser.py — Analizador Sintáctico (Parser) — Pratt Parser
#
# El Parser toma la secuencia de tokens del Lexer y construye el AST.
#
# Se implementa un PRATT PARSER (también llamado Top-Down Operator Precedence),
# que maneja la precedencia de operadores de forma elegante mediante una tabla
# de funciones de parseo asociadas a cada tipo de token.
#
# Conceptos clave del Pratt Parser:
#   - "nud" (null denotation): función que parsea un token que aparece al
#     INICIO de una expresión (e.g. un número, un identificador, un '(').
#   - "led" (left denotation): función que parsea un token que aparece en
#     POSICIÓN INFIJA (e.g. +, -, *, etc.) recibiendo la expresión izquierda.
#   - Cada token tiene una PRECEDENCIA numérica; a mayor número, más fuerte
#     la vinculación con sus operandos.
#
# Tabla de precedencias (de menor a mayor):
#   LOWEST    = 1   → base
#   OR        = 2   → or
#   AND       = 3   → and
#   EQUALS    = 4   → ==, !=
#   LESSGREAT = 5   → <, >, <=, >=
#   SUM       = 6   → +, -
#   PRODUCT   = 7   → *, /, %
#   PREFIX    = 8   → -x, !x  (operadores unarios)
#   POWER     = 9   → ^
#   CALL      = 10  → miFuncion(args)
# =============================================================================

from enum import IntEnum               # Para el enum de precedencias
from typing import (
    Callable, Dict, List, Optional
)

from laurasefue.tokens import Token, TokenType
from laurasefue import ast             # Nodos del AST
from laurasefue.lexer import Lexer


# ─────────────────────────────────────────────────────────────────────────────
# PRECEDENCIAS
# ─────────────────────────────────────────────────────────────────────────────

class Precedence(IntEnum):
    """
    Niveles de precedencia de los operadores.

    Un operador con mayor precedencia "atrae" a sus operandos más fuerte.
    Por ejemplo, * tiene mayor precedencia que +, por eso en 2 + 3 * 4
    primero se agrupa 3 * 4 y luego se suma.
    """
    LOWEST    = 1   # Precedencia base (sin operador)
    OR        = 2   # or
    AND       = 3   # and
    EQUALS    = 4   # == y !=
    LESSGREAT = 5   # < > <= >=
    SUM       = 6   # + y -
    PRODUCT   = 7   # * / %
    PREFIX    = 8   # -x  !x  (operadores prefijos)
    POWER     = 9   # ^
    CALL      = 10  # f(args)


# Tabla que mapea cada TokenType a su precedencia como operador infijo.
# Si un token no aparece aquí, se asume Precedence.LOWEST.
PRECEDENCES: Dict[TokenType, Precedence] = {
    TokenType.OR:       Precedence.OR,
    TokenType.AND:      Precedence.AND,
    TokenType.EQ:       Precedence.EQUALS,
    TokenType.DIF:      Precedence.EQUALS,
    TokenType.LT:       Precedence.LESSGREAT,
    TokenType.LTE:      Precedence.LESSGREAT,
    TokenType.GT:       Precedence.LESSGREAT,
    TokenType.GTE:      Precedence.LESSGREAT,
    TokenType.PLUS:     Precedence.SUM,
    TokenType.MINUS:    Precedence.SUM,
    TokenType.MULTIPLY: Precedence.PRODUCT,
    TokenType.DIVISION: Precedence.PRODUCT,
    TokenType.MOD:      Precedence.PRODUCT,
    TokenType.POW:      Precedence.POWER,
    TokenType.LPAREN:   Precedence.CALL,
}

# Tipos de funciones de parseo
# PrefixParseFn: función que parsea cuando el token aparece al inicio
PrefixParseFn = Callable[[], Optional[ast.Expression]]
# InfixParseFn: función que parsea en posición infija; recibe la expr. izquierda
InfixParseFn  = Callable[[ast.Expression], Optional[ast.Expression]]


# ─────────────────────────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────────────────────────

class Parser:
    """
    Construye el AST a partir de la secuencia de tokens del Lexer.

    Mantiene dos "punteros" de tokens:
      _current_token  → el token que se está procesando ahora
      _peek_token     → el token siguiente (look-ahead de 1)

    Esto permite tomar decisiones sin avanzar el cursor prematuramente.
    """

    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer

        # Lista de errores de parseo encontrados
        self._errors: List[str] = []

        # Tokens actuales (se inicializan vacíos; se llenan en _advance_tokens)
        self._current_token: Optional[Token] = None
        self._peek_token: Optional[Token] = None

        # ── Registro de funciones de parseo para posición PREFIJA ─────────────
        # Cada TokenType tiene asociada una función que sabe parsear ese token
        # cuando aparece al inicio de una expresión.
        self._prefix_parse_fns: Dict[TokenType, PrefixParseFn] = {
            TokenType.IDENTIFIER: self._parse_identifier,
            TokenType.INTEGER:    self._parse_integer_literal,
            TokenType.FLOAT:      self._parse_float_literal,
            TokenType.STRING:     self._parse_string_literal,
            TokenType.TRUE:       self._parse_boolean_literal,
            TokenType.FALSE:      self._parse_boolean_literal,
            TokenType.NEGATION:   self._parse_prefix_expression,
            TokenType.MINUS:      self._parse_prefix_expression,
            TokenType.LPAREN:     self._parse_grouped_expression,
            TokenType.IF:         self._parse_if_expression,
            TokenType.FUNCTION:   self._parse_function_literal,
        }

        # ── Registro de funciones de parseo para posición INFIJA ──────────────
        # Tokens que actúan como operadores binarios.
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

        # Carga los dos primeros tokens para que _current y _peek estén listos
        self._advance_tokens()
        self._advance_tokens()

    # ── Propiedad pública ────────────────────────────────────────────────────

    @property
    def errors(self) -> List[str]:
        """Lista de errores de parseo encontrados."""
        return self._errors

    # ─────────────────────────────────────────────────────────────────────────
    # PUNTO DE ENTRADA PRINCIPAL
    # ─────────────────────────────────────────────────────────────────────────

    def parse_program(self) -> ast.Program:
        """
        Parsea el programa completo y retorna el nodo raíz (Program).

        Itera sobre todos los tokens, parseando una sentencia a la vez,
        hasta llegar al token EOF.
        """
        program = ast.Program()

        # Procesa sentencias mientras no lleguemos al final del archivo
        while self._current_token.token_type != TokenType.EOF:
            statement = self._parse_statement()
            if statement is not None:
                program.statements.append(statement)
            # Avanza al siguiente token para parsear la siguiente sentencia
            self._advance_tokens()

        return program

    # ─────────────────────────────────────────────────────────────────────────
    # PARSEO DE SENTENCIAS
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_statement(self) -> Optional[ast.Statement]:
        """
        Decide qué tipo de sentencia parsear según el token actual.

        Retorna el nodo de sentencia correspondiente, o None si hay error.
        """
        match self._current_token.token_type:
            case TokenType.LET:
                return self._parse_let_statement()
            case TokenType.RETURN:
                return self._parse_return_statement()
            case TokenType.WHILE:
                return self._parse_while_statement()
            case TokenType.FOR:
                return self._parse_for_statement()
            case TokenType.PRINT:
                return self._parse_print_statement()
            case TokenType.BREAK:
                # 'break' es una sentencia de control: sale del bucle actual
                return self._parse_break_statement()
            case TokenType.CONTINUE:
                # 'continue' es una sentencia de control: salta al siguiente ciclo
                return self._parse_continue_statement()
            case _:
                # Si no es un statement conocido, se parsea como expresión
                return self._parse_expression_statement()

    def _parse_let_statement(self) -> Optional[ast.LetStatement]:
        """
        Parsea: let <identificador> = <expresión>;

        Ejemplo: let x = 5 + 3;
        """
        token = self._current_token   # Guarda el token 'let'

        # El siguiente token DEBE ser un identificador
        if not self._expected_token(TokenType.IDENTIFIER):
            return None

        # Crea el nodo Identifier con el nombre de la variable
        name = ast.Identifier(
            token=self._current_token,
            value=self._current_token.literal
        )

        # El siguiente token DEBE ser '='
        if not self._expected_token(TokenType.ASSIGN):
            return None

        # Avanza al inicio de la expresión del valor
        self._advance_tokens()

        # Parsea la expresión del lado derecho del '='
        value = self._parse_expression(Precedence.LOWEST)

        # Si hay punto y coma, lo consumimos (es opcional en expresiones)
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        node = ast.LetStatement(token=token, name=name, value=value)

        # Si el valor es una función, guardamos el nombre para la recursión.
        # Esto permite que una función se llame a sí misma por su nombre.
        if isinstance(node.value, ast.FunctionLiteral):
            node.value.name = name.value

        return node

    def _parse_return_statement(self) -> Optional[ast.ReturnStatement]:
        """
        Parsea: return <expresión>;

        Ejemplo: return x + 1;
        """
        token = self._current_token   # Guarda el token 'return'

        # Avanza para leer la expresión a retornar
        self._advance_tokens()

        # Parsea la expresión de retorno
        return_value = self._parse_expression(Precedence.LOWEST)

        # Consume el punto y coma si existe
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return ast.ReturnStatement(token=token, return_value=return_value)

    def _parse_expression_statement(self) -> Optional[ast.ExpressionStatement]:
        """
        Parsea una expresión usada como sentencia completa.

        Ejemplo: miFuncion(x);   o simplemente   x + 5;
        """
        token = self._current_token
        expression = self._parse_expression(Precedence.LOWEST)

        # El punto y coma es opcional al final de una expresión-sentencia
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return ast.ExpressionStatement(token=token, expression=expression)

    def _parse_while_statement(self) -> Optional[ast.WhileStatement]:
        """
        Parsea: while (<condición>) { <cuerpo> }

        Ejemplo:
            while (i < 10) {
                print(i);
                let i = i + 1;
            }
        """
        token = self._current_token   # Token 'while'

        # Espera '(' después de 'while'
        if not self._expected_token(TokenType.LPAREN):
            return None

        self._advance_tokens()   # Avanza al inicio de la condición

        # Parsea la condición entre paréntesis
        condition = self._parse_expression(Precedence.LOWEST)

        # Espera ')' para cerrar la condición
        if not self._expected_token(TokenType.RPAREN):
            return None

        # Espera '{' para abrir el cuerpo
        if not self._expected_token(TokenType.LBRACE):
            return None

        # Parsea el bloque del cuerpo del while
        body = self._parse_block_statement()

        return ast.WhileStatement(token=token, condition=condition, body=body)

    def _parse_for_statement(self) -> Optional[ast.ForStatement]:
        """
        Parsea: for (<init>; <condición>; <actualización>) { <cuerpo> }

        Ejemplo:
            for (let i = 0; i < 10; let i = i + 1) {
                print(i);
            }

        Nota: el init y el update pueden ser sentencias let o de expresión.
        """
        token = self._current_token   # Token 'for'

        if not self._expected_token(TokenType.LPAREN):
            return None

        self._advance_tokens()   # Avanza al inicio de init

        # ── Parsea la inicialización (let o expresión) ────────────────────────
        # Aquí NO usamos _parse_let_statement ni _parse_expression_statement
        # porque esos métodos consumen el ';', pero en el for el ';' separa
        # las tres partes de la cabecera. Por eso parseamos manualmente.
        init: Optional[ast.Statement] = None
        if self._current_token.token_type == TokenType.SEMICOLON:
            # init vacío: for (; cond; update)
            pass
        elif self._current_token.token_type == TokenType.LET:
            # Parsea el let pero sin consumir el ';'
            let_token = self._current_token
            if not self._expected_token(TokenType.IDENTIFIER):
                return None
            name = ast.Identifier(
                token=self._current_token,
                value=self._current_token.literal
            )
            if not self._expected_token(TokenType.ASSIGN):
                return None
            self._advance_tokens()
            value = self._parse_expression(Precedence.LOWEST)
            init = ast.LetStatement(token=let_token, name=name, value=value)
        else:
            # Expresión genérica como init
            expr_token = self._current_token
            expr = self._parse_expression(Precedence.LOWEST)
            init = ast.ExpressionStatement(token=expr_token, expression=expr)

        # Consume el ';' separador entre init y condition
        if not self._expected_token(TokenType.SEMICOLON):
            return None
        self._advance_tokens()   # Avanza al inicio de la condición

        # ── Parsea la condición ───────────────────────────────────────────────
        condition: Optional[ast.Expression] = None
        if self._current_token.token_type != TokenType.SEMICOLON:
            condition = self._parse_expression(Precedence.LOWEST)

        # Consume el ';' separador entre condition y update
        if not self._expected_token(TokenType.SEMICOLON):
            return None
        self._advance_tokens()   # Avanza al inicio del update

        # ── Parsea la actualización ───────────────────────────────────────────
        update: Optional[ast.Statement] = None
        if self._current_token.token_type != TokenType.RPAREN:
            if self._current_token.token_type == TokenType.LET:
                # Parsea el let del update (sin consumir ';')
                let_token = self._current_token
                if not self._expected_token(TokenType.IDENTIFIER):
                    return None
                name = ast.Identifier(
                    token=self._current_token,
                    value=self._current_token.literal
                )
                if not self._expected_token(TokenType.ASSIGN):
                    return None
                self._advance_tokens()
                value = self._parse_expression(Precedence.LOWEST)
                update = ast.LetStatement(token=let_token, name=name, value=value)
            else:
                expr_token = self._current_token
                expr = self._parse_expression(Precedence.LOWEST)
                update = ast.ExpressionStatement(token=expr_token, expression=expr)

        # Espera ')' para cerrar la cabecera del for
        if not self._expected_token(TokenType.RPAREN):
            return None

        # Espera '{' para el cuerpo
        if not self._expected_token(TokenType.LBRACE):
            return None

        body = self._parse_block_statement()

        return ast.ForStatement(
            token=token,
            init=init,
            condition=condition,
            update=update,
            body=body
        )

    def _parse_print_statement(self) -> Optional[ast.PrintStatement]:
        """
        Parsea: print(<expresión>);

        Ejemplo: print("hola " + nombre);
        """
        token = self._current_token   # Token 'print'

        if not self._expected_token(TokenType.LPAREN):
            return None

        self._advance_tokens()   # Al inicio del argumento

        value = self._parse_expression(Precedence.LOWEST)

        if not self._expected_token(TokenType.RPAREN):
            return None

        # Punto y coma opcional
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()

        return ast.PrintStatement(token=token, value=value)

    def _parse_block_statement(self) -> ast.BlockStatement:
        """
        Parsea un bloque de sentencias entre llaves: { stmt; stmt; ... }

        Asume que self._current_token es '{' al entrar.
        Sale cuando encuentra '}' o EOF.
        """
        token = self._current_token   # Token '{'
        block = ast.BlockStatement(token=token)

        self._advance_tokens()   # Avanza al primer token del cuerpo

        # Lee sentencias hasta encontrar '}' o fin de archivo
        while (self._current_token.token_type != TokenType.RBRACE and
               self._current_token.token_type != TokenType.EOF):
            statement = self._parse_statement()
            if statement is not None:
                block.statements.append(statement)
            self._advance_tokens()

        return block

    # ─────────────────────────────────────────────────────────────────────────
    # PARSEO DE EXPRESIONES (Pratt)
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_expression(self, precedence: Precedence) -> Optional[ast.Expression]:
        """
        Corazón del Pratt Parser. Parsea una expresión respetando precedencias.

        Algoritmo:
          1. Busca una función de parseo PREFIJA para el token actual.
          2. Llama a esa función para obtener la expresión izquierda.
          3. Mientras el siguiente token tenga mayor precedencia que la actual,
             llama a la función INFIJA del siguiente token, pasando la izquierda.
          4. Retorna la expresión final (que puede ser un árbol de nodos).

        Ejemplo para "1 + 2 * 3":
          - _parse_expression(LOWEST)
          - left = IntegerLiteral(1)
          - peek '+' tiene prec SUM > LOWEST → entra al while
          - left = InfixExpression(1, '+', _parse_expression(SUM))
          - dentro de _parse_expression(SUM):
              - left = IntegerLiteral(2)
              - peek '*' tiene prec PRODUCT > SUM → entra al while
              - left = InfixExpression(2, '*', IntegerLiteral(3))
          - resultado: InfixExpression(1, '+', InfixExpression(2, '*', 3))
        """
        # Busca la función de parseo prefija para el token actual
        prefix_fn = self._prefix_parse_fns.get(self._current_token.token_type)

        if prefix_fn is None:
            # No hay función prefija → no reconocemos este token como inicio de expr.
            self._errors.append(
                f'No se encontró función de parseo para '
                f'{self._current_token.token_type.name!r} '
                f'(literal: {self._current_token.literal!r})'
            )
            return None

        # Parsea la parte izquierda de la expresión
        left = prefix_fn()

        # Mientras el siguiente token tenga mayor precedencia, continúa
        while (self._peek_token.token_type != TokenType.SEMICOLON and
               precedence < self._peek_precedence()):

            # Busca la función infija para el siguiente token
            infix_fn = self._infix_parse_fns.get(self._peek_token.token_type)
            if infix_fn is None:
                return left

            self._advance_tokens()   # Avanza al operador infijo
            left = infix_fn(left)    # Construye el nodo infijo

        return left

    # ─────────────────────────────────────────────────────────────────────────
    # FUNCIONES DE PARSEO PREFIJAS
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_identifier(self) -> ast.Identifier:
        """Parsea un identificador simple: nombre de variable o función."""
        return ast.Identifier(
            token=self._current_token,
            value=self._current_token.literal
        )

    def _parse_integer_literal(self) -> Optional[ast.IntegerLiteral]:
        """
        Parsea un literal entero.

        Convierte el literal string del token a int Python.
        Si la conversión falla, registra un error.
        """
        token = self._current_token
        try:
            value = int(token.literal)
        except ValueError:
            self._errors.append(
                f'No se pudo parsear "{token.literal}" como entero.'
            )
            return None
        return ast.IntegerLiteral(token=token, value=value)

    def _parse_float_literal(self) -> Optional[ast.FloatLiteral]:
        """Parsea un literal float."""
        token = self._current_token
        try:
            value = float(token.literal)
        except ValueError:
            self._errors.append(
                f'No se pudo parsear "{token.literal}" como flotante.'
            )
            return None
        return ast.FloatLiteral(token=token, value=value)

    def _parse_string_literal(self) -> ast.StringLiteral:
        """Parsea un literal string (ya sin las comillas: el Lexer las quitó)."""
        return ast.StringLiteral(
            token=self._current_token,
            value=self._current_token.literal
        )

    def _parse_boolean_literal(self) -> ast.BooleanLiteral:
        """Parsea los literales booleanos: true y false."""
        return ast.BooleanLiteral(
            token=self._current_token,
            value=(self._current_token.token_type == TokenType.TRUE)
        )

    def _parse_prefix_expression(self) -> Optional[ast.PrefixExpression]:
        """
        Parsea una expresión prefija: <operador><expresión>

        Ejemplos: !verdadero,  -x,  -(5 + 3)
        """
        token = self._current_token         # El token del operador (! o -)
        operator = self._current_token.literal

        self._advance_tokens()   # Avanza a la expresión que sigue al operador

        # Parsea la expresión de la derecha con alta precedencia (PREFIX)
        # para que -5 + 3 se interprete como (-5) + 3 y no -(5+3)
        right = self._parse_expression(Precedence.PREFIX)

        return ast.PrefixExpression(token=token, operator=operator, right=right)

    def _parse_grouped_expression(self) -> Optional[ast.Expression]:
        """
        Parsea una expresión entre paréntesis: ( <expresión> )

        Los paréntesis simplemente agrupan/priorizan; no crean un nodo propio.
        """
        self._advance_tokens()   # Salta el '('

        # Parsea la expresión interior con la precedencia más baja
        expression = self._parse_expression(Precedence.LOWEST)

        # Espera ')' para cerrar el grupo
        if not self._expected_token(TokenType.RPAREN):
            return None

        return expression

    def _parse_if_expression(self) -> Optional[ast.IfExpression]:
        """
        Parsea: if (<cond>) { <bloque> } [elseif (<cond>) { <bloque> }]* [else { <bloque> }]

        Soporta múltiples ramas elseif.
        """
        token = self._current_token   # Token 'if'

        if not self._expected_token(TokenType.LPAREN):
            return None

        self._advance_tokens()   # Al inicio de la condición

        condition = self._parse_expression(Precedence.LOWEST)

        if not self._expected_token(TokenType.RPAREN):
            return None

        if not self._expected_token(TokenType.LBRACE):
            return None

        consequence = self._parse_block_statement()

        # ── Manejo de ramas elseif y else ────────────────────────────────────
        alternatives = []   # Lista de (condición, bloque) para ramas elseif
        else_block = None   # Bloque final else

        # Leemos todas las ramas elseif que haya seguidas
        while self._peek_token.token_type == TokenType.ELSEIF:
            self._advance_tokens()   # Avanza al token 'elseif'

            if not self._expected_token(TokenType.LPAREN):
                return None

            self._advance_tokens()   # Al inicio de la condición del elseif

            alt_condition = self._parse_expression(Precedence.LOWEST)

            if not self._expected_token(TokenType.RPAREN):
                return None

            if not self._expected_token(TokenType.LBRACE):
                return None

            alt_block = self._parse_block_statement()
            alternatives.append((alt_condition, alt_block))

        # Si después de los elseif hay un else, lo parseamos
        if self._peek_token.token_type == TokenType.ELSE:
            self._advance_tokens()   # Avanza al token 'else'

            if not self._expected_token(TokenType.LBRACE):
                return None

            else_block = self._parse_block_statement()

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
        """
        token = self._current_token   # Token 'function'

        if not self._expected_token(TokenType.LPAREN):
            return None

        # Lista de parámetros formales
        parameters = self._parse_function_parameters()
        if parameters is None:
            return None

        if not self._expected_token(TokenType.LBRACE):
            return None

        body = self._parse_block_statement()

        return ast.FunctionLiteral(token=token, parameters=parameters, body=body)

    def _parse_function_parameters(self) -> Optional[List[ast.Identifier]]:
        """
        Parsea la lista de parámetros formales de una función: (a, b, c)

        Asume que self._current_token es '(' al entrar.
        """
        identifiers: List[ast.Identifier] = []

        # Caso: lista vacía de parámetros  function() { ... }
        if self._peek_token.token_type == TokenType.RPAREN:
            self._advance_tokens()   # Avanza al ')'
            return identifiers

        self._advance_tokens()   # Avanza al primer parámetro

        # Lee el primer parámetro
        identifiers.append(ast.Identifier(
            token=self._current_token,
            value=self._current_token.literal
        ))

        # Lee el resto de parámetros separados por ','
        while self._peek_token.token_type == TokenType.COMMA:
            self._advance_tokens()   # Avanza al ','
            self._advance_tokens()   # Avanza al identificador
            identifiers.append(ast.Identifier(
                token=self._current_token,
                value=self._current_token.literal
            ))

        # Espera ')' para cerrar la lista
        if not self._expected_token(TokenType.RPAREN):
            return None

        return identifiers

    # ─────────────────────────────────────────────────────────────────────────
    # FUNCIONES DE PARSEO INFIJAS
    # ─────────────────────────────────────────────────────────────────────────

    def _parse_infix_expression(self, left: ast.Expression) -> ast.InfixExpression:
        """
        Parsea una expresión infija: <izquierda> <operador> <derecha>

        Recibe la expresión izquierda ya parseada.
        Lee el operador actual y parsea la expresión derecha con la
        precedencia del operador actual (para manejar asociatividad).
        """
        token = self._current_token
        operator = self._current_token.literal
        precedence = self._current_precedence()

        self._advance_tokens()   # Avanza a la expresión de la derecha

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

        Recibe la expresión función (ya parseada como prefija) y parsea
        los argumentos reales entre paréntesis.

        Ejemplo: factorial(n - 1)
        """
        token = self._current_token   # Token '('
        arguments = self._parse_call_arguments()
        return ast.CallExpression(token=token, function=function, arguments=arguments)

    def _parse_call_arguments(self) -> List[ast.Expression]:
        """
        Parsea la lista de argumentos de una llamada: (arg1, arg2, ...)

        Asume que self._current_token es '(' al entrar.
        """
        arguments: List[ast.Expression] = []

        # Caso: llamada sin argumentos  f()
        if self._peek_token.token_type == TokenType.RPAREN:
            self._advance_tokens()
            return arguments

        self._advance_tokens()   # Avanza al primer argumento

        # Parsea el primer argumento
        arg = self._parse_expression(Precedence.LOWEST)
        if arg:
            arguments.append(arg)

        # Parsea el resto de argumentos separados por ','
        while self._peek_token.token_type == TokenType.COMMA:
            self._advance_tokens()   # Avanza al ','
            self._advance_tokens()   # Avanza al argumento
            arg = self._parse_expression(Precedence.LOWEST)
            if arg:
                arguments.append(arg)

        # Espera ')' para cerrar los argumentos
        if not self._expected_token(TokenType.RPAREN):
            return []

        return arguments

    def _parse_break_statement(self) -> ast.BreakStatement:
        """
        Parsea: break;

        Sentencia que sale inmediatamente del bucle más cercano (while o for).
        """
        token = self._current_token   # Token 'break'
        # Consume el punto y coma si existe
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()
        return ast.BreakStatement(token=token)

    def _parse_continue_statement(self) -> ast.ContinueStatement:
        """
        Parsea: continue;

        Sentencia que salta el resto del cuerpo del bucle y va a la siguiente
        iteración (evaluando la condición y el update en el caso del for).
        """
        token = self._current_token   # Token 'continue'
        if self._peek_token.token_type == TokenType.SEMICOLON:
            self._advance_tokens()
        return ast.ContinueStatement(token=token)

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODOS AUXILIARES
    # ─────────────────────────────────────────────────────────────────────────

    def _advance_tokens(self) -> None:
        """
        Avanza el cursor de tokens.

        current ← peek
        peek    ← siguiente token del lexer
        """
        self._current_token = self._peek_token
        self._peek_token = self._lexer.next_token()

    def _expected_token(self, token_type: TokenType) -> bool:
        """
        Verifica que el PRÓXIMO token sea del tipo esperado y avanza.

        Si el próximo token coincide → avanza y retorna True.
        Si no coincide → registra un error y retorna False.

        Esta función es la principal fuente de errores de parseo descriptivos.
        """
        if self._peek_token.token_type == token_type:
            self._advance_tokens()
            return True

        self._errors.append(
            f'Se esperaba {token_type.name!r} pero '
            f'se encontró {self._peek_token.token_type.name!r} '
            f'(literal: {self._peek_token.literal!r})'
        )
        return False

    def _peek_precedence(self) -> Precedence:
        """Retorna la precedencia del PRÓXIMO token."""
        return PRECEDENCES.get(self._peek_token.token_type, Precedence.LOWEST)

    def _current_precedence(self) -> Precedence:
        """Retorna la precedencia del token ACTUAL."""
        return PRECEDENCES.get(self._current_token.token_type, Precedence.LOWEST)
