# =============================================================================
# tests/test_parser.py — Pruebas del Analizador Sintáctico (Parser)
#
# Verifica que el parser construye el AST correcto para cada construcción
# del lenguaje. Se prueba tanto la estructura del árbol (tipos de nodos)
# como los valores concretos (literales, operadores, nombres).
# =============================================================================

import pytest
from laurasefue.lexer import Lexer
from laurasefue.parser import Parser
from laurasefue import ast


# ─── FUNCIÓN AUXILIAR ────────────────────────────────────────────────────────

def parse(source: str) -> ast.Program:
    """
    Parsea un string de código fuente y retorna el nodo Program del AST.
    También verifica que no haya errores de parseo; si los hay, falla el test
    mostrando todos los errores encontrados.
    """
    lexer = Lexer(source)
    parser = Parser(lexer)
    program = parser.parse_program()

    # Si hay errores de parseo, el test falla con un mensaje descriptivo
    assert parser.errors == [], (
        f'El parser encontró {len(parser.errors)} error(es):\n'
        + '\n'.join(f'  • {e}' for e in parser.errors)
    )
    return program


# ─── LET STATEMENT ────────────────────────────────────────────────────────────

class TestLetStatement:
    """Pruebas para 'let nombre = expresión;'"""

    def test_let_entero(self):
        """'let x = 5;' debe parsear como LetStatement con IntegerLiteral."""
        program = parse('let x = 5;')
        assert len(program.statements) == 1
        stmt = program.statements[0]
        assert isinstance(stmt, ast.LetStatement)
        assert stmt.name.value == 'x'
        assert isinstance(stmt.value, ast.IntegerLiteral)
        assert stmt.value.value == 5

    def test_let_flotante(self):
        """'let pi = 3.14;' debe parsear como LetStatement con FloatLiteral."""
        program = parse('let pi = 3.14;')
        stmt = program.statements[0]
        assert isinstance(stmt, ast.LetStatement)
        assert stmt.name.value == 'pi'
        assert isinstance(stmt.value, ast.FloatLiteral)
        assert stmt.value.value == 3.14

    def test_let_string(self):
        """'let s = "hola";' debe parsear el string correctamente."""
        program = parse('let s = "hola";')
        stmt = program.statements[0]
        assert isinstance(stmt.value, ast.StringLiteral)
        assert stmt.value.value == 'hola'

    def test_let_booleano_true(self):
        """'let b = true;' debe parsear como BooleanLiteral(True)."""
        program = parse('let b = true;')
        stmt = program.statements[0]
        assert isinstance(stmt.value, ast.BooleanLiteral)
        assert stmt.value.value is True

    def test_let_booleano_false(self):
        """'let b = false;' debe parsear como BooleanLiteral(False)."""
        program = parse('let b = false;')
        stmt = program.statements[0]
        assert isinstance(stmt.value, ast.BooleanLiteral)
        assert stmt.value.value is False

    def test_let_expresion_infija(self):
        """'let r = 10 + 5;' debe parsear como LetStatement con InfixExpression."""
        program = parse('let r = 10 + 5;')
        stmt = program.statements[0]
        assert isinstance(stmt.value, ast.InfixExpression)
        assert stmt.value.operator == '+'


# ─── RETURN STATEMENT ────────────────────────────────────────────────────────

class TestReturnStatement:
    """Pruebas para 'return expresión;'"""

    def test_return_entero(self):
        """'return 5;' debe parsear como ReturnStatement con IntegerLiteral."""
        program = parse('return 5;')
        stmt = program.statements[0]
        assert isinstance(stmt, ast.ReturnStatement)
        assert isinstance(stmt.return_value, ast.IntegerLiteral)
        assert stmt.return_value.value == 5

    def test_return_expresion(self):
        """'return x + 1;' debe parsear como ReturnStatement con InfixExpression."""
        program = parse('return x + 1;')
        stmt = program.statements[0]
        assert isinstance(stmt, ast.ReturnStatement)
        assert isinstance(stmt.return_value, ast.InfixExpression)


# ─── EXPRESIONES PREFIJAS ─────────────────────────────────────────────────────

class TestExpresionPrefija:
    """Pruebas para operadores que aparecen antes de la expresión: ! y -"""

    def test_negacion_booleana(self):
        """'!true' debe parsear como PrefixExpression con operador '!'."""
        program = parse('!true;')
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, ast.PrefixExpression)
        assert expr.operator == '!'
        assert isinstance(expr.right, ast.BooleanLiteral)

    def test_negacion_numerica(self):
        """'-5' debe parsear como PrefixExpression con operador '-'."""
        program = parse('-5;')
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, ast.PrefixExpression)
        assert expr.operator == '-'
        assert isinstance(expr.right, ast.IntegerLiteral)
        assert expr.right.value == 5


