# =============================================================================
# test_parser.py — Pruebas Unitarias del Parser
#
# Verifica el correcto funcionamiento del analizador sintáctico.
# Cada clase de test se enfoca en un tipo de nodo del AST.
#
# Ejecutar: pytest test/test_parser.py -v
# =============================================================================

import pytest
from laurasefue.lexer import Lexer
from laurasefue.parser import Parser
from laurasefue import ast


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIONES AUXILIARES
# ─────────────────────────────────────────────────────────────────────────────

def parse(source: str) -> ast.Program:
    """
    Función auxiliar que parsea código fuente y retorna el programa.

    Verifica que no haya errores de parseo; si los hay, falla el test
    mostrando los errores encontrados.
    """
    lexer = Lexer(source)
    parser = Parser(lexer)
    program = parser.parse_program()

    if parser.errors:
        error_msgs = '\n'.join(f'  - {e}' for e in parser.errors)
        pytest.fail(f'El parser reportó errores:\n{error_msgs}')

    return program


def parse_single_statement(source: str) -> ast.Statement:
    """
    Parsea código que debe producir exactamente UNA sentencia.

    Retorna esa sentencia directamente para facilitar las aserciones.
    """
    program = parse(source)
    assert len(program.statements) == 1, \
        f'Se esperaba 1 sentencia, se obtuvieron {len(program.statements)}'
    return program.statements[0]


def parse_expression_value(source: str) -> ast.Expression:
    """
    Parsea código que es una expresión sola y retorna la Expression.

    El código se envuelve automáticamente en un ExpressionStatement,
    así que extraemos la expresión interna.
    """
    stmt = parse_single_statement(source)
    assert isinstance(stmt, ast.ExpressionStatement), \
        f'Se esperaba ExpressionStatement, se obtuvo {type(stmt).__name__}'
    assert stmt.expression is not None
    return stmt.expression


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: SENTENCIA LET
# ─────────────────────────────────────────────────────────────────────────────

class TestLetStatement:
    """Pruebas para let <nombre> = <expresión>;"""

    def test_let_entero(self):
        """let x = 5; debe crear un LetStatement con IntegerLiteral"""
        stmt = parse_single_statement('let x = 5;')

        assert isinstance(stmt, ast.LetStatement)
        assert stmt.token_literal() == 'let'
        assert str(stmt.name) == 'x'
        assert isinstance(stmt.value, ast.IntegerLiteral)
        assert stmt.value.value == 5

    def test_let_flotante(self):
        """let pi = 3.14; debe crear un LetStatement con FloatLiteral"""
        stmt = parse_single_statement('let pi = 3.14;')

        assert isinstance(stmt, ast.LetStatement)
        assert str(stmt.name) == 'pi'
        assert isinstance(stmt.value, ast.FloatLiteral)
        assert stmt.value.value == 3.14

    def test_let_booleano_true(self):
        """let activo = true;"""
        stmt = parse_single_statement('let activo = true;')

        assert isinstance(stmt, ast.LetStatement)
        assert str(stmt.name) == 'activo'
        assert isinstance(stmt.value, ast.BooleanLiteral)
        assert stmt.value.value is True

    def test_let_booleano_false(self):
        """let inactivo = false;"""
        stmt = parse_single_statement('let inactivo = false;')

        assert isinstance(stmt, ast.LetStatement)
        assert str(stmt.name) == 'inactivo'
        assert isinstance(stmt.value, ast.BooleanLiteral)
        assert stmt.value.value is False

    def test_let_string(self):
        """let nombre = "Laura";"""
        stmt = parse_single_statement('let nombre = "Laura";')

        assert isinstance(stmt, ast.LetStatement)
        assert str(stmt.name) == 'nombre'
        assert isinstance(stmt.value, ast.StringLiteral)
        assert stmt.value.value == 'Laura'

    def test_let_expresion(self):
        """let resultado = 10 + 5; debe parsear la expresión infija"""
        stmt = parse_single_statement('let resultado = 10 + 5;')

        assert isinstance(stmt, ast.LetStatement)
        assert str(stmt.name) == 'resultado'
        assert isinstance(stmt.value, ast.InfixExpression)
        assert stmt.value.operator == '+'

    def test_let_identificador(self):
        """let y = x; asigna una variable a otra"""
        stmt = parse_single_statement('let y = x;')

        assert isinstance(stmt, ast.LetStatement)
        assert str(stmt.name) == 'y'
        assert isinstance(stmt.value, ast.Identifier)
        assert stmt.value.value == 'x'

    def test_let_sin_punto_y_coma(self):
        """let x = 5 (el punto y coma es opcional)"""
        stmt = parse_single_statement('let x = 5')

        assert isinstance(stmt, ast.LetStatement)
        assert str(stmt.name) == 'x'
        assert isinstance(stmt.value, ast.IntegerLiteral)
        assert stmt.value.value == 5

    def test_let_con_funcion(self):
        """let suma = function(a, b) { return a + b; };"""
        stmt = parse_single_statement(
            'let suma = function(a, b) { return a + b; };'
        )

        assert isinstance(stmt, ast.LetStatement)
        assert str(stmt.name) == 'suma'
        assert isinstance(stmt.value, ast.FunctionLiteral)
        # El nombre se asigna automáticamente al de la variable
        assert stmt.value.name == 'suma'

    def test_let_multiples(self):
        """Parsea múltiples sentencias let"""
        program = parse('let x = 5; let y = 10; let z = x;')

        assert len(program.statements) == 3
        for stmt in program.statements:
            assert isinstance(stmt, ast.LetStatement)


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: SENTENCIA RETURN
# ─────────────────────────────────────────────────────────────────────────────

