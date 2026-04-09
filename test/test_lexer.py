import pytest
from laurasefue.lexer import Lexer
from laurasefue.tokens import Token, TokenType
def tokenize(source:str)->list[Token]:
    lexer=Lexer(source)
    tokens=[]
    while True:
        tok=lexer.next_token()
        if tok.token_type==TokenType.EOF:
            break
        tokens.append(tok)
    return tokens
class TestOperadoresAritmeticos:
    def test_suma(self):
        tokens=tokenize("+")
        assert len(tokens) == 1
        assert tokens[0].token_type == TokenType.PLUS
        assert tokens[0].literal=="+"
    def test_expresion_aritmetica(self):
        tokens=tokenize("10 + 3 * 2 - 1")
        tipos=[t.token_type for t in tokens]
        assert tipos==[
            TokenType.INTEGER,
            TokenType.PLUS,
            TokenType.INTEGER,
            TokenType.MULTIPLY,
            TokenType.INTEGER,
            TokenType.MINUS,
            TokenType.INTEGER
        ]
