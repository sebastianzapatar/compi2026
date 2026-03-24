from re import match
from laurasefue.tokens import(
    Token,
    TokenType,
    lookup_token_type
)
class Lexer:
    def __init__(self,source:str):
        self._source:str=source
        self._character:str=''
        self._position:int=0
        self._read_position:int=0
        self._read_character()
    def next_token(self)->Token:
        if match(r'^$',self._character):
            token=Token(TokenType.EOF,self._character)
        elif self._character=='+':
            token=Token(TokenType.PLUS,self._character)
        elif match(r'^>$',self._character):
            token=Token(TokenType.GT,self._character)
        else:
            print(self._character)
            token=Token(TokenType.ILLEGAL,self._character)
        self._read_character()
        return token

    def _read_character(self)->None:
        if self._read_position>=len(self._source):
            self._character=''
        else:
            self._character=self._source[self._read_position]
        self._position=self._read_position
        self._read_position+=1