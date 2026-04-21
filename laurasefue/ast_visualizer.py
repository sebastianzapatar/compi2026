# =============================================================================
# ast_visualizer.py — Visualizador de Árboles Sintácticos (AST)
#
# Este módulo recorre los nodos del AST y genera una representación
# visual en forma de árbol usando caracteres Unicode de tipo box-drawing.
#
# Ejemplo de salida para: let x = 5 + 3;
#
#   Program
#   └── LetStatement
#       ├── name: Identifier
#       │   └── "x"
#       └── value: InfixExpression [+]
#           ├── left: IntegerLiteral
#           │   └── 5
#           └── right: IntegerLiteral
#               └── 3
# =============================================================================

from laurasefue import ast

# ─── Caracteres Unicode para dibujar el árbol ────────────────────────────────
PIPE      = '│   '    # Línea vertical que continúa (hay más hermanos abajo)
TEE       = '├── '    # Rama con más hermanos después
ELBOW     = '└── '    # Última rama (no hay más hermanos)
BLANK     = '    '    # Espacio vacío (sin línea vertical)

# ─── Colores ANSI ────────────────────────────────────────────────────────────
RESET   = '\033[0m'
BOLD    = '\033[1m'
RED     = '\033[91m'
GREEN   = '\033[92m'
YELLOW  = '\033[93m'
BLUE    = '\033[94m'
MAGENTA = '\033[95m'
CYAN    = '\033[96m'
DIM     = '\033[2m'
WHITE   = '\033[97m'


def visualize(program: ast.Program) -> str:
    """
    Genera la representación visual completa del AST como string.

    Recibe el nodo raíz Program y retorna un string multilínea
    con el árbol dibujado usando caracteres Unicode.
    """
    lines: list[str] = []
    lines.append(f'{MAGENTA}{BOLD}🌳 Program{RESET}')

    stmts = program.statements
    for i, stmt in enumerate(stmts):
        is_last = (i == len(stmts) - 1)
        connector = ELBOW if is_last else TEE
        child_prefix = BLANK if is_last else PIPE
        _build_node(stmt, '', connector, child_prefix, lines)

    return '\n'.join(lines)


def _build_node(
    node: ast.Node,
    prefix: str,
    connector: str,
    child_prefix: str,
    lines: list[str],
    label: str = ''
) -> None:
    """
    Construye recursivamente las líneas de un nodo del AST.

    Parámetros:
      node          → El nodo AST a visualizar
      prefix        → Prefijo acumulado de indentación (tuberías │ y espacios)
      connector     → El conector de este nodo (├── o └──)
      child_prefix  → El prefijo que heredarán los hijos de este nodo
      lines         → Lista acumuladora de líneas de salida
      label         → Etiqueta opcional antes del tipo de nodo (e.g. "left: ")
    """
    full_prefix = prefix + connector
    next_prefix = prefix + child_prefix

    # ─── Despachar según el tipo de nodo ─────────────────────────────────
    if isinstance(node, ast.LetStatement):
        _build_let(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.ReturnStatement):
        _build_return(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.PrintStatement):
        _build_print(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.ExpressionStatement):
        _build_expression_stmt(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.WhileStatement):
        _build_while(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.ForStatement):
        _build_for(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.BreakStatement):
        lines.append(f'{full_prefix}{_label(label)}{YELLOW}{BOLD}BreakStatement{RESET}')

    elif isinstance(node, ast.ContinueStatement):
        lines.append(f'{full_prefix}{_label(label)}{YELLOW}{BOLD}ContinueStatement{RESET}')

    elif isinstance(node, ast.BlockStatement):
        _build_block(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.InfixExpression):
        _build_infix(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.PrefixExpression):
        _build_prefix(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.IfExpression):
        _build_if(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.FunctionLiteral):
        _build_function(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.CallExpression):
        _build_call(node, full_prefix, next_prefix, label, lines)

    elif isinstance(node, ast.IntegerLiteral):
        lines.append(
            f'{full_prefix}{_label(label)}{CYAN}IntegerLiteral{RESET}'
            f' {DIM}→{RESET} {WHITE}{BOLD}{node.value}{RESET}'
        )

    elif isinstance(node, ast.FloatLiteral):
        lines.append(
            f'{full_prefix}{_label(label)}{CYAN}FloatLiteral{RESET}'
            f' {DIM}→{RESET} {WHITE}{BOLD}{node.value}{RESET}'
        )

    elif isinstance(node, ast.StringLiteral):
        lines.append(
            f'{full_prefix}{_label(label)}{CYAN}StringLiteral{RESET}'
            f' {DIM}→{RESET} {GREEN}"{node.value}"{RESET}'
        )

    elif isinstance(node, ast.BooleanLiteral):
        val_color = GREEN if node.value else RED
        lines.append(
            f'{full_prefix}{_label(label)}{CYAN}BooleanLiteral{RESET}'
            f' {DIM}→{RESET} {val_color}{BOLD}'
            f'{"true" if node.value else "false"}{RESET}'
        )

    elif isinstance(node, ast.Identifier):
        lines.append(
            f'{full_prefix}{_label(label)}{CYAN}Identifier{RESET}'
            f' {DIM}→{RESET} {BLUE}{BOLD}{node.value}{RESET}'
        )

    else:
        lines.append(
            f'{full_prefix}{_label(label)}{DIM}{type(node).__name__}{RESET}'
        )


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES DE CONSTRUCCIÓN POR TIPO DE NODO
# ─────────────────────────────────────────────────────────────────────────────

