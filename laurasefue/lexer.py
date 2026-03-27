# =============================================================================
# lexer.py — Analizador Léxico (Lexer / Scanner)
#
# El Lexer es la primera etapa del intérprete. Su trabajo es leer el código
# fuente carácter a carácter y agruparlos en TOKENS significativos.
#
# Ejemplo de transformación:
#   Código fuente: let x = 10 + 5;
#   Tokens:  [LET 'let'] [IDENT 'x'] [ASSIGN '='] [INT '10']
#            [PLUS '+'] [INT '5'] [SEMICOLON ';'] [EOF '']
# =============================================================================

from laurasefue.tokens import (
    Token,
    TokenType,
    lookup_token_type   # Función que distingue keywords de identificadores
)
from re import match    # Expresiones regulares para detectar espacios en blanco


class Lexer:
    """
    Convierte una cadena de código fuente en una secuencia de tokens.

    Uso típico:
        lexer = Lexer(source_code)
        while (tok := lexer.next_token()).token_type != TokenType.EOF:
            print(tok)
    """

    def __init__(self, source: str) -> None:
        # Código fuente completo (string) que el lexer va a procesar
        self._source: str = source

        # El carácter actual que se está evaluando
        self._character: str = ''

        # Índice del carácter actual en self._source
        self._position: int = 0

        # Índice del PRÓXIMO carácter a leer (siempre un paso adelante)
        self._read_position: int = 0

        # Lee el primer carácter para inicializar el estado del lexer
        self._read_character()

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODO PRINCIPAL
    # ─────────────────────────────────────────────────────────────────────────

    def next_token(self) -> Token:
        """
        Lee el siguiente token del código fuente y lo retorna.

        Proceso:
          1. Salta espacios en blanco y comentarios.
          2. Analiza el carácter actual con match-case.
          3. Para tokens de dos caracteres (==, !=, <=, >=), usa _peek_character().
          4. Para identificadores y números, usa _read_identifier() / _read_number().
          5. Avanza al siguiente carácter antes de retornar.

        Retorna un Token con su tipo y literal correspondiente.
        """
        # Omite espacios, tabs, saltos de línea y comentarios de línea (//)
        self._skip_whitespace_and_comments()

        token: Token

        match self._character:

            # ── Fin de archivo ───────────────────────────────────────────────
            case '':
                token = Token(TokenType.EOF, '')

            # ── Operadores aritméticos ────────────────────────────────────────
            case '+':
                token = Token(TokenType.PLUS, self._character)

            case '-':
                token = Token(TokenType.MINUS, self._character)

            case '*':
                token = Token(TokenType.MULTIPLY, self._character)

            case '/':
                # '/' sola = división; '//' = comentario (ya filtrado antes)
                token = Token(TokenType.DIVISION, self._character)

            case '%':
                token = Token(TokenType.MOD, self._character)

            case '^':
                token = Token(TokenType.POW, self._character)

            # ── Comparación: = y == ───────────────────────────────────────────
            case '=':
                if self._peek_character() == '=':
                    # El siguiente carácter también es '=', entonces es '=='
                    token = self._make_two_character_token(TokenType.EQ)
                else:
                    token = Token(TokenType.ASSIGN, self._character)

            # ── Negación / distinto: ! y != ───────────────────────────────────
            case '!':
                if self._peek_character() == '=':
                    token = self._make_two_character_token(TokenType.DIF)
                else:
                    token = Token(TokenType.NEGATION, self._character)

            # ── Comparación: < y <= ───────────────────────────────────────────
            case '<':
                if self._peek_character() == '=':
                    token = self._make_two_character_token(TokenType.LTE)
                else:
                    token = Token(TokenType.LT, self._character)

            # ── Comparación: > y >= ───────────────────────────────────────────
            case '>':
                if self._peek_character() == '=':
                    token = self._make_two_character_token(TokenType.GTE)
                else:
                    token = Token(TokenType.GT, self._character)

            # ── Delimitadores ─────────────────────────────────────────────────
            case ',':
                token = Token(TokenType.COMMA, self._character)

            case ';':
                token = Token(TokenType.SEMICOLON, self._character)

            case '(':
                token = Token(TokenType.LPAREN, self._character)

            case ')':
                token = Token(TokenType.RPAREN, self._character)

            case '{':
                token = Token(TokenType.LBRACE, self._character)

            case '}':
                token = Token(TokenType.RBRACE, self._character)

            # ── Cadena de texto (string literal) ─────────────────────────────
            case '"':
                # Lee todo el contenido entre comillas dobles
                str_content = self._read_string()
                # Retorno anticipado: _read_string ya avanzó más allá del cierre
                return Token(TokenType.STRING, str_content)

            # ── Identificadores y palabras reservadas ─────────────────────────
            case _ if self._is_letter(self._character):
                # Lee todos los caracteres alfanuméricos/guion_bajo contiguos
                literal = self._read_identifier()
                # lookup_token_type decide si es keyword o nombre de usuario
                token_type = lookup_token_type(literal)
                # Retorno anticipado: _read_identifier ya avanzó la posición
                return Token(token_type, literal)

            # ── Literales numéricos (entero o flotante) ───────────────────────
            case _ if self._character.isdigit():
                # Lee el número completo (puede contener un punto decimal)
                literal, token_type = self._read_number()
                # Retorno anticipado: _read_number ya avanzó la posición
                return Token(token_type, literal)

            # ── Carácter no reconocido ────────────────────────────────────────
            case _:
                token = Token(TokenType.ILLEGAL, self._character)

        # Avanza al siguiente carácter del código fuente
        self._read_character()
        return token

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODOS AUXILIARES PRIVADOS
    # ─────────────────────────────────────────────────────────────────────────

    def _read_character(self) -> None:
        """
        Avanza un carácter en el código fuente.

        - Actualiza self._character con el siguiente carácter.
        - Si ya llegamos al final, self._character queda como '' (EOF).
        - self._position apunta al carácter actual.
        - self._read_position apunta al SIGUIENTE carácter (look-ahead de 1).
        """
        if self._read_position >= len(self._source):
            self._character = ''   # Señal de fin de archivo
        else:
            self._character = self._source[self._read_position]

        self._position = self._read_position
        self._read_position += 1

    def _peek_character(self) -> str:
        """
        Devuelve el siguiente carácter SIN avanzar la posición.

        Útil para tokens de dos caracteres como '==', '!=', '<=', '>='.
        """
        if self._read_position >= len(self._source):
            return ''
        return self._source[self._read_position]

    def _make_two_character_token(self, token_type: TokenType) -> Token:
        """
        Crea un token a partir de los DOS caracteres actuales: self._character
        y el siguiente carácter.

        Ejemplo: cuando estamos en '=' y el siguiente es '=', produce '=='.
        """
        prefix = self._character         # primer carácter (ya leído)
        self._read_character()           # avanza al segundo
        suffix = self._character         # segundo carácter
        return Token(token_type, f'{prefix}{suffix}')

    def _skip_whitespace_and_comments(self) -> None:
        """
        Salta espacios en blanco (espacio, tab, \\n, \\r) y comentarios de línea.

        Un comentario de línea empieza con '//' y se extiende hasta el final
        de la línea. Por ejemplo:
            let x = 5; // esto es un comentario
        Todo el texto tras '//' es ignorado.
        """
        while True:
            # Salta cualquier carácter de espacio en blanco
            if match(r'^\s$', self._character):
                self._read_character()

            # Si encuentra '//' inicia un comentario: salta hasta fin de línea
            elif self._character == '/' and self._peek_character() == '/':
                while self._character != '\n' and self._character != '':
                    self._read_character()

            else:
                break   # No es espacio ni comentario: salir del bucle

    def _is_letter(self, ch: str) -> bool:
        """
        Determina si un carácter puede ser parte de un identificador.

        Los identificadores pueden contener:
          - Letras (a-z, A-Z)
          - Guion bajo (_)  → e.g. mi_variable
        No pueden empezar con dígito (eso se maneja por separado).
        """
        return ch.isalpha() or ch == '_'

    def _read_identifier(self) -> str:
        """
        Lee una secuencia de letras/guiones_bajos y retorna el string completo.

        Ejemplo: para 'miVariable' retorna 'miVariable'.
        Deja self._character apuntando al primer carácter que NO es parte
        del identificador (para que next_token() lo procese).
        """
        start = self._position
        # Avanza mientras el carácter sea letra, dígito o guion bajo
        while self._is_letter(self._character) or self._character.isdigit():
            self._read_character()
        return self._source[start:self._position]

    def _read_number(self) -> tuple[str, TokenType]:
        """
        Lee un número entero o decimal (flotante).

        Puede contener un punto decimal, e.g. 3.14.
        Retorna una tupla (literal_string, TokenType.INTEGER | TokenType.FLOAT).
        """
        start = self._position
        token_type = TokenType.INTEGER

        # Lee la parte entera
        while self._character.isdigit():
            self._read_character()

        # Si hay un punto seguido de dígitos → es un número flotante
        if self._character == '.' and self._peek_character().isdigit():
            token_type = TokenType.FLOAT
            self._read_character()   # consume el '.'
            while self._character.isdigit():
                self._read_character()

        literal = self._source[start:self._position]
        return literal, token_type

    def _read_string(self) -> str:
        """
        Lee el contenido de un string delimitado por comillas dobles.

        Asume que self._character es actualmente '"' (la comilla de apertura).
        Avanza hasta encontrar la comilla de cierre o EOF.
        Retorna solo el contenido como str (sin las comillas).

        Ejemplo: para el código "hola mundo" retorna 'hola mundo'
        """
        self._read_character()          # Salta la comilla de apertura '"'
        start = self._position

        # Avanza hasta encontrar la comilla de cierre
        while self._character != '"' and self._character != '':
            self._read_character()

        # Extrae el contenido entre las comillas
        literal = self._source[start:self._position]

        self._read_character()          # Salta la comilla de cierre '"'

        return literal