class TestReturnStatement:
    """Pruebas para return <expresión>;"""

    def test_return_entero(self):
        """return 5;"""
        stmt = parse_single_statement('return 5;')

        assert isinstance(stmt, ast.ReturnStatement)
        assert stmt.token_literal() == 'return'
        assert isinstance(stmt.return_value, ast.IntegerLiteral)
        assert stmt.return_value.value == 5

    def test_return_expresion(self):
        """return x + 1;"""
        stmt = parse_single_statement('return x + 1;')

        assert isinstance(stmt, ast.ReturnStatement)
        assert isinstance(stmt.return_value, ast.InfixExpression)

    def test_return_booleano(self):
        """return true;"""
        stmt = parse_single_statement('return true;')

        assert isinstance(stmt, ast.ReturnStatement)
        assert isinstance(stmt.return_value, ast.BooleanLiteral)
        assert stmt.return_value.value is True


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: SENTENCIA PRINT
# ─────────────────────────────────────────────────────────────────────────────

class TestPrintStatement:
    """Pruebas para print(<expresión>);"""

    def test_print_entero(self):
        """print(42);"""
        stmt = parse_single_statement('print(42);')

        assert isinstance(stmt, ast.PrintStatement)
        assert stmt.token_literal() == 'print'
        assert isinstance(stmt.value, ast.IntegerLiteral)
        assert stmt.value.value == 42

    def test_print_string(self):
        """print("hola mundo");"""
        stmt = parse_single_statement('print("hola mundo");')

        assert isinstance(stmt, ast.PrintStatement)
        assert isinstance(stmt.value, ast.StringLiteral)
        assert stmt.value.value == 'hola mundo'

    def test_print_expresion(self):
        """print(x + 1);"""
        stmt = parse_single_statement('print(x + 1);')

        assert isinstance(stmt, ast.PrintStatement)
        assert isinstance(stmt.value, ast.InfixExpression)

    def test_print_variable(self):
        """print(resultado);"""
        stmt = parse_single_statement('print(resultado);')

        assert isinstance(stmt, ast.PrintStatement)
        assert isinstance(stmt.value, ast.Identifier)
        assert stmt.value.value == 'resultado'


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: LITERALES (Expressions que son valores directos)
# ─────────────────────────────────────────────────────────────────────────────

