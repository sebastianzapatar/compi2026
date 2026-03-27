# =============================================================================
# tests/test_lexer.py — Pruebas del Analizador Léxico (Lexer)
#
# Verifica que el lexer convierte correctamente el código fuente en tokens.
# Cada test cubre un aspecto específico del reconocimiento léxico:
#   - operadores simples y compuestos
#   - literales (enteros, floats, strings, booleanos)
#   - palabras reservadas (keywords)
#   - identificadores
#   - comentarios de línea (--)
#   - espacios en blanco y saltos de línea
# =============================================================================

import pytest
from laurasefue.lexer import Lexer
from laurasefue.tokens import Token, TokenType


# ─── FUNCIÓN AUXILIAR ────────────────────────────────────────────────────────

def tokenize(source: str) -> list[Token]:
    """
    Convierte una cadena de código fuente en una lista de tokens.
    Excluye el token EOF del resultado para simplificar las comparaciones.
    """
    lexer = Lexer(source)
    tokens = []
    while True:
        tok = lexer.next_token()
        if tok.token_type == TokenType.EOF:
            break
        tokens.append(tok)
    return tokens


# ─── OPERADORES ARITMÉTICOS ───────────────────────────────────────────────────

class TestOperadoresAritmeticos:
    """Pruebas para los 6 operadores aritméticos del lenguaje."""

    def test_suma(self):
        """El símbolo '+' debe producir el token PLUS."""
        tokens = tokenize('+')
        assert len(tokens) == 1
        assert tokens[0].token_type == TokenType.PLUS
        assert tokens[0].literal == '+'

    def test_resta(self):
        """El símbolo '-' debe producir el token MINUS."""
        tokens = tokenize('-')
        assert tokens[0].token_type == TokenType.MINUS

    def test_multiplicacion(self):
        """El símbolo '*' debe producir el token MULTIPLY."""
        tokens = tokenize('*')
        assert tokens[0].token_type == TokenType.MULTIPLY

    def test_division(self):
        """El símbolo '/' solo debe producir el token DIVISION (no comentario)."""
        tokens = tokenize('/')
        assert tokens[0].token_type == TokenType.DIVISION

    def test_modulo(self):
        """El símbolo '%' debe producir el token MOD."""
        tokens = tokenize('%')
        assert tokens[0].token_type == TokenType.MOD

    def test_potencia(self):
        """El símbolo '^' debe producir el token POW."""
        tokens = tokenize('^')
        assert tokens[0].token_type == TokenType.POW

    def test_expresion_aritmetica_completa(self):
        """Una expresión con múltiples operadores debe tokenizarse correctamente."""
        tokens = tokenize('10 + 3 * 2 - 1')
        tipos = [t.token_type for t in tokens]
        assert tipos == [
            TokenType.INTEGER,
            TokenType.PLUS,
            TokenType.INTEGER,
            TokenType.MULTIPLY,
            TokenType.INTEGER,
            TokenType.MINUS,
            TokenType.INTEGER,
        ]


# ─── OPERADORES DE COMPARACIÓN ────────────────────────────────────────────────

class TestOperadoresComparacion:
    """Pruebas para los operadores de comparación, incluyendo los de dos caracteres."""

    def test_igual(self):
        """'==' debe producir EQ (no dos ASSIGN)."""
        tokens = tokenize('==')
        assert len(tokens) == 1
        assert tokens[0].token_type == TokenType.EQ
        assert tokens[0].literal == '=='

    def test_diferente(self):
        """'!=' debe producir DIF."""
        tokens = tokenize('!=')
        assert len(tokens) == 1
        assert tokens[0].token_type == TokenType.DIF
        assert tokens[0].literal == '!='

    def test_menor(self):
        """'<' solo debe producir LT."""
        tokens = tokenize('<')
        assert tokens[0].token_type == TokenType.LT

    def test_menor_igual(self):
        """'<=' debe producir LTE (no LT + ASSIGN)."""
        tokens = tokenize('<=')
        assert len(tokens) == 1
        assert tokens[0].token_type == TokenType.LTE
        assert tokens[0].literal == '<='

    def test_mayor(self):
        """'>' solo debe producir GT."""
        tokens = tokenize('>')
        assert tokens[0].token_type == TokenType.GT

    def test_mayor_igual(self):
        """'>=' debe producir GTE."""
        tokens = tokenize('>=')
        assert len(tokens) == 1
        assert tokens[0].token_type == TokenType.GTE
        assert tokens[0].literal == '>='

    def test_asignacion_no_igual(self):
        """'=' seguido de un espacio y otro carácter debe ser solo ASSIGN."""
        tokens = tokenize('= 5')
        assert tokens[0].token_type == TokenType.ASSIGN
        assert tokens[0].literal == '='


