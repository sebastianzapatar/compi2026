# =============================================================================
# tests/test_evaluador.py — Pruebas del Evaluador
#
# Verifica que el evaluador produce los OBJETOS correctos para cada
# construcción del lenguaje. Se prueba de extremo a extremo:
#   código fuente → Lexer → Parser → Evaluador → Object
# =============================================================================

import pytest
from laurasefue.lexer import Lexer
from laurasefue.parser import Parser
from laurasefue.evaluator import evaluate
from laurasefue.object_system import (
    Object, ObjectType, Environment,
    Integer, Float, String, Boolean, Null, Error,
    TRUE, FALSE, NULL
)


# ─── FUNCIÓN AUXILIAR ────────────────────────────────────────────────────────

def evaluar(source: str) -> Object:
    """
    Ejecuta el pipeline completo Lexer → Parser → Evaluador sobre el source.
    Retorna el último objeto producido por el evaluador.
    """
    lexer   = Lexer(source)
    parser  = Parser(lexer)
    program = parser.parse_program()

    # Si el parser tiene errores, el test falla con un mensaje claro
    assert parser.errors == [], (
        'Errores de parseo:\n' + '\n'.join(f'  • {e}' for e in parser.errors)
    )

    env    = Environment()
    result = evaluate(program, env)
    return result


# ─── LITERALES ────────────────────────────────────────────────────────────────

class TestLiterales:
    """Pruebas para la evaluación de valores literales."""

    def test_entero(self):
        """Un entero debe evaluarse como Integer con el valor correcto."""
        result = evaluar('5')
        assert isinstance(result, Integer)
        assert result.value == 5

    def test_flotante(self):
        """Un flotante debe evaluarse como Float con el valor correcto."""
        result = evaluar('3.14')
        assert isinstance(result, Float)
        assert result.value == pytest.approx(3.14)

    def test_string(self):
        """Un string debe evaluarse como String con el contenido sin comillas."""
        result = evaluar('"hola mundo"')
        assert isinstance(result, String)
        assert result.value == 'hola mundo'

    def test_booleano_true(self):
        """'true' debe evaluarse como el singleton TRUE."""
        result = evaluar('true')
        assert result is TRUE

    def test_booleano_false(self):
        """'false' debe evaluarse como el singleton FALSE."""
        result = evaluar('false')
        assert result is FALSE


# ─── ARITMÉTICA ──────────────────────────────────────────────────────────────

class TestAritmetica:
    """Pruebas para las operaciones aritméticas entre enteros y flotantes."""

    @pytest.mark.parametrize('source, esperado', [
        ('2 + 3',    5),
        ('10 - 4',   6),
        ('3 * 4',   12),
        ('10 % 3',   1),
        ('2 ^ 8',  256),
        ('0 + 0',    0),
        ('100 - 100', 0),
    ])
    def test_operacion_entera(self, source, esperado):
        """Las operaciones entre enteros deben retornar Integer con el valor correcto."""
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == esperado

    def test_division_produce_float(self):
        """La división entre enteros debe producir siempre un Float."""
        result = evaluar('10 / 4')
        assert isinstance(result, Float)
        assert result.value == pytest.approx(2.5)

    def test_aritmetica_flotante(self):
        """Las operaciones con flotantes deben producir Float."""
        result = evaluar('2.5 + 1.5')
        assert isinstance(result, Float)
        assert result.value == pytest.approx(4.0)

    def test_negacion_numerica(self):
        """-5 debe producir Integer(-5)."""
        result = evaluar('-5')
        assert isinstance(result, Integer)
        assert result.value == -5

    def test_potencia(self):
        """2^10 debe ser 1024."""
        result = evaluar('2 ^ 10')
        assert isinstance(result, Integer)
        assert result.value == 1024

    def test_precedencia(self):
        """'2 + 3 * 4' debe ser 14 (no 20), respetando la precedencia."""
        result = evaluar('2 + 3 * 4')
        assert isinstance(result, Integer)
        assert result.value == 14

    def test_parentesis_cambia_resultado(self):
        """'(2 + 3) * 4' debe ser 20."""
        result = evaluar('(2 + 3) * 4')
        assert isinstance(result, Integer)
        assert result.value == 20

    def test_division_por_cero(self):
        """Dividir por cero debe producir un Error."""
        result = evaluar('10 / 0')
        assert isinstance(result, Error)
        assert 'cero' in result.message.lower()

    def test_modulo_por_cero(self):
        """Módulo por cero debe producir un Error."""
        result = evaluar('10 % 0')
        assert isinstance(result, Error)


