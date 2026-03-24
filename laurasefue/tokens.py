from enum import (
    auto,
    Enum,
    unique
)
from typing import(
    NamedTuple,
    Dict
)
@unique
class TokenType(Enum):
    ASSIGN=auto()
    COMMA=auto()
    DIF=auto()
    ELSE=auto()
    ELSEIF=auto()
    EOF=auto()
    EQ=auto()
    FOR=auto()
    FUNCTION=auto()
    IDENTIFIER=auto()
    IF=auto()
    GT=auto()
    GTE=auto()
    ILLEGAL=auto()
    INTEGER=auto()
    LBRACE=auto()
    LET=auto()
    LPAREN=auto()
    LT=auto()
    LTE=auto()
    MINUS=auto()
    NEGATION=auto()
    PLUS=auto()
    RBRACE=auto()
    SEMICOLON=auto()
    STRING=auto()
    WHILE=auto()

class Token(NamedTuple):
    token_type:TokenType
    literal:str
    def __str__(self):
        return f'Type {self.token_type}, Literal {self.literal}'
def lookup_token_type(literal:str)->TokenType:
    keywords:Dict[str,TokenType]={
        'function':TokenType.FUNCTION,
        'for':TokenType.FOR,
        'let':TokenType.LET,
        'if':TokenType.IF,
        'else':TokenType.ELSE,
        'elseif':TokenType.ELSEIF,
        'while':TokenType.WHILE
    }
    return keywords.get(literal,TokenType.IDENTIFIER)