class TestLiterales:
    """Pruebas para literales: enteros, flotantes, strings, booleanos"""

    def test_entero(self):
        """42 como expresión"""
        expr = parse_expression_value('42')

        assert isinstance(expr, ast.IntegerLiteral)
        assert expr.value == 42
        assert str(expr) == '42'

    def test_flotante(self):
        """3.14 como expresión"""
        expr = parse_expression_value('3.14')

        assert isinstance(expr, ast.FloatLiteral)
        assert expr.value == 3.14

    def test_string(self):
        """"hola" como expresión"""
        expr = parse_expression_value('"hola"')

        assert isinstance(expr, ast.StringLiteral)
        assert expr.value == 'hola'

    def test_true(self):
        """true como expresión"""
        expr = parse_expression_value('true')

        assert isinstance(expr, ast.BooleanLiteral)
        assert expr.value is True

    def test_false(self):
        """false como expresión"""
        expr = parse_expression_value('false')

        assert isinstance(expr, ast.BooleanLiteral)
        assert expr.value is False

    def test_identificador(self):
        """miVariable como expresión"""
        expr = parse_expression_value('miVariable')

        assert isinstance(expr, ast.Identifier)
        assert expr.value == 'miVariable'


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: EXPRESIONES PREFIX (operadores unarios)
# ─────────────────────────────────────────────────────────────────────────────

class TestPrefixExpressions:
    """Pruebas para -<expr> y !<expr>"""

    def test_negacion_numerica(self):
        """-5 → PrefixExpression(operator='-', right=5)"""
        expr = parse_expression_value('-5')

        assert isinstance(expr, ast.PrefixExpression)
        assert expr.operator == '-'
        assert isinstance(expr.right, ast.IntegerLiteral)
        assert expr.right.value == 5

    def test_negacion_logica(self):
        """!true → PrefixExpression(operator='!', right=true)"""
        expr = parse_expression_value('!true')

        assert isinstance(expr, ast.PrefixExpression)
        assert expr.operator == '!'
        assert isinstance(expr.right, ast.BooleanLiteral)
        assert expr.right.value is True

    def test_negacion_identificador(self):
        """-x → PrefixExpression(operator='-', right=x)"""
        expr = parse_expression_value('-x')

        assert isinstance(expr, ast.PrefixExpression)
        assert expr.operator == '-'
        assert isinstance(expr.right, ast.Identifier)
        assert expr.right.value == 'x'

    def test_doble_negacion(self):
        """!!true → PrefixExpression(!, PrefixExpression(!, true))"""
        expr = parse_expression_value('!!true')

        assert isinstance(expr, ast.PrefixExpression)
        assert expr.operator == '!'
        assert isinstance(expr.right, ast.PrefixExpression)
        assert expr.right.operator == '!'

    def test_str_representation(self):
        """-5 debe representarse como '(-5)'"""
        expr = parse_expression_value('-5')
        assert str(expr) == '(-5)'


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: EXPRESIONES INFIX (operadores binarios)
# ─────────────────────────────────────────────────────────────────────────────