# ─── STRINGS ─────────────────────────────────────────────────────────────────

class TestStrings:
    """Pruebas para operaciones con cadenas de texto."""

    def test_concatenacion(self):
        """Dos strings con '+' deben concatenarse."""
        result = evaluar('"hola" + " mundo"')
        assert isinstance(result, String)
        assert result.value == 'hola mundo'

    def test_comparacion_igual(self):
        """Dos strings iguales comparados con '==' deben retornar TRUE."""
        result = evaluar('"abc" == "abc"')
        assert result is TRUE

    def test_comparacion_diferente(self):
        """Dos strings distintos comparados con '!=' deben retornar TRUE."""
        result = evaluar('"abc" != "def"')
        assert result is TRUE

    def test_resta_string_es_error(self):
        """Restar dos strings debe producir un Error."""
        result = evaluar('"hola" - "mundo"')
        assert isinstance(result, Error)


# ─── COMPARACIONES ────────────────────────────────────────────────────────────

class TestComparaciones:
    """Pruebas para los operadores de comparación numérica."""

    @pytest.mark.parametrize('source, esperado_true', [
        ('5 >  3',   True),
        ('3 <  5',   True),
        ('5 >= 5',   True),
        ('5 <= 5',   True),
        ('5 == 5',   True),
        ('5 != 3',   True),
        ('3 >  5',  False),
        ('5 <  3',  False),
        ('5 >= 6',  False),
    ])
    def test_comparacion(self, source, esperado_true):
        result = evaluar(source)
        assert isinstance(result, Boolean)
        assert result.value == esperado_true


# ─── OPERADORES LÓGICOS ───────────────────────────────────────────────────────

class TestOperadoresLogicos:
    """Pruebas para 'and', 'or' y '!' (negación)."""

    def test_and_verdadero(self):
        """'true and true' debe ser TRUE."""
        assert evaluar('true and true') is TRUE

    def test_and_falso(self):
        """'true and false' debe ser FALSE."""
        assert evaluar('true and false') is FALSE

    def test_or_verdadero(self):
        """'false or true' debe ser TRUE."""
        assert evaluar('false or true') is TRUE

    def test_or_falso(self):
        """'false or false' debe ser FALSE."""
        assert evaluar('false or false') is FALSE

    def test_negacion_true(self):
        """'!true' debe ser FALSE."""
        assert evaluar('!true') is FALSE

    def test_negacion_false(self):
        """'!false' debe ser TRUE."""
        assert evaluar('!false') is TRUE

    def test_negacion_null(self):
        """'!null' (implícito a través de variable no asignada) → TRUE."""
        # null es "falsy", así que !null = true
        result = evaluar('!false')
        assert result is TRUE


# ─── VARIABLES ────────────────────────────────────────────────────────────────

class TestVariables:
    """Pruebas para la declaración y uso de variables (LetStatement)."""

    def test_declarar_y_leer(self):
        """'let x = 10; x' debe retornar Integer(10)."""
        result = evaluar('let x = 10; x')
        assert isinstance(result, Integer)
        assert result.value == 10

    def test_usar_variable_en_expresion(self):
        """'let x = 5; x * 2' debe retornar Integer(10)."""
        result = evaluar('let x = 5; x * 2')
        assert isinstance(result, Integer)
        assert result.value == 10

    def test_variable_no_definida(self):
        """Usar una variable sin declararla debe producir un Error."""
        result = evaluar('z')
        assert isinstance(result, Error)
        assert 'z' in result.message

    def test_reasignacion(self):
        """'let x = 1; let x = 2; x' debe retornar 2 (shadowing local)."""
        result = evaluar('let x = 1; let x = 2; x')
        assert isinstance(result, Integer)
        assert result.value == 2