# ─── LITERALES ────────────────────────────────────────────────────────────────

class TestLiterales:
    """Pruebas para todos los tipos de literales del lenguaje."""

    def test_entero(self):
        """Un número entero debe producir el token INTEGER con su literal."""
        tokens = tokenize('42')
        assert tokens[0].token_type == TokenType.INTEGER
        assert tokens[0].literal == '42'

    def test_entero_cero(self):
        """El número 0 también es un entero válido."""
        tokens = tokenize('0')
        assert tokens[0].token_type == TokenType.INTEGER
        assert tokens[0].literal == '0'

    def test_entero_largo(self):
        """Números con múltiples dígitos deben capturarse completos."""
        tokens = tokenize('3628800')
        assert tokens[0].token_type == TokenType.INTEGER
        assert tokens[0].literal == '3628800'

    def test_flotante(self):
        """Un número con punto decimal debe producir el token FLOAT."""
        tokens = tokenize('3.14')
        assert tokens[0].token_type == TokenType.FLOAT
        assert tokens[0].literal == '3.14'

    def test_flotante_compuesto(self):
        """Un flotante en una expresión debe separarse correctamente del operador."""
        tokens = tokenize('2.5 + 1.0')
        assert tokens[0].token_type == TokenType.FLOAT
        assert tokens[0].literal == '2.5'
        assert tokens[1].token_type == TokenType.PLUS
        assert tokens[2].token_type == TokenType.FLOAT
        assert tokens[2].literal == '1.0'

    def test_string_simple(self):
        """Un string entre comillas debe producir STRING con el contenido sin comillas."""
        tokens = tokenize('"hola"')
        assert len(tokens) == 1
        assert tokens[0].token_type == TokenType.STRING
        assert tokens[0].literal == 'hola'

    def test_string_con_espacios(self):
        """Los espacios dentro de un string deben preservarse."""
        tokens = tokenize('"hola mundo"')
        assert tokens[0].token_type == TokenType.STRING
        assert tokens[0].literal == 'hola mundo'

    def test_string_vacio(self):
        """Un string vacío "" debe producir STRING con literal ''."""
        tokens = tokenize('""')
        assert tokens[0].token_type == TokenType.STRING
        assert tokens[0].literal == ''

    def test_booleano_true(self):
        """La palabra 'true' debe reconocerse como el token TRUE."""
        tokens = tokenize('true')
        assert tokens[0].token_type == TokenType.TRUE
        assert tokens[0].literal == 'true'

    def test_booleano_false(self):
        """La palabra 'false' debe reconocerse como el token FALSE."""
        tokens = tokenize('false')
        assert tokens[0].token_type == TokenType.FALSE
        assert tokens[0].literal == 'false'


# ─── PALABRAS RESERVADAS (KEYWORDS) ──────────────────────────────────────────

class TestKeywords:
    """Pruebas para todas las palabras reservadas del lenguaje."""

    # Tabla de (código_fuente, TokenType_esperado)
    @pytest.mark.parametrize('source, expected_type', [
        ('let',      TokenType.LET),
        ('function', TokenType.FUNCTION),
        ('return',   TokenType.RETURN),
        ('if',       TokenType.IF),
        ('elseif',   TokenType.ELSEIF),
        ('else',     TokenType.ELSE),
        ('while',    TokenType.WHILE),
        ('for',      TokenType.FOR),
        ('break',    TokenType.BREAK),
        ('continue', TokenType.CONTINUE),
        ('print',    TokenType.PRINT),
        ('true',     TokenType.TRUE),
        ('false',    TokenType.FALSE),
        ('and',      TokenType.AND),
        ('or',       TokenType.OR),
    ])
    def test_keyword(self, source, expected_type):
        """Cada palabra reservada debe mapearse a su TokenType correcto."""
        tokens = tokenize(source)
        assert len(tokens) == 1
        assert tokens[0].token_type == expected_type
        assert tokens[0].literal == source


# ─── IDENTIFICADORES ─────────────────────────────────────────────────────────

