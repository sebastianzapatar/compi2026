# =============================================================================
# tokens.py — Definición de todos los tipos de tokens del lenguaje
#
# Un TOKEN es la unidad mínima de significado para el lenguaje.
# Por ejemplo: una palabra clave (if), un número (42), un operador (+), etc.
# El Lexer convierte el código fuente (texto plano) en una lista de tokens.
# =============================================================================

# Importa utilidades para crear enumeraciones (tipos de tokens)
from enum import (
    auto,   # Asigna valores enteros automáticamente a cada variante del Enum
    Enum,   # Clase base para crear enumeraciones
    unique  # Garantiza que no haya dos variantes con el mismo valor
)

# Importa tipos para estructuras de datos tipadas
from typing import (
    NamedTuple,  # Para crear tuplas inmutables con nombres de campo
    Dict         # Para tipar diccionarios con clave y valor específicos
)


# El decorador @unique evita que dos tokens tengan el mismo valor numérico
@unique
class TokenType(Enum):
    """
    Enumera todos los tipos de tokens reconocidos por el lenguaje.

    Cada elemento representa una categoría léxica distinta.
    El valor de cada uno (asignado por auto()) es solo interno.
    """

    # ─── Operadores aritméticos ───────────────────────────────────────────────
    PLUS = auto()       # +  Suma
    MINUS = auto()      # -  Resta
    MULTIPLY = auto()   # *  Multiplicación
    DIVISION = auto()   # /  División
    MOD = auto()        # %  Módulo (resto de la división)
    POW = auto()        # ^  Potencia

    # ─── Operadores de comparación ────────────────────────────────────────────
    EQ = auto()         # == Igual
    DIF = auto()        # != Diferente
    LT = auto()         # <  Menor que
    LTE = auto()        # <= Menor o igual que
    GT = auto()         # >  Mayor que
    GTE = auto()        # >= Mayor o igual que

    # ─── Operadores lógicos ───────────────────────────────────────────────────
    AND = auto()        # and  Y lógico
    OR = auto()         # or   O lógico
    NEGATION = auto()   # !    Negación lógica (NOT)

    # ─── Operador de asignación ───────────────────────────────────────────────
    ASSIGN = auto()     # =  Asignar un valor a una variable

    # ─── Delimitadores y puntuación ───────────────────────────────────────────
    COMMA = auto()      # ,  Separador de argumentos / parámetros
    SEMICOLON = auto()  # ;  Fin de sentencia
    LPAREN = auto()     # (  Paréntesis izquierdo
    RPAREN = auto()     # )  Paréntesis derecho
    LBRACE = auto()     # {  Llave izquierda (inicio de bloque)
    RBRACE = auto()     # }  Llave derecha (fin de bloque)

    # ─── Tipos de datos literales ─────────────────────────────────────────────
    INTEGER = auto()    # Número entero,  e.g. 42
    FLOAT = auto()      # Número decimal, e.g. 3.14
    STRING = auto()     # Cadena de texto, e.g. "hola"
    TRUE = auto()       # Literal booleano verdadero:  true
    FALSE = auto()      # Literal booleano falso:      false

    # ─── Identificadores ─────────────────────────────────────────────────────
    IDENTIFIER = auto() # Nombre de variable o función, e.g. miVariable

    # ─── Palabras reservadas (keywords) ──────────────────────────────────────
    FUNCTION = auto()   # function — definir una función
    LET = auto()        # let      — declarar una variable
    RETURN = auto()     # return   — retornar valor desde función
    IF = auto()         # if       — condicional
    ELSEIF = auto()     # elseif   — rama condicional adicional
    ELSE = auto()       # else     — rama por defecto del condicional
    WHILE = auto()      # while    — bucle mientras condición sea verdadera
    FOR = auto()        # for      — bucle con inicialización, condición e incremento
    BREAK = auto()      # break    — salir de un bucle
    CONTINUE = auto()   # continue — saltar al siguiente ciclo del bucle
    PRINT = auto()      # print    — imprimir un valor en consola (built-in)

    # ─── Tokens especiales ───────────────────────────────────────────────────
    EOF = auto()        # Fin del archivo / del input
    ILLEGAL = auto()    # Carácter no reconocido por el lenguaje


class Token(NamedTuple):
    """
    Representa un token individual producido por el Lexer.

    Cada token tiene:
      - token_type: su categoría (TokenType)
      - literal:    el texto original del código fuente que lo generó

    Por ejemplo, para el código `let x = 5;`:
      Token(LET, 'let')
      Token(IDENTIFIER, 'x')
      Token(ASSIGN, '=')
      Token(INTEGER, '5')
      Token(SEMICOLON, ';')
    """

    token_type: TokenType   # Categoría del token
    literal: str            # Texto original del token en el código fuente

    def __str__(self) -> str:
        """Representación legible del token (útil para debug)."""
        return f'Type: {self.token_type.name:<12}  Literal: {self.literal!r}'


def lookup_token_type(literal: str) -> TokenType:
    """
    Determina si una cadena es una palabra reservada (keyword) o un identificador.

    El Lexer llama a esta función cada vez que termina de leer un identificador.
    Si el texto pertenece al lenguaje (e.g. 'if', 'while'), retorna su TokenType.
    Si no, lo trata como un nombre de variable/función → IDENTIFIER.

    Ejemplos:
      lookup_token_type('if')       → TokenType.IF
      lookup_token_type('function') → TokenType.FUNCTION
      lookup_token_type('miVar')    → TokenType.IDENTIFIER
    """

    # Tabla completa de palabras reservadas del lenguaje
    keywords: Dict[str, TokenType] = {
        'function': TokenType.FUNCTION,
        'let':      TokenType.LET,
        'return':   TokenType.RETURN,
        'if':       TokenType.IF,
        'elseif':   TokenType.ELSEIF,
        'else':     TokenType.ELSE,
        'while':    TokenType.WHILE,
        'for':      TokenType.FOR,
        'break':    TokenType.BREAK,
        'continue': TokenType.CONTINUE,
        'true':     TokenType.TRUE,
        'false':    TokenType.FALSE,
        'and':      TokenType.AND,
        'or':       TokenType.OR,
        'print':    TokenType.PRINT,
    }

    # Busca el literal en el diccionario; si no existe devuelve IDENTIFIER
    return keywords.get(literal, TokenType.IDENTIFIER)