# ─── EXPRESIONES INFIJAS ──────────────────────────────────────────────────────

class TestExpresionInfija:
    """Pruebas para los operadores binarios y su precedencia."""

    @pytest.mark.parametrize('op', ['+', '-', '*', '/', '%', '^',
                                     '==', '!=', '<', '<=', '>', '>=',
                                     'and', 'or'])
    def test_operador(self, op):
        """Cada operador binario debe parsear como InfixExpression correctamente."""
        program = parse(f'5 {op} 3;')
        stmt = program.statements[0]
        expr = stmt.expression
        assert isinstance(expr, ast.InfixExpression), (
            f'Se esperaba InfixExpression para el operador "{op}"'
        )
        assert expr.operator == op

    def test_precedencia_suma_vs_multiplicacion(self):
        """'1 + 2 * 3' debe agruparse como '1 + (2 * 3)', no '(1 + 2) * 3'."""
        program = parse('1 + 2 * 3;')
        expr = program.statements[0].expression
        # La expresión raíz debe ser la suma (menor precedencia)
        assert isinstance(expr, ast.InfixExpression)
        assert expr.operator == '+'
        # El lado derecho de la suma debe ser la multiplicación
        assert isinstance(expr.right, ast.InfixExpression)
        assert expr.right.operator == '*'

    def test_parentesis_cambia_precedencia(self):
        """'(1 + 2) * 3' debe agruparse como la multiplicación en la raíz."""
        program = parse('(1 + 2) * 3;')
        expr = program.statements[0].expression
        assert isinstance(expr, ast.InfixExpression)
        assert expr.operator == '*'
        # El lado izquierdo es la suma entre paréntesis
        assert isinstance(expr.left, ast.InfixExpression)
        assert expr.left.operator == '+'

    def test_encadenamiento_left(self):
        """'5 - 3 - 1' debe ser (5-3)-1 (asociatividad izquierda)."""
        program = parse('5 - 3 - 1;')
        expr = program.statements[0].expression
        assert isinstance(expr, ast.InfixExpression)
        assert expr.operator == '-'
        assert isinstance(expr.left, ast.InfixExpression)
        assert expr.left.operator == '-'


# ─── IF / ELSEIF / ELSE ───────────────────────────────────────────────────────

class TestCondicionales:
    """Pruebas para la estructura if / elseif / else."""

    def test_if_simple(self):
        """'if (x) { }' debe parsear como IfExpression con condición y bloque."""
        program = parse('if (x) { let y = 1; }')
        stmt = program.statements[0].expression
        assert isinstance(stmt, ast.IfExpression)
        assert isinstance(stmt.condition, ast.Identifier)
        assert len(stmt.consequence.statements) == 1
        assert stmt.else_block is None

    def test_if_else(self):
        """'if (x) { } else { }' debe parsear con un bloque else."""
        program = parse('if (x) { } else { let a = 1; }')
        stmt = program.statements[0].expression
        assert isinstance(stmt, ast.IfExpression)
        assert stmt.else_block is not None
        assert len(stmt.else_block.statements) == 1

    def test_if_elseif_else(self):
        """Múltiples ramas elseif deben capturarse en la lista alternatives."""
        source = '''
            if (x > 0) {
                let r = 1;
            } elseif (x == 0) {
                let r = 2;
            } else {
                let r = 3;
            }
        '''
        program = parse(source)
        stmt = program.statements[0].expression
        assert isinstance(stmt, ast.IfExpression)
        assert len(stmt.alternatives) == 1   # una rama elseif
        assert stmt.else_block is not None


# ─── WHILE ────────────────────────────────────────────────────────────────────

class TestWhile:
    """Pruebas para el bucle while."""

    def test_while_simple(self):
        """'while (cond) { }' debe parsear como WhileStatement."""
        program = parse('while (x < 10) { let x = x + 1; }')
        stmt = program.statements[0]
        assert isinstance(stmt, ast.WhileStatement)
        assert isinstance(stmt.condition, ast.InfixExpression)
        assert stmt.condition.operator == '<'
        assert len(stmt.body.statements) == 1

    def test_while_con_break(self):
        """El cuerpo de un while puede contener un BreakStatement."""
        program = parse('while (true) { break; }')
        stmt = program.statements[0]
        assert isinstance(stmt, ast.WhileStatement)
        body_stmt = stmt.body.statements[0]
        assert isinstance(body_stmt, ast.BreakStatement)


# ─── FOR ─────────────────────────────────────────────────────────────────────