class TestInfixExpressions:
    """Pruebas para <izq> <op> <der>"""

    @pytest.mark.parametrize('source,operator,left_val,right_val', [
        ('5 + 3', '+', 5, 3),
        ('10 - 4', '-', 10, 4),
        ('6 * 7', '*', 6, 7),
        ('20 / 4', '/', 20, 4),
        ('10 % 3', '%', 10, 3),
        ('2 ^ 8', '^', 2, 8),
    ], ids=['suma', 'resta', 'multiplicacion', 'division', 'modulo', 'potencia'])
    def test_operaciones_aritmeticas(self, source, operator, left_val, right_val):
        """Prueba todas las operaciones aritméticas binarias"""
        expr = parse_expression_value(source)

        assert isinstance(expr, ast.InfixExpression)
        assert expr.operator == operator
        assert isinstance(expr.left, ast.IntegerLiteral)
        assert expr.left.value == left_val
        assert isinstance(expr.right, ast.IntegerLiteral)
        assert expr.right.value == right_val

    @pytest.mark.parametrize('source,operator', [
        ('x == y', '=='),
        ('a != b', '!='),
        ('x < y', '<'),
        ('x <= y', '<='),
        ('x > y', '>'),
        ('x >= y', '>='),
    ], ids=['igual', 'diferente', 'menor', 'menor_igual', 'mayor', 'mayor_igual'])
    def test_operaciones_comparacion(self, source, operator):
        """Prueba todas las operaciones de comparación"""
        expr = parse_expression_value(source)

        assert isinstance(expr, ast.InfixExpression)
        assert expr.operator == operator
        assert isinstance(expr.left, ast.Identifier)
        assert isinstance(expr.right, ast.Identifier)

    @pytest.mark.parametrize('source,operator', [
        ('x and y', 'and'),
        ('a or b', 'or'),
    ], ids=['and', 'or'])
    def test_operaciones_logicas(self, source, operator):
        """Prueba operadores lógicos and y or"""
        expr = parse_expression_value(source)

        assert isinstance(expr, ast.InfixExpression)
        assert expr.operator == operator

    def test_str_representation(self):
        """5 + 3 debe representarse como '(5 + 3)'"""
        expr = parse_expression_value('5 + 3')
        assert str(expr) == '(5 + 3)'


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: PRECEDENCIA DE OPERADORES
# ─────────────────────────────────────────────────────────────────────────────

class TestPrecedencia:
    """
    Pruebas para verificar que la precedencia de operadores funciona.

    La representación en string del AST usa paréntesis para mostrar
    exactamente cómo se agrupan las operaciones.
    """

    @pytest.mark.parametrize('source,expected', [
        # Multiplicación tiene mayor precedencia que suma
        ('2 + 3 * 4', '(2 + (3 * 4))'),
        # Resta y suma tienen la misma precedencia (left-to-right)
        ('5 - 2 + 1', '((5 - 2) + 1)'),
        # Los paréntesis anulan la precedencia natural
        ('(2 + 3) * 4', '((2 + 3) * 4)'),
        # Prefix tiene mayor precedencia que infix
        ('-5 + 3', '((-5) + 3)'),
        # Operadores lógicos tienen menor precedencia que comparación
        ('x < 5 and y > 3', '((x < 5) and (y > 3))'),
        # OR tiene menor precedencia que AND
        ('a or b and c', '(a or (b and c))'),
        # Comparación vs aritmética
        ('x + 1 < y * 2', '((x + 1) < (y * 2))'),
        # Negación lógica
        ('!true == false', '((!true) == false)'),
        # Potencia tiene mayor precedencia que multiplicación
        ('2 * 3 ^ 4', '(2 * (3 ^ 4))'),
    ], ids=[
        'mult_antes_que_suma',
        'misma_prec_izq_a_der',
        'parentesis_anulan_prec',
        'prefix_antes_infix',
        'logicos_vs_comparacion',
        'or_vs_and',
        'comparacion_vs_aritmetica',
        'negacion_logica',
        'potencia_antes_mult',
    ])
    def test_precedencia(self, source, expected):
        """Verifica que la precedencia genere el AST correcto"""
        expr = parse_expression_value(source)
        assert str(expr) == expected


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: EXPRESIONES AGRUPADAS (paréntesis)
# ─────────────────────────────────────────────────────────────────────────────

