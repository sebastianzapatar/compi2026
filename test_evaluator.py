# =============================================================================
# test_evaluator.py — Tests del Evaluador
#
# Cubre todas las operaciones que implementa el evaluador:
#   - Literales (entero, flotante, booleano, string)
#   - Prefijos (-, !)
#   - Aritméticas (+, -, *, /, %, ^)
#   - Comparación (==, !=, <, <=, >, >=)
#   - Lógicas (and, or, !)
#   - Variables (let + identificador)
#   - Condicionales (if / elseif / else)
#   - Bucles (while, for, break, continue)
#   - Funciones (definición, llamada, closures, recursión)
#   - Errores de ejecución
# =============================================================================

import unittest

from laurasefue.lexer import Lexer
from laurasefue.parser import Parser
from laurasefue.evaluator import evaluate
from laurasefue.environment import Environment
from laurasefue.object_system import (
    Object, Integer, Float, Boolean, String, Null, Error, Function,
    ObjectType, TRUE, FALSE, NULL,
)


# ─── Helper ───────────────────────────────────────────────────────────────────

def _eval(source: str) -> Object:
    """Atajo: convierte código fuente → Object evaluado."""
    lexer = Lexer(source)
    parser = Parser(lexer)
    program = parser.parse_program()
    env = Environment()
    return evaluate(program, env)


def _assert_integer(obj: Object, expected: int):
    assert isinstance(obj, Integer), f'Esperado Integer, got {type(obj).__name__}: {obj}'
    assert obj.value == expected, f'Esperado {expected}, got {obj.value}'


def _assert_float(obj: Object, expected: float):
    assert isinstance(obj, Float), f'Esperado Float, got {type(obj).__name__}: {obj}'
    assert abs(obj.value - expected) < 1e-9, f'Esperado {expected}, got {obj.value}'


def _assert_bool(obj: Object, expected: bool):
    assert isinstance(obj, Boolean), f'Esperado Boolean, got {type(obj).__name__}: {obj}'
    assert obj.value == expected, f'Esperado {expected}, got {obj.value}'


def _assert_null(obj: Object):
    assert isinstance(obj, Null), f'Esperado Null, got {type(obj).__name__}: {obj}'


def _assert_error(obj: Object, expected_msg: str = ''):
    assert isinstance(obj, Error), f'Esperado Error, got {type(obj).__name__}: {obj}'
    if expected_msg:
        assert expected_msg in obj.message, \
            f'Mensaje esperado contiene "{expected_msg}", got "{obj.message}"'


# ─────────────────────────────────────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestLiterals(unittest.TestCase):
    """Evaluación de valores literales."""

    def test_integer(self):
        _assert_integer(_eval('5;'), 5)
        _assert_integer(_eval('0;'), 0)
        _assert_integer(_eval('1000;'), 1000)

    def test_float(self):
        _assert_float(_eval('3.14;'), 3.14)
        _assert_float(_eval('0.5;'), 0.5)

    def test_boolean_true(self):
        _assert_bool(_eval('true;'), True)

    def test_boolean_false(self):
        _assert_bool(_eval('false;'), False)

    def test_string(self):
        result = _eval('"hola mundo";')
        assert isinstance(result, String)
        assert result.value == 'hola mundo'


class TestPrefixExpressions(unittest.TestCase):
    """Operadores prefijos: - y !"""

    def test_minus_integer(self):
        _assert_integer(_eval('-5;'), -5)
        _assert_integer(_eval('-100;'), -100)

    def test_minus_float(self):
        _assert_float(_eval('-3.14;'), -3.14)

    def test_bang_true(self):
        _assert_bool(_eval('!true;'), False)

    def test_bang_false(self):
        _assert_bool(_eval('!false;'), True)

    def test_bang_integer(self):
        _assert_bool(_eval('!5;'), False)   # 5 es truthy  → !5 = false
        _assert_bool(_eval('!0;'), True)    # 0 es falsy   → !0 = true

    def test_double_bang(self):
        _assert_bool(_eval('!!true;'), True)
        _assert_bool(_eval('!!false;'), False)


