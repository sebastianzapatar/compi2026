from laurasefue.tokens import (
    Token,
    TokenType,
    lookup_token_type  # Aún no se usa, pero puede servir después para keywords
)


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

            # Cualquier otro carácter no reconocido se marca como ilegal
            case _:
                print(self._character)  # Útil para depuración
                token = Token(TokenType.ILLEGAL, self._character)

        # Después de reconocer el token, avanza al siguiente carácter
        self._read_character()

        # Retorna el token encontrado
        return token

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