class TestGroupedExpressions:
    """Pruebas para expresiones entre paréntesis"""

    def test_simple_agrupacion(self):
        """(5 + 3) debe parsear correctamente"""
        expr = parse_expression_value('(5 + 3)')

        assert isinstance(expr, ast.InfixExpression)
        assert expr.operator == '+'

    def test_agrupacion_altera_precedencia(self):
        """(1 + 2) * 3 → la suma se evalúa primero"""
        expr = parse_expression_value('(1 + 2) * 3')

        assert isinstance(expr, ast.InfixExpression)
        assert expr.operator == '*'
        # El lado izquierdo es la suma agrupada
        assert isinstance(expr.left, ast.InfixExpression)
        assert expr.left.operator == '+'

    def test_agrupacion_anidada(self):
        """((5)) → un entero doblemente agrupado"""
        expr = parse_expression_value('((5))')

        assert isinstance(expr, ast.IntegerLiteral)
        assert expr.value == 5


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: CONDICIONALES IF / ELSEIF / ELSE
# ─────────────────────────────────────────────────────────────────────────────

class TestIfExpression:
    """Pruebas para if (...) { } elseif (...) { } else { }"""

    def test_if_simple(self):
        """if (x > 5) { return x; }"""
        expr = parse_expression_value('if (x > 5) { return x; }')

        assert isinstance(expr, ast.IfExpression)
        # Condición
        assert isinstance(expr.condition, ast.InfixExpression)
        assert expr.condition.operator == '>'
        # Consecuencia
        assert len(expr.consequence.statements) == 1
        # Sin else ni elseif
        assert len(expr.alternatives) == 0
        assert expr.else_block is None

    def test_if_else(self):
        """if (x) { 1 } else { 2 }"""
        expr = parse_expression_value('if (x) { 1 } else { 2 }')

        assert isinstance(expr, ast.IfExpression)
        assert len(expr.consequence.statements) == 1
        assert expr.else_block is not None
        assert len(expr.else_block.statements) == 1

    def test_if_elseif(self):
        """if (x > 0) { 1 } elseif (x == 0) { 0 }"""
        expr = parse_expression_value(
            'if (x > 0) { 1 } elseif (x == 0) { 0 }'
        )

        assert isinstance(expr, ast.IfExpression)
        assert len(expr.alternatives) == 1
        # La condición del elseif
        alt_cond, alt_block = expr.alternatives[0]
        assert isinstance(alt_cond, ast.InfixExpression)
        assert alt_cond.operator == '=='
        assert expr.else_block is None

    def test_if_elseif_else(self):
        """if (a) { 1 } elseif (b) { 2 } else { 3 }"""
        expr = parse_expression_value(
            'if (a) { 1 } elseif (b) { 2 } else { 3 }'
        )

        assert isinstance(expr, ast.IfExpression)
        assert len(expr.alternatives) == 1
        assert expr.else_block is not None

    def test_if_multiples_elseif(self):
        """if (a) { 1 } elseif (b) { 2 } elseif (c) { 3 } else { 4 }"""
        expr = parse_expression_value(
            'if (a) { 1 } elseif (b) { 2 } elseif (c) { 3 } else { 4 }'
        )

        assert isinstance(expr, ast.IfExpression)
        assert len(expr.alternatives) == 2
        assert expr.else_block is not None


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: FUNCIONES
# ─────────────────────────────────────────────────────────────────────────────

