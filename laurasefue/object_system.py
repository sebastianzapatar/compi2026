# =============================================================================
# object_system.py — Sistema de Objetos en Tiempo de Ejecución
#
# Cuando el Evaluador recorre el AST, cada expresión produce un "Object".
# Este módulo define todos los tipos de valores que el lenguaje puede manejar
# en tiempo de ejecución (runtime):
#
#   Integer     → 42, -7, 0
#   Float       → 3.14, -0.5
#   Boolean     → true, false
#   String      → "hola mundo"
#   Null        → ausencia de valor
#   ReturnValue → envuelve un valor para propagar un 'return'
#   Error       → encapsula un mensaje de error de ejecución
#   Function    → una función con parámetros, cuerpo y entorno de cierre
#
# Todos los objetos del lenguaje heredan de la clase abstracta `Object`.
# =============================================================================

from abc import ABC, abstractmethod
from enum import Enum, auto, unique
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from laurasefue.ast import Identifier, BlockStatement
    from laurasefue.environment import Environment


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE OBJETO
# ─────────────────────────────────────────────────────────────────────────────

@unique
class ObjectType(Enum):
    """Categorías de valores del lenguaje en tiempo de ejecución."""
    INTEGER  = auto()
    FLOAT    = auto()
    BOOLEAN  = auto()
    STRING   = auto()
    NULL     = auto()
    RETURN   = auto()   # Señal de control: propagar un `return`
    ERROR    = auto()   # Señal de error de ejecución
    FUNCTION = auto()   # Objeto función (closure)
    BREAK    = auto()   # Señal de control: `break` dentro de un bucle
    CONTINUE = auto()   # Señal de control: `continue` dentro de un bucle


# ─────────────────────────────────────────────────────────────────────────────
# CLASE BASE
# ─────────────────────────────────────────────────────────────────────────────

class Object(ABC):
    """
    Clase base abstracta para todos los valores del lenguaje.

    Cada subclase representa un tipo de dato concreto.
    """

    @property
    @abstractmethod
    def type(self) -> ObjectType:
        """Retorna el tipo de este objeto."""
        pass

    @abstractmethod
    def inspect(self) -> str:
        """Representación legible del valor (para imprimir en el REPL)."""
        pass

    def __str__(self) -> str:
        return self.inspect()


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS CONCRETOS
# ─────────────────────────────────────────────────────────────────────────────

class Integer(Object):
    """
    Valor entero del lenguaje.

    Ejemplo:  42,  -7,  0
    Internamente usa int de Python.
    """

    def __init__(self, value: int) -> None:
        self.value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.INTEGER

    def inspect(self) -> str:
        return str(self.value)


class Float(Object):
    """
    Valor decimal (punto flotante) del lenguaje.

    Ejemplo:  3.14,  -0.5,  2.0
    Internamente usa float de Python.
    """

    def __init__(self, value: float) -> None:
        self.value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.FLOAT

    def inspect(self) -> str:
        # Mostrar sin notación científica cuando sea posible
        formatted = f'{self.value:g}'
        # Si no tiene punto decimal, agregar '.0' para distinguir de entero
        if '.' not in formatted and 'e' not in formatted:
            formatted += '.0'
        return formatted


class Boolean(Object):
    """
    Valor booleano del lenguaje: true o false.

    Para optimizar, el evaluador reutiliza dos singletons globales
    (TRUE y FALSE) en lugar de crear un objeto nuevo por cada booleano.
    """

    def __init__(self, value: bool) -> None:
        self.value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.BOOLEAN

    def inspect(self) -> str:
        return 'true' if self.value else 'false'


class String(Object):
    """
    Valor de cadena de texto del lenguaje.

    Ejemplo:  "hola mundo",  "resultado: "
    Internamente usa str de Python.
    """

    def __init__(self, value: str) -> None:
        self.value = value

    @property
    def type(self) -> ObjectType:
        return ObjectType.STRING

    def inspect(self) -> str:
        return self.value


class Null(Object):
    """
    Representa la ausencia de valor (null).

    El evaluador retorna este objeto cuando una expresión no produce valor,
    por ejemplo un if sin else cuya condición es falsa.
    """

    @property
    def type(self) -> ObjectType:
        return ObjectType.NULL

    def inspect(self) -> str:
        return 'null'


class ReturnValue(Object):
    """
    Señal de control para propagar un `return` a través del call stack.

    Envuelve el valor real que se retorna. El evaluador lo desenvuelve
    al salir de la función.
    """

    def __init__(self, value: Object) -> None:
        self.value = value      # El objeto real que se va a retornar

    @property
    def type(self) -> ObjectType:
        return ObjectType.RETURN

    def inspect(self) -> str:
        return self.value.inspect()


class Error(Object):
    """
    Representa un error en tiempo de ejecución.

    El evaluador propaga el error hacia arriba del call stack hasta que
    alguien lo maneje, de forma similar a como ReturnValue propaga return.
    """

    def __init__(self, message: str) -> None:
        self.message = message      # Descripción del error

    @property
    def type(self) -> ObjectType:
        return ObjectType.ERROR

    def inspect(self) -> str:
        return f'ERROR: {self.message}'


class Function(Object):
    """
    Objeto función (closure) del lenguaje.

    Guarda los parámetros, el cuerpo y el entorno léxico en el que
    fue definida. Esto permite funciones de primera clase y closures.
    """

    def __init__(
        self,
        parameters: List['Identifier'],
        body: 'BlockStatement',
        env: 'Environment',
        name: str = ''
    ) -> None:
        self.parameters = parameters    # Lista de Identifier (parámetros formales)
        self.body = body                # BlockStatement con el código de la función
        self.env = env                  # Entorno léxico en el momento de la definición
        self.name = name                # Nombre (si fue asignada con let)

    @property
    def type(self) -> ObjectType:
        return ObjectType.FUNCTION

    def inspect(self) -> str:
        params = ', '.join(str(p) for p in self.parameters)
        name_str = f' {self.name}' if self.name else ''
        return f'function{name_str}({params}) {{ ... }}'


class BreakSignal(Object):
    """
    Señal de control interna para propagar un `break` desde el cuerpo
    de un bucle hasta el manejador de while/for.

    No es un valor visible para el usuario.
    """

    @property
    def type(self) -> ObjectType:
        return ObjectType.BREAK

    def inspect(self) -> str:
        return 'break'


class ContinueSignal(Object):
    """
    Señal de control interna para propagar un `continue` desde el cuerpo
    de un bucle hasta el manejador de while/for.

    No es un valor visible para el usuario.
    """

    @property
    def type(self) -> ObjectType:
        return ObjectType.CONTINUE

    def inspect(self) -> str:
        return 'continue'


# ─────────────────────────────────────────────────────────────────────────────
# SINGLETONS GLOBALES
# ─────────────────────────────────────────────────────────────────────────────

# Singleton para true: evita crear un nuevo objeto Boolean en cada evaluación
TRUE = Boolean(True)

# Singleton para false
FALSE = Boolean(False)

# Singleton para null
NULL = Null()

# Singleton para break (señal de control)
BREAK_SIGNAL = BreakSignal()

# Singleton para continue (señal de control)
CONTINUE_SIGNAL = ContinueSignal()