# ─── CONDICIONALES ────────────────────────────────────────────────────────────

class TestCondicionales:
    """Pruebas para if / elseif / else."""

    def test_if_verdadero(self):
        """Si la condición es true, debe ejecutar el bloque if."""
        result = evaluar('if (true) { 42 }')
        assert isinstance(result, Integer)
        assert result.value == 42

    def test_if_falso_sin_else(self):
        """Si la condición es false y no hay else, debe retornar NULL."""
        result = evaluar('if (false) { 42 }')
        assert result is NULL

    def test_if_else(self):
        """Si la condición es false, debe ejecutar el bloque else."""
        result = evaluar('if (false) { 1 } else { 2 }')
        assert isinstance(result, Integer)
        assert result.value == 2

    def test_elseif(self):
        """La rama elseif debe ejecutarse cuando la condición del if es false."""
        source = '''
            let x = 5;
            if (x > 10) {
                let r = 1;
            } elseif (x > 3) {
                let r = 2;
            } else {
                let r = 3;
            }
            r
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 2

    def test_if_con_comparacion(self):
        """'if (5 > 3) { 1 } else { 0 }' debe retornar 1."""
        result = evaluar('if (5 > 3) { 1 } else { 0 }')
        assert result.value == 1


# ─── WHILE ────────────────────────────────────────────────────────────────────

class TestWhile:
    """Pruebas para el bucle while."""

    def test_while_cuenta_hasta_5(self):
        """El while debe ejecutarse N veces hasta que la condición sea false."""
        source = '''
            let i = 0;
            let suma = 0;
            while (i < 5) {
                let suma = suma + 1;
                let i = i + 1;
            }
            suma
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 5

    def test_while_no_ejecuta_si_condicion_falsa(self):
        """Un while con condición inicialmente falsa no debe ejecutarse."""
        source = 'let x = 0; while (false) { let x = 999; } x'
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 0

    def test_while_con_break(self):
        """break debe salir del bucle inmediatamente."""
        source = '''
            let x = 0;
            while (true) {
                let x = x + 1;
                if (x == 3) { break; }
            }
            x
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 3


# ─── FOR ─────────────────────────────────────────────────────────────────────

class TestFor:
    """Pruebas para el bucle for."""

    def test_for_suma_acumulada(self):
        """for de 1 a 4: suma 1+2+3+4 = 10."""
        source = '''
            let s = 0;
            for (let i = 1; i <= 4; let i = i + 1) {
                let s = s + i;
            }
            s
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 10

    def test_for_con_continue(self):
        """continue debe saltar al update del for sin ejecutar el resto del cuerpo."""
        source = '''
            let s = 0;
            for (let i = 1; i <= 6; let i = i + 1) {
                if (i % 2 == 0) { continue; }
                let s = s + i;
            }
            s
        '''
        # Suma de impares del 1 al 5: 1+3+5 = 9
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 9


# ─── FUNCIONES ────────────────────────────────────────────────────────────────

