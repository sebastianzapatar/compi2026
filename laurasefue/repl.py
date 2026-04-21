# =============================================================================
# repl.py — REPL (Read-Eval-Print Loop)
#
# Interfaz interactiva para probar el compilador LauraSeFue.
# Permite escribir código y ver:
#   - Los tokens generados por el Lexer
#   - El AST generado por el Parser
#
# Comandos especiales:
#   salir()  → Termina el REPL
#   modo()   → Alterna entre modo 'lexer' y modo 'parser'
#   ayuda()  → Muestra los comandos disponibles
# =============================================================================

from laurasefue.lexer import Lexer
from laurasefue.parser import Parser
from laurasefue.tokens import Token, TokenType
from laurasefue.ast_visualizer import visualize

# Token constante para detectar fin de entrada
EOF_TOKEN: Token = Token(TokenType.EOF, '')

# ─── Colores ANSI para la terminal ───────────────────────────────────────────
RESET   = '\033[0m'
BOLD    = '\033[1m'
RED     = '\033[91m'
GREEN   = '\033[92m'
YELLOW  = '\033[93m'
CYAN    = '\033[96m'
MAGENTA = '\033[95m'
DIM     = '\033[2m'


def _print_banner() -> None:
    """Imprime el banner de bienvenida del REPL."""
    print(f"""
{CYAN}{BOLD}╔═══════════════════════════════════════════════════╗
║       🌿  LauraSeFue — REPL Interactivo  🌿       ║
╠═══════════════════════════════════════════════════╣
║  Escribe código para ver el AST generado.         ║
║  Comandos: salir() · modo() · ayuda()             ║
╚═══════════════════════════════════════════════════╝{RESET}
""")


def _print_help() -> None:
    """Imprime la ayuda del REPL."""
    print(f"""
{YELLOW}{BOLD}Comandos disponibles:{RESET}
  {GREEN}salir(){RESET}  → Terminar el REPL
  {GREEN}modo(){RESET}   → Alternar entre modo 'lexer' y 'parser'
  {GREEN}ayuda(){RESET}  → Mostrar esta ayuda

{YELLOW}{BOLD}Modo Lexer:{RESET}
  Muestra los tokens generados por el analizador léxico.

{YELLOW}{BOLD}Modo Parser:{RESET}
  Muestra el Árbol Sintáctico Abstracto (AST) generado.

{YELLOW}{BOLD}Ejemplos de código:{RESET}
  {DIM}let x = 5 + 3;{RESET}
  {DIM}let suma = function(a, b) {{ return a + b; }};{RESET}
  {DIM}if (x > 0) {{ print(x); }} else {{ print(0); }}{RESET}
  {DIM}while (x < 10) {{ let x = x + 1; }}{RESET}
""")


def _show_tokens(source: str) -> None:
    """Muestra los tokens generados por el Lexer para el código fuente dado."""
    lexer = Lexer(source)

    print(f"\n{CYAN}{BOLD}═══ Tokens ═══{RESET}")

    while (token := lexer.next_token()) != EOF_TOKEN:
        print(f"  {GREEN}{token.token_type.name:<12}{RESET}  →  {YELLOW}{token.literal!r}{RESET}")

    print()


def _show_ast(source: str) -> None:
    """
    Muestra el AST generado por el Parser para el código fuente dado.

    Si hay errores de parseo, los muestra en rojo.
    Si no hay errores, dibuja el árbol AST completo con caracteres Unicode.
    """
    lexer = Lexer(source)
    parser = Parser(lexer)
    program = parser.parse_program()

    # Verificar si hubo errores de parseo
    if parser.errors:
        print(f"\n{RED}{BOLD}═══ Errores de parseo ═══{RESET}")
        for error in parser.errors:
            print(f"  {RED}✗ {error}{RESET}")
        print()
        return

    # Dibujar el árbol AST completo
    print()
    tree = visualize(program)
    print(tree)
    print()


def start_repl() -> None:
    """
    Inicia el REPL (Read-Eval-Print Loop).

    Modos disponibles:
      - 'parser' (por defecto): muestra el AST generado por el parser
      - 'lexer': muestra los tokens generados por el lexer

    Soporta entrada multilínea: si se detecta '{' sin cerrar,
    continúa leyendo líneas hasta que se cierre el bloque.
    """
    _print_banner()

    # Modo inicial: parser (el más útil para probar)
    current_mode = 'parser'
    print(f"  {DIM}Modo actual: {GREEN}{BOLD}{current_mode}{RESET}\n")

    while True:
        try:
            # Prompt principal
            prompt = f"{CYAN}{BOLD}>> {RESET}"
            source = input(prompt)

        except (EOFError, KeyboardInterrupt):
            # Ctrl+D o Ctrl+C → salir limpiamente
            print(f"\n{YELLOW}¡Hasta luego! 👋{RESET}")
            break

        # Ignorar líneas vacías
        if not source.strip():
            continue

        # ── Comandos especiales ──────────────────────────────────────────
        if source.strip() == 'salir()':
            print(f"\n{YELLOW}¡Hasta luego! 👋{RESET}")
            break

        if source.strip() == 'modo()':
            current_mode = 'lexer' if current_mode == 'parser' else 'parser'
            print(f"  {DIM}Modo cambiado a: {GREEN}{BOLD}{current_mode}{RESET}\n")
            continue

        if source.strip() == 'ayuda()':
            _print_help()
            continue

        # ── Soporte multilínea ───────────────────────────────────────────
        # Si la línea tiene más '{' que '}', sigue leyendo
        open_braces = source.count('{') - source.count('}')
        while open_braces > 0:
            try:
                continuation = f"{DIM}...{RESET} "
                line = input(continuation)
                source += '\n' + line
                open_braces += line.count('{') - line.count('}')
            except (EOFError, KeyboardInterrupt):
                break

        # ── Procesar según el modo ───────────────────────────────────────
        if current_mode == 'lexer':
            _show_tokens(source)
        else:
            _show_ast(source)