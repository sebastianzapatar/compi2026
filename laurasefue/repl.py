# =============================================================================
# repl.py — REPL (Read-Eval-Print Loop)
#
# Interfaz interactiva para probar el compilador LauraSeFue.
# Permite escribir código y ver:
#   - Los tokens generados por el Lexer        (modo: lexer)
#   - El AST generado por el Parser            (modo: parser)
#   - El resultado de evaluación               (modo: eval)   ← NUEVO
#
# Comandos especiales:
#   salir()  → Termina el REPL
#   modo()   → Cicla entre modos: parser → eval → lexer → parser
#   ayuda()  → Muestra los comandos disponibles
# =============================================================================

from laurasefue.lexer import Lexer
from laurasefue.parser import Parser
from laurasefue.tokens import Token, TokenType
from laurasefue.ast_visualizer import visualize
from laurasefue.evaluator import evaluate
from laurasefue.environment import Environment
from laurasefue.object_system import ObjectType, NULL

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

# Orden de ciclo de modos
_MODES = ['eval', 'parser', 'lexer']


def _print_banner() -> None:
    """Imprime el banner de bienvenida del REPL."""
    print(f"""
{CYAN}{BOLD}╔═══════════════════════════════════════════════════╗
║       🌿  LauraSeFue — REPL Interactivo  🌿       ║
╠═══════════════════════════════════════════════════╣
║  Escribe código para probar el intérprete.        ║
║  Comandos: salir() · modo() · ayuda()             ║
╚═══════════════════════════════════════════════════╝{RESET}
""")


def _print_help() -> None:
    """Imprime la ayuda del REPL."""
    print(f"""
{YELLOW}{BOLD}Comandos disponibles:{RESET}
  {GREEN}salir(){RESET}  → Terminar el REPL
  {GREEN}modo(){RESET}   → Ciclar entre modos (eval → parser → lexer → eval)
  {GREEN}ayuda(){RESET}  → Mostrar esta ayuda

{YELLOW}{BOLD}Modo Eval (por defecto):{RESET}
  Evalúa el código y muestra el resultado. ¡El intérprete completo!

{YELLOW}{BOLD}Modo Parser:{RESET}
  Muestra el Árbol Sintáctico Abstracto (AST) generado.

{YELLOW}{BOLD}Modo Lexer:{RESET}
  Muestra los tokens generados por el analizador léxico.

{YELLOW}{BOLD}Ejemplos de código:{RESET}
  {DIM}let x = 10 + 5;{RESET}
  {DIM}print(x * 2);{RESET}
  {DIM}let potencia = 2 ^ 8; print(potencia);{RESET}
  {DIM}let modulo = 17 % 5; print(modulo);{RESET}
  {DIM}print(3 > 2 and 5 != 6);{RESET}
  {DIM}let fact = function(n) {{ if (n <= 1) {{ return 1; }} return n * fact(n - 1); }};{RESET}
  {DIM}print(fact(10));{RESET}
  {DIM}for (let i = 0; i < 5; let i = i + 1) {{ print(i); }}{RESET}
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


def _eval_source(source: str, env: Environment) -> None:
    """
    Evalúa el código fuente dado y muestra el resultado.

    1. Lexer → tokens
    2. Parser → AST  (si hay errores de parseo, los muestra)
    3. Evaluator → Object  (si hay errores de ejecución, los muestra en rojo)
    4. Si el resultado no es NULL, lo imprime en verde.

    El entorno `env` se reutiliza entre llamadas para que las variables
    declaradas persistan durante la sesión del REPL.
    """
    lexer = Lexer(source)
    parser = Parser(lexer)
    program = parser.parse_program()

    # ── Errores de parseo ──────────────────────────────────────────────────
    if parser.errors:
        print(f"\n{RED}{BOLD}═══ Errores de parseo ═══{RESET}")
        for error in parser.errors:
            print(f"  {RED}✗ {error}{RESET}")
        print()
        return

    # ── Evaluación ─────────────────────────────────────────────────────────
    result = evaluate(program, env)

    if result is None:
        return

    # ── Mostrar errores de ejecución ───────────────────────────────────────
    if result.type == ObjectType.ERROR:
        print(f"\n  {RED}{BOLD}✗ {result.inspect()}{RESET}\n")
        return

    # ── Mostrar resultado (solo si no es null) ─────────────────────────────
    if result is not NULL and result.type != ObjectType.NULL:
        print(f"  {GREEN}▶ {result.inspect()}{RESET}")


def start_repl() -> None:
    """
    Inicia el REPL (Read-Eval-Print Loop).

    Modos disponibles (ciclados con modo()):
      - 'eval'   (por defecto): evalúa el código y muestra el resultado
      - 'parser': muestra el AST generado por el parser
      - 'lexer':  muestra los tokens generados por el lexer

    El entorno global persiste durante toda la sesión: las variables
    declaradas con `let` están disponibles en entradas posteriores.

    Soporta entrada multilínea: si se detecta '{' sin cerrar,
    continúa leyendo líneas hasta que se cierre el bloque.
    """
    _print_banner()

    # Modo inicial: eval (el más útil para probar el intérprete)
    current_mode = 'eval'
    print(f"  {DIM}Modo actual: {GREEN}{BOLD}{current_mode}{RESET}\n")

    # Entorno global persistente para toda la sesión del REPL
    global_env = Environment()

    while True:
        try:
            # Prompt con indicación del modo actual
            mode_indicator = {
                'eval':   f'{GREEN}eval{RESET}',
                'parser': f'{CYAN}ast{RESET}',
                'lexer':  f'{YELLOW}lex{RESET}',
            }.get(current_mode, current_mode)

            prompt = f"{CYAN}{BOLD}[{mode_indicator}{CYAN}{BOLD}]>> {RESET}"
            source = input(prompt)

        except (EOFError, KeyboardInterrupt):
            # Ctrl+D o Ctrl+C → salir limpiamente
            print(f"\n{YELLOW}¡Hasta luego! 👋{RESET}")
            break

        # Ignorar líneas vacías
        if not source.strip():
            continue

        # ── Comandos especiales ──────────────────────────────────────────────
        if source.strip() == 'salir()':
            print(f"\n{YELLOW}¡Hasta luego! 👋{RESET}")
            break

        if source.strip() == 'modo()':
            idx = _MODES.index(current_mode)
            current_mode = _MODES[(idx + 1) % len(_MODES)]
            print(f"  {DIM}Modo cambiado a: {GREEN}{BOLD}{current_mode}{RESET}\n")
            continue

        if source.strip() == 'ayuda()':
            _print_help()
            continue

        # ── Soporte multilínea ───────────────────────────────────────────────
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

        # ── Procesar según el modo ───────────────────────────────────────────
        if current_mode == 'lexer':
            _show_tokens(source)
        elif current_mode == 'parser':
            _show_ast(source)
        else:
            _eval_source(source, global_env)