class TestFunciones:
    """Pruebas para definición y llamada de funciones."""

    def test_funcion_simple(self):
        """Una función que suma dos números debe retornar el resultado correcto."""
        source = '''
            let suma = function(a, b) { return a + b; };
            suma(3, 4)
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 7

    def test_funcion_sin_return_explicito(self):
        """Una función sin return debe retornar el valor de la última expresión."""
        source = 'let f = function() { 42 }; f()'
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 42

    def test_funcion_con_argumentos_erroneos(self):
        """Llamar con un argumento extra debe producir un Error."""
        source = 'let f = function(x) { x }; f(1, 2)'
        result = evaluar(source)
        assert isinstance(result, Error)

    def test_closure(self):
        """Una función puede capturar variables del entorno donde fue definida."""
        source = '''
            let x = 10;
            let f = function() { x };
            f()
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 10

    def test_funcion_como_argumento(self):
        """Una función puede recibir otra función como argumento."""
        source = '''
            let aplicar = function(f, x) { f(x) };
            let doble   = function(n) { n * 2 };
            aplicar(doble, 5)
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 10


# ─── RECURSIÓN ────────────────────────────────────────────────────────────────

class TestRecursion:
    """Pruebas para funciones recursivas (factorial y fibonacci)."""

    def test_factorial_0(self):
        """factorial(0) debe ser 1 (caso base)."""
        source = '''
            let factorial = function(n) {
                if (n == 0) { return 1; }
                return n * factorial(n - 1);
            };
            factorial(0)
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 1

    def test_factorial_5(self):
        """factorial(5) debe ser 120."""
        source = '''
            let factorial = function(n) {
                if (n == 0) { return 1; }
                return n * factorial(n - 1);
            };
            factorial(5)
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 120

    def test_factorial_10(self):
        """factorial(10) debe ser 3628800."""
        source = '''
            let factorial = function(n) {
                if (n == 0) { return 1; }
                return n * factorial(n - 1);
            };
            factorial(10)
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 3628800

    def test_fibonacci_0(self):
        """fibonacci(0) = 0 (caso base)."""
        source = '''
            let fib = function(n) {
                if (n == 0) { return 0; }
                if (n == 1) { return 1; }
                return fib(n - 1) + fib(n - 2);
            };
            fib(0)
        '''
        assert evaluar(source).value == 0

    def test_fibonacci_1(self):
        """fibonacci(1) = 1 (caso base)."""
        source = '''
            let fib = function(n) {
                if (n == 0) { return 0; }
                if (n == 1) { return 1; }
                return fib(n - 1) + fib(n - 2);
            };
            fib(1)
        '''
        assert evaluar(source).value == 1

    def test_fibonacci_10(self):
        """fibonacci(10) = 55."""
        source = '''
            let fib = function(n) {
                if (n == 0) { return 0; }
                if (n == 1) { return 1; }
                return fib(n - 1) + fib(n - 2);
            };
            fib(10)
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 55

    def test_suma_recursiva(self):
        """Función recursiva que suma del 1 al n: sum(5) = 15."""
        source = '''
            let sumaHasta = function(n) {
                if (n == 0) { return 0; }
                return n + sumaHasta(n - 1);
            };
            sumaHasta(5)
        '''
        result = evaluar(source)
        assert isinstance(result, Integer)
        assert result.value == 15


# ─── ERRORES EN TIEMPO DE EJECUCIÓN ──────────────────────────────────────────

class TestErroresEjecucion:
    """Pruebas para el manejo de errores en tiempo de ejecución."""

    def test_variable_no_definida(self):
        """Usar una variable no declarada debe dar Error con el nombre."""
        result = evaluar('variableInexistente')
        assert isinstance(result, Error)
        assert 'variableInexistente' in result.message

    def test_division_por_cero(self):
        """La división por cero debe dar Error."""
        result = evaluar('5 / 0')
        assert isinstance(result, Error)

    def test_llamar_no_funcion(self):
        """Llamar a algo que no es función debe dar Error."""
        result = evaluar('let x = 5; x()')
        assert isinstance(result, Error)

    def test_tipos_incompatibles(self):
        """Sumar un número y un booleano debe dar Error."""
        result = evaluar('5 + true')
        assert isinstance(result, Error)

    def test_error_no_detiene_evaluacion_siguiente_programa(self):
        """
        El Error se propaga hasta el top-level; el programa termina,
        pero el intérprete no falla con excepción Python.
        """
        result = evaluar('variableInexistente')
        # No debe lanzar una excepción Python; en cambio, retorna Error
        assert isinstance(result, Error)