def _label(label: str) -> str:
    """Formatea la etiqueta opcional (e.g. 'left: ', 'cond: ')."""
    if label:
        return f'{DIM}{label}: {RESET}'
    return ''


def _add_children(
    children: list[tuple[str, ast.Node]],
    next_prefix: str,
    lines: list[str]
) -> None:
    """
    Agrega una lista de hijos al árbol.

    Cada hijo es una tupla (etiqueta, nodo). Calcula automáticamente
    qué conector usar (├── para intermedios, └── para el último).
    """
    for i, (child_label, child_node) in enumerate(children):
        is_last_child = (i == len(children) - 1)
        conn = ELBOW if is_last_child else TEE
        cpfx = BLANK if is_last_child else PIPE
        _build_node(child_node, next_prefix, conn, cpfx, lines, label=child_label)


def _build_let(
    node: ast.LetStatement,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para LetStatement."""
    lines.append(
        f'{full_prefix}{_label(label)}{YELLOW}{BOLD}LetStatement{RESET}'
    )

    children: list[tuple[str, ast.Node]] = [('name', node.name)]
    if node.value is not None:
        children.append(('value', node.value))

    _add_children(children, next_prefix, lines)


def _build_return(
    node: ast.ReturnStatement,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para ReturnStatement."""
    lines.append(
        f'{full_prefix}{_label(label)}{YELLOW}{BOLD}ReturnStatement{RESET}'
    )

    if node.return_value is not None:
        _add_children([('value', node.return_value)], next_prefix, lines)


def _build_print(
    node: ast.PrintStatement,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para PrintStatement."""
    lines.append(
        f'{full_prefix}{_label(label)}{YELLOW}{BOLD}PrintStatement{RESET}'
    )

    _add_children([('value', node.value)], next_prefix, lines)


def _build_expression_stmt(
    node: ast.ExpressionStatement,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para ExpressionStatement."""
    lines.append(
        f'{full_prefix}{_label(label)}{YELLOW}{BOLD}ExpressionStatement{RESET}'
    )

    if node.expression is not None:
        _add_children([('expr', node.expression)], next_prefix, lines)


def _build_infix(
    node: ast.InfixExpression,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para InfixExpression."""
    lines.append(
        f'{full_prefix}{_label(label)}'
        f'{CYAN}InfixExpression{RESET} '
        f'{RED}{BOLD}[ {node.operator} ]{RESET}'
    )

    children: list[tuple[str, ast.Node]] = [('left', node.left)]
    if node.right is not None:
        children.append(('right', node.right))

    _add_children(children, next_prefix, lines)


def _build_prefix(
    node: ast.PrefixExpression,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para PrefixExpression."""
    lines.append(
        f'{full_prefix}{_label(label)}'
        f'{CYAN}PrefixExpression{RESET} '
        f'{RED}{BOLD}[ {node.operator} ]{RESET}'
    )

    if node.right is not None:
        _add_children([('right', node.right)], next_prefix, lines)


def _build_if(
    node: ast.IfExpression,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para IfExpression."""
    lines.append(
        f'{full_prefix}{_label(label)}{MAGENTA}{BOLD}IfExpression{RESET}'
    )

    children: list[tuple[str, ast.Node]] = [
        ('cond', node.condition),
        ('then', node.consequence),
    ]

    # Agregar ramas elseif
    for i, (alt_cond, alt_block) in enumerate(node.alternatives):
        # Para cada elseif, creamos un nodo virtual que agrupa condición y bloque
        # Pero como son dos nodos, los agregamos individualmente con etiquetas
        children.append((f'elseif[{i}] cond', alt_cond))
        children.append((f'elseif[{i}] body', alt_block))

    # Agregar bloque else
    if node.else_block is not None:
        children.append(('else', node.else_block))

    _add_children(children, next_prefix, lines)


def _build_block(
    node: ast.BlockStatement,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para BlockStatement."""
    lines.append(
        f'{full_prefix}{_label(label)}'
        f'{DIM}BlockStatement{RESET} '
        f'{DIM}({len(node.statements)} stmt{"s" if len(node.statements) != 1 else ""}){RESET}'
    )

    children = [(f'[{i}]', s) for i, s in enumerate(node.statements)]
    _add_children(children, next_prefix, lines)


def _build_while(
    node: ast.WhileStatement,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para WhileStatement."""
    lines.append(
        f'{full_prefix}{_label(label)}{MAGENTA}{BOLD}WhileStatement{RESET}'
    )

    _add_children([
        ('cond', node.condition),
        ('body', node.body),
    ], next_prefix, lines)


def _build_for(
    node: ast.ForStatement,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para ForStatement."""
    lines.append(
        f'{full_prefix}{_label(label)}{MAGENTA}{BOLD}ForStatement{RESET}'
    )

    children: list[tuple[str, ast.Node]] = []
    if node.init is not None:
        children.append(('init', node.init))
    if node.condition is not None:
        children.append(('cond', node.condition))
    if node.update is not None:
        children.append(('update', node.update))
    children.append(('body', node.body))

    _add_children(children, next_prefix, lines)


def _build_function(
    node: ast.FunctionLiteral,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para FunctionLiteral."""
    name_str = f' {BLUE}"{node.name}"{RESET}' if node.name else ''
    params_str = ', '.join(str(p) for p in node.parameters)
    lines.append(
        f'{full_prefix}{_label(label)}'
        f'{MAGENTA}{BOLD}FunctionLiteral{RESET}'
        f'{name_str} '
        f'{DIM}({params_str}){RESET}'
    )

    # Los parámetros como hijos
    children: list[tuple[str, ast.Node]] = []
    for p in node.parameters:
        children.append(('param', p))
    children.append(('body', node.body))

    _add_children(children, next_prefix, lines)


def _build_call(
    node: ast.CallExpression,
    full_prefix: str,
    next_prefix: str,
    label: str,
    lines: list[str]
) -> None:
    """Construye el subárbol para CallExpression."""
    lines.append(
        f'{full_prefix}{_label(label)}'
        f'{MAGENTA}{BOLD}CallExpression{RESET}'
    )

    children: list[tuple[str, ast.Node]] = [('func', node.function)]
    for i, arg in enumerate(node.arguments):
        children.append((f'arg[{i}]', arg))

    _add_children(children, next_prefix, lines)