class TestArithmetic(unittest.TestCase):
    """Operaciones aritméticas: + - * / % ^"""

    def test_addition(self):
        _assert_integer(_eval('3 + 4;'), 7)
        _assert_integer(_eval('0 + 0;'), 0)

    def test_subtraction(self):
        _assert_integer(_eval('10 - 3;'), 7)
        _assert_integer(_eval('5 - 10;'), -5)

    def test_multiplication(self):
        _assert_integer(_eval('4 * 5;'), 20)
        _assert_integer(_eval('0 * 1000;'), 0)

    def test_division_exact(self):
        _assert_integer(_eval('10 / 2;'), 5)
        _assert_integer(_eval('100 / 4;'), 25)

    def test_division_float_result(self):
        _assert_float(_eval('7 / 2;'), 3.5)
        _assert_float(_eval('1 / 3;'), 1/3)

    def test_modulo(self):
        _assert_integer(_eval('17 % 5;'), 2)
        _assert_integer(_eval('10 % 3;'), 1)
        _assert_integer(_eval('9 % 3;'), 0)

    def test_power(self):
        _assert_integer(_eval('2 ^ 8;'), 256)
        _assert_integer(_eval('3 ^ 3;'), 27)
        _assert_integer(_eval('5 ^ 0;'), 1)

    def test_power_negative_exponent(self):
        result = _eval('2 ^ -1;')
        assert isinstance(result, Float)

    def test_mixed_int_float(self):
        _assert_float(_eval('3 + 1.5;'), 4.5)
        _assert_float(_eval('10 - 0.5;'), 9.5)
        _assert_float(_eval('4 * 2.5;'), 10.0)

    def test_float_arithmetic(self):
        _assert_float(_eval('1.5 + 2.5;'), 4.0)
        _assert_float(_eval('3.0 * 2.0;'), 6.0)
        _assert_float(_eval('10.0 % 3.0;'), 1.0)

    def test_complex_expression(self):
        # (2 + 3) * 4 - 1
        _assert_integer(_eval('(2 + 3) * 4 - 1;'), 19)

    def test_division_by_zero(self):
        _assert_error(_eval('5 / 0;'), 'cero')

    def test_modulo_by_zero(self):
        _assert_error(_eval('5 % 0;'), 'cero')


class TestComparison(unittest.TestCase):
    """Operadores de comparación: == != < <= > >="""

    def test_equal_integers(self):
        _assert_bool(_eval('5 == 5;'), True)
        _assert_bool(_eval('5 == 6;'), False)

    def test_not_equal(self):
        _assert_bool(_eval('5 != 6;'), True)
        _assert_bool(_eval('5 != 5;'), False)

    def test_less_than(self):
        _assert_bool(_eval('3 < 5;'), True)
        _assert_bool(_eval('5 < 3;'), False)
        _assert_bool(_eval('5 < 5;'), False)

    def test_less_than_or_equal(self):
        _assert_bool(_eval('3 <= 5;'), True)
        _assert_bool(_eval('5 <= 5;'), True)
        _assert_bool(_eval('6 <= 5;'), False)

    def test_greater_than(self):
        _assert_bool(_eval('5 > 3;'), True)
        _assert_bool(_eval('3 > 5;'), False)

    def test_greater_than_or_equal(self):
        _assert_bool(_eval('5 >= 5;'), True)
        _assert_bool(_eval('6 >= 5;'), True)
        _assert_bool(_eval('4 >= 5;'), False)

    def test_boolean_equality(self):
        _assert_bool(_eval('true == true;'), True)
        _assert_bool(_eval('false == false;'), True)
        _assert_bool(_eval('true == false;'), False)

    def test_mixed_numeric_comparison(self):
        _assert_bool(_eval('3 == 3.0;'), True)
        _assert_bool(_eval('2.5 > 2;'), True)

    def test_string_equality(self):
        _assert_bool(_eval('"hola" == "hola";'), True)
        _assert_bool(_eval('"hola" != "mundo";'), True)


class TestLogical(unittest.TestCase):
    """Operadores lógicos: and, or, !"""

    def test_and_true(self):
        _assert_bool(_eval('true and true;'), True)

    def test_and_false(self):
        _assert_bool(_eval('true and false;'), False)
        _assert_bool(_eval('false and true;'), False)
        _assert_bool(_eval('false and false;'), False)

    def test_or_true(self):
        _assert_bool(_eval('true or false;'), True)
        _assert_bool(_eval('false or true;'), True)
        _assert_bool(_eval('true or true;'), True)

    def test_or_false(self):
        _assert_bool(_eval('false or false;'), False)

    def test_logical_with_expressions(self):
        _assert_bool(_eval('3 > 2 and 5 != 6;'), True)
        _assert_bool(_eval('1 > 2 or 3 == 3;'), True)
        _assert_bool(_eval('1 > 2 or 3 != 3;'), False)

    def test_not_operator(self):
        _assert_bool(_eval('!true;'), False)
        _assert_bool(_eval('!false;'), True)
        _assert_bool(_eval('!(3 > 2);'), False)


class TestStrings(unittest.TestCase):
    """Operaciones con strings."""

    def test_concatenation(self):
        result = _eval('"hola" + " mundo";')
        assert isinstance(result, String)
        assert result.value == 'hola mundo'

    def test_string_comparison(self):
        _assert_bool(_eval('"abc" == "abc";'), True)
        _assert_bool(_eval('"abc" != "xyz";'), True)


class TestVariables(unittest.TestCase):
    """Declaración y uso de variables con let."""

    def test_let_integer(self):
        _assert_integer(_eval('let x = 5; x;'), 5)

    def test_let_expression(self):
        _assert_integer(_eval('let x = 3 + 4; x;'), 7)

    def test_multiple_lets(self):
        _assert_integer(_eval('let x = 5; let y = 3; let z = x + y; z;'), 8)

    def test_let_reassignment(self):
        # let redefine en el mismo scope
        _assert_integer(_eval('let x = 5; let x = 10; x;'), 10)

    def test_undefined_variable(self):
        _assert_error(_eval('fooBarBaz;'), 'no definida')