class TestFunctionLiteral:
    """Pruebas para function(<params>) { <body> }"""

    def test_funcion_sin_parametros(self):
        """function() { return 5; }"""
        expr = parse_expression_value('function() { return 5; }')

        assert isinstance(expr, ast.FunctionLiteral)
        assert len(expr.parameters) == 0
        assert len(expr.body.statements) == 1

    def test_funcion_un_parametro(self):
        """function(x) { return x; }"""
        expr = parse_expression_value('function(x) { return x; }')

        assert isinstance(expr, ast.FunctionLiteral)
        assert len(expr.parameters) == 1
        assert str(expr.parameters[0]) == 'x'

    def test_funcion_multiples_parametros(self):
        """function(x, y, z) { return x + y + z; }"""
        expr = parse_expression_value(
            'function(x, y, z) { return x + y + z; }'
        )

        assert isinstance(expr, ast.FunctionLiteral)
        assert len(expr.parameters) == 3
        nombres = [str(p) for p in expr.parameters]
        assert nombres == ['x', 'y', 'z']

    def test_funcion_con_cuerpo_complejo(self):
        """Función con múltiples sentencias en el cuerpo"""
        source = '''function(n) {
            let resultado = 1;
            return resultado;
        }'''
        expr = parse_expression_value(source)

        assert isinstance(expr, ast.FunctionLiteral)
        assert len(expr.parameters) == 1
        assert len(expr.body.statements) == 2


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: LLAMADAS A FUNCIÓN
# ─────────────────────────────────────────────────────────────────────────────

class TestCallExpression:
    """Pruebas para <función>(<argumentos>)"""

    def test_llamada_sin_argumentos(self):
        """miFuncion()"""
        expr = parse_expression_value('miFuncion()')

        assert isinstance(expr, ast.CallExpression)
        assert isinstance(expr.function, ast.Identifier)
        assert expr.function.value == 'miFuncion'
        assert len(expr.arguments) == 0

    def test_llamada_con_un_argumento(self):
        """factorial(5)"""
        expr = parse_expression_value('factorial(5)')

        assert isinstance(expr, ast.CallExpression)
        assert len(expr.arguments) == 1
        assert isinstance(expr.arguments[0], ast.IntegerLiteral)
        assert expr.arguments[0].value == 5

    def test_llamada_con_multiples_argumentos(self):
        """suma(1, 2, 3)"""
        expr = parse_expression_value('suma(1, 2, 3)')

        assert isinstance(expr, ast.CallExpression)
        assert len(expr.arguments) == 3

    def test_llamada_con_expresiones(self):
        """operacion(x + 1, y * 2)"""
        expr = parse_expression_value('operacion(x + 1, y * 2)')

        assert isinstance(expr, ast.CallExpression)
        assert len(expr.arguments) == 2
        assert isinstance(expr.arguments[0], ast.InfixExpression)
        assert isinstance(expr.arguments[1], ast.InfixExpression)

    def test_llamada_anidada(self):
        """suma(factorial(3), factorial(4))"""
        expr = parse_expression_value('suma(factorial(3), factorial(4))')

        assert isinstance(expr, ast.CallExpression)
        assert len(expr.arguments) == 2
        assert isinstance(expr.arguments[0], ast.CallExpression)
        assert isinstance(expr.arguments[1], ast.CallExpression)

    def test_str_representation(self):
        """suma(1, 2) debe representarse como 'suma(1, 2)'"""
        expr = parse_expression_value('suma(1, 2)')
        assert str(expr) == 'suma(1, 2)'


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: WHILE
# ─────────────────────────────────────────────────────────────────────────────

class TestWhileStatement:
    """Pruebas para while (<condición>) { <cuerpo> }"""

    def test_while_simple(self):
        """while (x < 10) { let x = x + 1; }"""
        stmt = parse_single_statement('while (x < 10) { let x = x + 1; }')

        assert isinstance(stmt, ast.WhileStatement)
        assert stmt.token_literal() == 'while'
        # Condición
        assert isinstance(stmt.condition, ast.InfixExpression)
        assert stmt.condition.operator == '<'
        # Cuerpo
        assert len(stmt.body.statements) == 1
        assert isinstance(stmt.body.statements[0], ast.LetStatement)

    def test_while_multiples_sentencias(self):
        """while con múltiples sentencias en el cuerpo"""
        source = '''while (i < 5) {
            print(i);
            let i = i + 1;
        }'''
        stmt = parse_single_statement(source)

        assert isinstance(stmt, ast.WhileStatement)
        assert len(stmt.body.statements) == 2

    def test_while_condicion_booleana(self):
        """while (true) { break; }"""
        stmt = parse_single_statement('while (true) { break; }')

        assert isinstance(stmt, ast.WhileStatement)
        assert isinstance(stmt.condition, ast.BooleanLiteral)
        assert stmt.condition.value is True


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: FOR
# ─────────────────────────────────────────────────────────────────────────────