class TestFor:
    """Pruebas para el bucle for."""

    def test_for_completo(self):
        """'for (let i = 0; i < 5; let i = i + 1) { }' debe parsear correctamente."""
        source = 'for (let i = 0; i < 5; let i = i + 1) { print(i); }'
        program = parse(source)
        stmt = program.statements[0]
        assert isinstance(stmt, ast.ForStatement)
        # Verificar que el init es un LetStatement
        assert isinstance(stmt.init, ast.LetStatement)
        assert stmt.init.name.value == 'i'
        # Verificar que la condición es una comparación
        assert isinstance(stmt.condition, ast.InfixExpression)
        assert stmt.condition.operator == '<'
        # Verificar que el update es un LetStatement
        assert isinstance(stmt.update, ast.LetStatement)
        # Verificar que el cuerpo tiene una sentencia
        assert len(stmt.body.statements) == 1

    def test_for_con_continue(self):
        """El cuerpo de un for puede contener un ContinueStatement."""
        source = 'for (let i = 0; i < 5; let i = i + 1) { continue; }'
        program = parse(source)
        stmt = program.statements[0]
        body_stmt = stmt.body.statements[0]
        assert isinstance(body_stmt, ast.ContinueStatement)


# ─── FUNCIONES ────────────────────────────────────────────────────────────────

class TestFunciones:
    """Pruebas para la definición y llamada de funciones."""

    def test_funcion_sin_parametros(self):
        """'function() { }' debe parsear como FunctionLiteral sin parámetros."""
        program = parse('function() { }')
        expr = program.statements[0].expression
        assert isinstance(expr, ast.FunctionLiteral)
        assert len(expr.parameters) == 0

    def test_funcion_un_parametro(self):
        """'function(x) { }' debe tener un parámetro."""
        program = parse('function(x) { return x; }')
        expr = program.statements[0].expression
        assert isinstance(expr, ast.FunctionLiteral)
        assert len(expr.parameters) == 1
        assert expr.parameters[0].value == 'x'

    def test_funcion_varios_parametros(self):
        """'function(a, b, c) { }' debe tener tres parámetros en orden."""
        program = parse('function(a, b, c) { }')
        expr = program.statements[0].expression
        assert len(expr.parameters) == 3
        assert [p.value for p in expr.parameters] == ['a', 'b', 'c']

    def test_funcion_asignada_a_variable(self):
        """'let f = function(x) { ... }' debe guardar el nombre en FunctionLiteral."""
        program = parse('let f = function(x) { return x; };')
        stmt = program.statements[0]
        assert isinstance(stmt, ast.LetStatement)
        fn = stmt.value
        assert isinstance(fn, ast.FunctionLiteral)
        assert fn.name == 'f'   # Nombre asignado automáticamente por el parser

    def test_llamada_sin_argumentos(self):
        """'f()' debe parsear como CallExpression sin argumentos."""
        program = parse('f()')
        expr = program.statements[0].expression
        assert isinstance(expr, ast.CallExpression)
        assert len(expr.arguments) == 0

    def test_llamada_con_argumentos(self):
        """'f(1, 2, 3)' debe parsear como CallExpression con 3 argumentos."""
        program = parse('f(1, 2, 3)')
        expr = program.statements[0].expression
        assert isinstance(expr, ast.CallExpression)
        assert len(expr.arguments) == 3

    def test_llamada_con_expresiones_como_argumentos(self):
        """Los argumentos pueden ser expresiones complejas."""
        program = parse('suma(x + 1, y * 2)')
        expr = program.statements[0].expression
        assert isinstance(expr, ast.CallExpression)
        assert isinstance(expr.arguments[0], ast.InfixExpression)
        assert isinstance(expr.arguments[1], ast.InfixExpression)


# ─── ERRORES DEL PARSER ───────────────────────────────────────────────────────

class TestErroresParser:
    """Pruebas para el manejo de errores de sintaxis."""

    def test_let_sin_identificador(self):
        """'let 5 = x;' debe registrar un error (falta el nombre)."""
        lexer = Lexer('let 5 = x;')
        parser = Parser(lexer)
        parser.parse_program()
        assert len(parser.errors) > 0

    def test_let_sin_asignacion(self):
        """'let x;' debe registrar un error (falta el '=')."""
        lexer = Lexer('let x;')
        parser = Parser(lexer)
        parser.parse_program()
        assert len(parser.errors) > 0

    def test_if_sin_parentesis(self):
        """'if x { }' (sin paréntesis) debe registrar error."""
        lexer = Lexer('if x { }')
        parser = Parser(lexer)
        parser.parse_program()
        assert len(parser.errors) > 0
