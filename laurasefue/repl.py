# Importa la clase Lexer que se encarga de convertir texto en tokens
from laurasefue.lexer import Lexer

# Importa las estructuras de tokens
from laurasefue.tokens import (
    Token,
    TokenType
)

# Token constante que representa el fin de entrada (EOF)
# Se usa para comparar cuándo detener el procesamiento
EOF_TOKEN: Token = Token(TokenType.EOF, '')


def start_repl() -> None:
    """
    Inicia un REPL (Read-Eval-Print Loop).

    Este bucle:
    1. Lee una entrada del usuario
    2. La procesa con el lexer
    3. Imprime los tokens generados
    4. Repite hasta que el usuario escriba 'salir()'
    """

    # Bucle infinito hasta que el usuario escriba 'salir()'
    while (source := input(">>")) != 'salir()':

        # Se crea una instancia del lexer con el texto ingresado
        lexer: Lexer = Lexer(source)

        # Se obtienen tokens uno a uno hasta llegar a EOF
        while (token := lexer.next_token()) != EOF_TOKEN:
            
            # Imprime cada token generado (debug / visualización)
            print(token)