class TestForStatement:
    """Pruebas para for (<init>; <cond>; <update>) { <cuerpo> }"""

    def test_for_completo(self):
        """for (let i = 0; i < 10; let i = i + 1) { print(i); }"""
        stmt = parse_single_statement(
            'for (let i = 0; i < 10; let i = i + 1) { print(i); }'
        )

        assert isinstance(stmt, ast.ForStatement)
        assert stmt.token_literal() == 'for'
        # Inicialización
        assert isinstance(stmt.init, ast.LetStatement)
        assert str(stmt.init.name) == 'i'
        # Condición
        assert isinstance(stmt.condition, ast.InfixExpression)
        assert stmt.condition.operator == '<'
        # Actualización
        assert isinstance(stmt.update, ast.LetStatement)
        # Cuerpo
        assert len(stmt.body.statements) == 1


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: BREAK Y CONTINUE
# ─────────────────────────────────────────────────────────────────────────────

class TestBreakContinue:
    """Pruebas para break; y continue;"""

    def test_break(self):
        """break;"""
        stmt = parse_single_statement('break;')

        assert isinstance(stmt, ast.BreakStatement)
        assert stmt.token_literal() == 'break'
        assert str(stmt) == 'break;'

    def test_continue(self):
        """continue;"""
        stmt = parse_single_statement('continue;')

        assert isinstance(stmt, ast.ContinueStatement)
        assert stmt.token_literal() == 'continue'
        assert str(stmt) == 'continue;'

    def test_break_dentro_de_while(self):
        """while (true) { break; }"""
        stmt = parse_single_statement('while (true) { break; }')

        assert isinstance(stmt, ast.WhileStatement)
        assert len(stmt.body.statements) == 1
        assert isinstance(stmt.body.statements[0], ast.BreakStatement)

    def test_continue_dentro_de_while(self):
        """while (true) { continue; }"""
        stmt = parse_single_statement('while (true) { continue; }')

        assert isinstance(stmt, ast.WhileStatement)
        assert len(stmt.body.statements) == 1
        assert isinstance(stmt.body.statements[0], ast.ContinueStatement)


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: REPRESENTACIÓN STRING DEL AST
# ─────────────────────────────────────────────────────────────────────────────

class TestASTString:
    """
    Pruebas para __str__ de los nodos del AST.

    La representación en string es crucial para debug y para
    verificar que el AST se construyó correctamente.
    """

    def test_let_str(self):
        """let x = 5; se representa como 'let x = 5;'"""
        stmt = parse_single_statement('let x = 5;')
        assert str(stmt) == 'let x = 5;'

    def test_return_str(self):
        """return 5; se representa como 'return 5;'"""
        stmt = parse_single_statement('return 5;')
        assert str(stmt) == 'return 5;'

    def test_print_str(self):
        """print(42); se representa como 'print(42);'"""
        stmt = parse_single_statement('print(42);')
        assert str(stmt) == 'print(42);'

    def test_infix_str(self):
        """5 + 3 se representa como '(5 + 3)'"""
        expr = parse_expression_value('5 + 3')
        assert str(expr) == '(5 + 3)'

    def test_prefix_str(self):
        """-5 se representa como '(-5)'"""
        expr = parse_expression_value('-5')
        assert str(expr) == '(-5)'

    def test_string_literal_str(self):
        """Un string se envuelve en comillas"""
        expr = parse_expression_value('"hola"')
        assert str(expr) == '"hola"'

    def test_boolean_str(self):
        """Los booleanos se representan en minúscula"""
        assert str(parse_expression_value('true')) == 'true'
        assert str(parse_expression_value('false')) == 'false'


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: MANEJO DE ERRORES DEL PARSER
# ─────────────────────────────────────────────────────────────────────────────

