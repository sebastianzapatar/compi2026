# =============================================================================
# main.py — Punto de entrada del intérprete
#
# Uso:
#   python main.py <archivo.lf>
#
# El intérprete:
#   1. Lee el archivo fuente (.lf) pasado como argumento.
#   2. Crea un Lexer que convierte el texto en tokens.
#   3. Crea un Parser que construye el AST a partir de los tokens.
#   4. Si hay errores de parseo, los muestra y termina.
#   5. Crea un entorno global y evalúa el AST.
#   6. Si hay errores de ejecución, los muestra.
# =============================================================================

import sys                                    # Para leer argumentos de línea de comandos

# El intérprete es tree-walking: cada llamada a función del lenguaje consume
# varios frames de Python. Subimos el límite para soportar recursión profunda.
sys.setrecursionlimit(50_000)
from laurasefue.lexer import Lexer            # Analizador léxico
from laurasefue.parser import Parser          # Analizador sintáctico
from laurasefue.evaluator import evaluate     # Evaluador del AST
from laurasefue.object_system import (        # Sistema de objetos en tiempo de ejecución
    Environment,
    ObjectType
)


def run_file(filepath: str) -> None:
    """
    Lee y ejecuta un archivo de código fuente del lenguaje.

    Parámetros:
      filepath: ruta al archivo .lf a interpretar

    Proceso:
      1. Abre y lee el archivo completo.
      2. Ejecuta el pipeline: Lexer → Parser → Evaluador.
      3. Muestra errores de parseo o de ejecución si los hay.
    """
    # ── Paso 1: Leer el archivo ──────────────────────────────────────────────
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        print(f'[Error] No se encontró el archivo: "{filepath}"')
        sys.exit(1)
    except IOError as e:
        print(f'[Error] No se pudo leer el archivo: {e}')
        sys.exit(1)

    # ── Paso 2: Análisis Léxico (Lexer) ──────────────────────────────────────
    # El Lexer convierte el string del código fuente en una secuencia de tokens.
    lexer = Lexer(source)

    # ── Paso 3: Análisis Sintáctico (Parser) ─────────────────────────────────
    # El Parser construye el AST a partir de los tokens.
    parser = Parser(lexer)
    program = parser.parse_program()

    # Si el parser encontró errores de sintaxis, los mostramos y paramos.
    if parser.errors:
        print('═' * 50)
        print('  Errores de sintaxis encontrados:')
        print('═' * 50)
        for error in parser.errors:
            print(f'  → {error}')
        print('═' * 50)
        sys.exit(1)

    # ── Paso 4: Evaluación ───────────────────────────────────────────────────
    # El Evaluador recorre el AST y ejecuta el programa.
    env = Environment()            # Entorno global vacío (sin variables aún)
    result = evaluate(program, env)

    # Si el resultado final es un error, lo mostramos.
    if result is not None and result.object_type() == ObjectType.ERROR:
        print('═' * 50)
        print('  Error de ejecución:')
        print('═' * 50)
        print(f'  → {result.inspect()}')
        print('═' * 50)
        sys.exit(1)


def main() -> None:
    """
    Función principal del intérprete.

    Verifica que se haya pasado exactamente un argumento (el archivo .lf)
    y lanza la ejecución.
    """
    # Verifica que el usuario haya pasado el nombre del archivo
    if len(sys.argv) != 2:
        print('Uso: python3 main.py <archivo.lf>')
        print('Ejemplo: python3 main.py mi_programa.lf')
        sys.exit(1)

    filepath = sys.argv[1]   # El primer argumento es la ruta al archivo

    # Capturamos RecursionError para dar un mensaje más amigable al usuario
    try:
        run_file(filepath)
    except RecursionError:
        print('═' * 50)
        print('  Error: recursión demasiado profunda.')
        print('  Verifica que tus funciones recursivas tengan')
        print('  un caso base correcto, o reduce la profundidad.')
        print('═' * 50)
        sys.exit(1)


if __name__ == '__main__':
    main()