class TestConditionals(unittest.TestCase):
    """Condicionales: if, elseif, else."""

    def test_if_true(self):
        _assert_integer(_eval('if (true) { 10; }'), 10)

    def test_if_false_no_else(self):
        _assert_null(_eval('if (false) { 10; }'))

    def test_if_else_true(self):
        _assert_integer(_eval('if (true) { 10; } else { 20; }'), 10)

    def test_if_else_false(self):
        _assert_integer(_eval('if (false) { 10; } else { 20; }'), 20)

    def test_elseif(self):
        code = '''
        let x = 0;
        if (x > 0) { 1; } elseif (x == 0) { 0; } else { -1; }
        '''
        _assert_integer(_eval(code), 0)

    def test_nested_if(self):
        code = '''
        let x = 5;
        if (x > 0) {
            if (x > 3) { 100; } else { 50; }
        } else {
            0;
        }
        '''
        _assert_integer(_eval(code), 100)


class TestWhileLoop(unittest.TestCase):
    """Bucles while con break y continue."""

    def test_basic_while(self):
        code = '''
        let x = 0;
        while (x < 5) { let x = x + 1; }
        x;
        '''
        _assert_integer(_eval(code), 5)

    def test_while_break(self):
        code = '''
        let x = 0;
        while (true) {
            let x = x + 1;
            if (x == 3) { break; }
        }
        x;
        '''
        _assert_integer(_eval(code), 3)

    def test_while_continue(self):
        # Suma solo números pares hasta 10
        code = '''
        let i = 0;
        let suma = 0;
        while (i < 10) {
            let i = i + 1;
            if (i % 2 != 0) { continue; }
            let suma = suma + i;
        }
        suma;
        '''
        _assert_integer(_eval(code), 30)  # 2+4+6+8+10


class TestForLoop(unittest.TestCase):
    """Bucles for con break y continue."""

    def test_basic_for(self):
        code = '''
        let suma = 0;
        for (let i = 1; i <= 5; let i = i + 1) {
            let suma = suma + i;
        }
        suma;
        '''
        _assert_integer(_eval(code), 15)  # 1+2+3+4+5

    def test_for_break(self):
        code = '''
        let suma = 0;
        for (let i = 0; i < 10; let i = i + 1) {
            if (i == 3) { break; }
            let suma = suma + i;
        }
        suma;
        '''
        _assert_integer(_eval(code), 3)  # 0+1+2

    def test_for_continue(self):
        code = '''
        let suma = 0;
        for (let i = 1; i <= 5; let i = i + 1) {
            if (i == 3) { continue; }
            let suma = suma + i;
        }
        suma;
        '''
        _assert_integer(_eval(code), 12)  # 1+2+4+5


class TestFunctions(unittest.TestCase):
    """Definición, llamada, closures y recursión."""

    def test_identity_function(self):
        _assert_integer(_eval('let id = function(x) { x; }; id(5);'), 5)

    def test_addition_function(self):
        _assert_integer(_eval('let add = function(a, b) { a + b; }; add(3, 4);'), 7)

    def test_return_statement(self):
        _assert_integer(
            _eval('let f = function(x) { return x * 2; }; f(5);'),
            10
        )

    def test_early_return(self):
        code = '''
        let f = function(x) {
            if (x > 0) { return 1; }
            return -1;
        };
        f(5);
        '''
        _assert_integer(_eval(code), 1)

    def test_closure(self):
        code = '''
        let make_adder = function(n) {
            function(x) { x + n; }
        };
        let add5 = make_adder(5);
        add5(10);
        '''
        _assert_integer(_eval(code), 15)

    def test_recursion_factorial(self):
        code = '''
        let fact = function(n) {
            if (n <= 1) { return 1; }
            return n * fact(n - 1);
        };
        fact(10);
        '''
        _assert_integer(_eval(code), 3628800)

    def test_recursion_fibonacci(self):
        code = '''
        let fib = function(n) {
            if (n <= 1) { return n; }
            return fib(n - 1) + fib(n - 2);
        };
        fib(10);
        '''
        _assert_integer(_eval(code), 55)

    def test_wrong_arg_count(self):
        code = 'let f = function(a, b) { a + b; }; f(1);'
        _assert_error(_eval(code), 'argumentos')

    def test_call_non_function(self):
        _assert_error(_eval('let x = 5; x(1);'), 'no es una función')


class TestErrors(unittest.TestCase):
    """Propagación correcta de errores."""

    def test_type_mismatch(self):
        _assert_error(_eval('true + 5;'), 'incompatibles')

    def test_unknown_prefix(self):
        # El parser no generaría esto en condiciones normales,
        # pero el evaluador lo maneja
        result = _eval('!5;')
        # ! sobre entero → false (no es error, sino falsy)
        _assert_bool(result, False)

    def test_error_in_condition(self):
        # Error dentro del if
        code = 'if (1 + true) { 5; }'
        _assert_error(_eval(code))

    def test_error_in_let(self):
        _assert_error(_eval('let x = 5 / 0;'), 'cero')


if __name__ == '__main__':
    unittest.main(verbosity=2)