class TestParserErrors:
    """Pruebas para verificar que el parser reporta errores correctamente"""

    def test_error_let_sin_identificador(self):
        """let = 5; debe generar un error (falta el nombre)"""
        lexer = Lexer('let = 5;')
        parser = Parser(lexer)
        parser.parse_program()

        assert len(parser.errors) > 0
        assert 'IDENTIFIER' in parser.errors[0]

    def test_error_let_sin_asignacion(self):
        """let x 5; debe generar un error (falta el '=')"""
        lexer = Lexer('let x 5;')
        parser = Parser(lexer)
        parser.parse_program()

        assert len(parser.errors) > 0
        assert 'ASSIGN' in parser.errors[0]

    def test_error_parentesis_sin_cerrar(self):
        """(5 + 3 → falta el ')' de cierre"""
        lexer = Lexer('(5 + 3')
        parser = Parser(lexer)
        parser.parse_program()

        assert len(parser.errors) > 0


# ─────────────────────────────────────────────────────────────────────────────
# TESTS: PROGRAMAS COMPLETOS
# ─────────────────────────────────────────────────────────────────────────────

class TestProgramasCompletos:
    """
    Pruebas de integración con programas completos.

    Verifica que el parser puede manejar múltiples sentencias y
    construcciones complejas juntas.
    """

    def test_programa_factorial(self):
        """Programa que define una función factorial recursiva"""
        source = '''
        let factorial = function(n) {
            if (n <= 1) {
                return 1;
            } else {
                return n * factorial(n - 1);
            }
        };
        let resultado = factorial(5);
        print(resultado);
        '''
        program = parse(source)

        assert len(program.statements) == 3
        assert isinstance(program.statements[0], ast.LetStatement)
        assert isinstance(program.statements[1], ast.LetStatement)
        assert isinstance(program.statements[2], ast.PrintStatement)

    def test_programa_fibonacci(self):
        """Programa con función fibonacci"""
        source = '''
        let fib = function(n) {
            if (n <= 0) { return 0; }
            elseif (n == 1) { return 1; }
            else { return fib(n - 1) + fib(n - 2); }
        };
        print(fib(10));
        '''
        program = parse(source)

        assert len(program.statements) == 2
        assert isinstance(program.statements[0], ast.LetStatement)
        assert isinstance(program.statements[1], ast.PrintStatement)

    def test_programa_con_while(self):
        """Programa con while y variables"""
        source = '''
        let x = 0;
        while (x < 5) {
            print(x);
            let x = x + 1;
        }
        '''
        program = parse(source)

        assert len(program.statements) == 2
        assert isinstance(program.statements[0], ast.LetStatement)
        assert isinstance(program.statements[1], ast.WhileStatement)

    def test_programa_con_for(self):
        """Programa con bucle for"""
        source = '''
        for (let i = 0; i < 10; let i = i + 1) {
            print(i);
        }
        '''
        program = parse(source)

        assert len(program.statements) == 1
        assert isinstance(program.statements[0], ast.ForStatement)

    def test_programa_expresiones_complejas(self):
        """Programa con expresiones complejas anidadas"""
        source = '''
        let a = 5;
        let b = 10;
        let c = a + b * 2;
        let d = (a + b) * 2;
        print(c);
        print(d);
        '''
        program = parse(source)

        assert len(program.statements) == 6

    def test_programa_vacio(self):
        """Un programa vacío no debe generar errores"""
        program = parse('')
        assert len(program.statements) == 0

    def test_programa_solo_comentarios(self):
        """Programa con solo comentarios → programa vacío"""
        program = parse('// esto es un comentario\n// otro comentario')
        assert len(program.statements) == 0