class TestIdentificadores:
    """Pruebas para el reconocimiento de nombres de variables y funciones."""

    def test_identificador_simple(self):
        """Un nombre de una sola letra debe ser IDENTIFIER."""
        tokens = tokenize('x')
        assert tokens[0].token_type == TokenType.IDENTIFIER
        assert tokens[0].literal == 'x'

    def test_identificador_largo(self):
        """Un nombre compuesto de letras debe capturarse completo."""
        tokens = tokenize('miVariable')
        assert tokens[0].token_type == TokenType.IDENTIFIER
        assert tokens[0].literal == 'miVariable'

    def test_identificador_con_guion_bajo(self):
        """Los guiones bajos son válidos en identificadores."""
        tokens = tokenize('mi_var')
        assert tokens[0].token_type == TokenType.IDENTIFIER
        assert tokens[0].literal == 'mi_var'

    def test_identificador_con_numero(self):
        """Un identificador puede contener números (pero no empezar con uno)."""
        tokens = tokenize('var1')
        assert tokens[0].token_type == TokenType.IDENTIFIER
        assert tokens[0].literal == 'var1'

    def test_no_confundir_keyword_con_identificador_prefijo(self):
        """'letting' no debe reconocerse como keyword 'let'; es un IDENTIFIER."""
        tokens = tokenize('letting')
        assert tokens[0].token_type == TokenType.IDENTIFIER
        assert tokens[0].literal == 'letting'


# ─── DELIMITADORES ────────────────────────────────────────────────────────────

class TestDelimitadores:
    """Pruebas para paréntesis, llaves, coma y punto y coma."""

    @pytest.mark.parametrize('char, expected', [
        ('(', TokenType.LPAREN),
        (')', TokenType.RPAREN),
        ('{', TokenType.LBRACE),
        ('}', TokenType.RBRACE),
        (',', TokenType.COMMA),
        (';', TokenType.SEMICOLON),
    ])
    def test_delimitador(self, char, expected):
        tokens = tokenize(char)
        assert tokens[0].token_type == expected


# ─── COMENTARIOS ─────────────────────────────────────────────────────────────

class TestComentarios:
    """Pruebas para los comentarios de línea (//)."""

    def test_comentario_solo(self):
        """Una línea de solo comentario no debe producir ningún token."""
        tokens = tokenize('// esto es un comentario')
        assert len(tokens) == 0

    def test_comentario_al_final_de_linea(self):
        """El comentario al final de una línea no debe afectar los tokens previos."""
        tokens = tokenize('let x = 5; // comentario')
        tipos = [t.token_type for t in tokens]
        assert tipos == [
            TokenType.LET,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.INTEGER,
            TokenType.SEMICOLON,
        ]

    def test_codigo_despues_del_comentario(self):
        """El código en la siguiente línea tras un comentario debe tokenizarse."""
        source = '// linea de comentario\nlet x = 1;'
        tokens = tokenize(source)
        assert tokens[0].token_type == TokenType.LET

    def test_barra_sola_no_es_comentario(self):
        """'/' sola debe ser DIVISION, no inicio de comentario."""
        tokens = tokenize('10 / 2')
        assert tokens[1].token_type == TokenType.DIVISION


# ─── SECUENCIAS COMPUESTAS ────────────────────────────────────────────────────

class TestSecuenciasCompuestas:
    """Pruebas de tokenización de fragmentos de código reales (integración léxica)."""

    def test_declaracion_let(self):
        """'let x = 42;' debe producir la secuencia exacta de tokens."""
        tokens = tokenize('let x = 42;')
        assert [t.token_type for t in tokens] == [
            TokenType.LET,
            TokenType.IDENTIFIER,
            TokenType.ASSIGN,
            TokenType.INTEGER,
            TokenType.SEMICOLON,
        ]
        assert tokens[1].literal == 'x'
        assert tokens[3].literal == '42'

    def test_llamada_a_funcion(self):
        """'f(x, y)' debe tokenizarse como IDENT LPAREN IDENT COMMA IDENT RPAREN."""
        tokens = tokenize('f(x, y)')
        tipos = [t.token_type for t in tokens]
        assert tipos == [
            TokenType.IDENTIFIER,  # f
            TokenType.LPAREN,      # (
            TokenType.IDENTIFIER,  # x
            TokenType.COMMA,       # ,
            TokenType.IDENTIFIER,  # y
            TokenType.RPAREN,      # )
        ]

    def test_multilinea(self):
        """Los saltos de línea deben omitirse como espacios en blanco."""
        source = 'let\nx\n=\n5'
        tokens = tokenize(source)
        tipos = [t.token_type for t in tokens]
        assert tipos == [TokenType.LET, TokenType.IDENTIFIER,
                         TokenType.ASSIGN, TokenType.INTEGER]

    def test_negacion_vs_diferente(self):
        """'!' solo debe ser NEGATION; '!=' debe ser DIF."""
        tokens = tokenize('! !=')
        assert tokens[0].token_type == TokenType.NEGATION
        assert tokens[1].token_type == TokenType.DIF
