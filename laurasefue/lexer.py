from laurasefue.tokens import (
    Token,
    TokenType,
    lookup_token_type  # Aún no se usa, pero puede servir después para keywords
)
from re import match

class Lexer:
    def __init__(self, source: str):
        # Código fuente completo que va a analizar el lexer
        self._source: str = source

        # Carácter actual que se está leyendo
        self._character: str = ''

        # Posición actual dentro del string
        self._position: int = 0

        # Posición del siguiente carácter a leer
        self._read_position: int = 0

        # Lee el primer carácter apenas se crea el lexer
        self._read_character()

    def next_token(self) -> Token:
        """
        Retorna el siguiente token encontrado en el input.

        Usa match-case para hacer el código más limpio y más fácil de
        mantener cuando se agreguen más símbolos.
        """
        self._skip_white_spaces()
        match self._character:
            # Si el carácter actual es vacío, significa fin del input
            case '':
                token = Token(TokenType.EOF, '')

            # Si encuentra un signo +
            case '+':
                token = Token(TokenType.PLUS, self._character)

            # Si encuentra un signo >
            case '>':
                token = Token(TokenType.GT, self._character)
            case '-':
                token=Token(TokenType.MINUS,self._character)
            case '^':
                token=Token(TokenType.POW,self._character)
            case '*':
                token=Token(TokenType.MULTIPLY,self._character)
            case '%':
                token=Token(TokenType.MOD,self._character)
            case '!':
                if self._peek_token()=="=":
                    token=self._make_two_character_token(TokenType.DIF)
                else:
                    token=Token(TokenType.NEGATION,self._character)
            case '=':
                if self._peek_token()=="=":
                    token=self._make_two_character_token(TokenType.EQ)
                else:    
                    token=Token(TokenType.ASSIGN,self._character)
            #Es letra
            case _ if self._character.isalpha():
                literal=self._read_identifier()
                tokenType=lookup_token_type(literal)
                token=Token(tokenType,literal)
            #Es digito
            case _ if self._character.isdigit():
                literal=self._read_number()
                token=Token(TokenType.INTEGER,literal)
            # Cualquier otro carácter no reconocido se marca como ilegal
            case _:
                print(self._character)  # Útil para depuración
                token = Token(TokenType.ILLEGAL, self._character)

        # Después de reconocer el token, avanza al siguiente carácter
        self._read_character()

        # Retorna el token encontrado
        return token
    def _skip_white_spaces(self)->None:
        while match(r'^\s$',self._character):
            self._read_character()
    def _read_character(self) -> None:
        """
        Lee el siguiente carácter del input y actualiza
        el estado interno del lexer.
        """

        # Si la posición de lectura ya se salió del tamaño del string,
        # significa que llegamos al final del archivo/input
        if self._read_position >= len(self._source):
            self._character = ''
        else:
            # Toma el carácter actual desde el código fuente
            self._character = self._source[self._read_position]

        # Actualiza la posición actual
        self._position = self._read_position

        # Avanza la posición de lectura al siguiente carácter
        self._read_position += 1
    def _read_number(self):
        start=self._position
        while self._character.isdigit():
            self._read_character()
        return self._source[start:self._position]
    def _read_identifier(self):
        start=self._position
        while self._character.isalpha():
            self._read_character()
        return self._source[start:self._position]
    def _peek_token(self)->str:
        if self._read_position>=len(self._source):
            return ''
        return self._source[self._read_position]
    def _make_two_character_token(self,token_type:TokenType)->Token:
        prefix=self._character
        self._read_character()
        suffix=self._character
        return Token(token_type,f'{prefix}{suffix}')