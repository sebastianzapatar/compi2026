# Importa utilidades para crear enumeraciones (tipos de tokens)
from enum import (
    auto,   # Permite asignar valores automáticamente a cada token
    Enum,   # Clase base para crear enumeraciones
    unique  # Garantiza que no haya valores repetidos en el Enum
)

# Importa tipos para estructuras de datos tipadas
from typing import (
    NamedTuple,  # Para crear estructuras inmutables tipo tupla
    Dict         # Para tipar diccionarios
)

# Decorador que asegura que todos los valores del Enum sean únicos
@unique
class TokenType(Enum):
    """
    Enum que define todos los tipos de tokens del lenguaje.
    Cada elemento representa una categoría léxica.
    """

    # Operadores y símbolos básicos
    ASSIGN = auto()       # =
    COMMA = auto()        # ,
    DIF = auto()          # != o diferencia
    EQ = auto()           # ==
    GT = auto()           # >
    GTE = auto()          # >=
    LT = auto()           # <
    LTE = auto()          # <=
    PLUS = auto()         # +
    MINUS = auto()        # -
    NEGATION = auto()     # ! (negación)
    POW = auto()           # ^ POTENCIA
    MULTIPLY = auto()
    MOD = auto()
    # Delimitadores
    LPAREN = auto()       # (
    LBRACE = auto()       # {
    RBRACE = auto()       # }
    SEMICOLON = auto()    # ;

    # Tipos de datos
    IDENTIFIER = auto()   # Variables / nombres
    INTEGER = auto()      # Números enteros
    STRING = auto()       # Cadenas de texto

    # Palabras reservadas (keywords)
    FUNCTION = auto()     # function
    LET = auto()          # let
    IF = auto()           # if
    ELSE = auto()         # else
    ELSEIF = auto()       # elseif
    FOR = auto()          # for
    WHILE = auto()        # while
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()

    # Tokens especiales
    EOF = auto()          # Fin del archivo/input
    ILLEGAL = auto()      # Token no reconocido


class Token(NamedTuple):
    """
    Representa un token individual generado por el lexer.
    
    Atributos:
    - token_type: tipo del token (TokenType)
    - literal: valor en texto del token
    """

    token_type: TokenType
    literal: str

    def __str__(self):
        """
        Representación en string del token (útil para debugging)
        """
        return f'Type {self.token_type}, Literal {self.literal}'


def lookup_token_type(literal: str) -> TokenType:
    """
    Determina si un identificador es una palabra reservada (keyword)
    o un identificador normal.

    Ejemplo:
    - "if" → TokenType.IF
    - "variable" → TokenType.IDENTIFIER
    """

    # Diccionario de palabras reservadas del lenguaje
    keywords: Dict[str, TokenType] = {
        'function': TokenType.FUNCTION,
        'for': TokenType.FOR,
        'let': TokenType.LET,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'elseif': TokenType.ELSEIF,
        'while': TokenType.WHILE,
        'return': TokenType.RETURN,
        'continue':TokenType.CONTINUE
    }

    # Si el literal está en keywords → retorna su tipo
    # Si no → se considera un IDENTIFIER
    return keywords.get(literal, TokenType.IDENTIFIER)