# =============================================================================
# object_system.py — Sistema de Objetos en Tiempo de Ejecución
#
# Cuando el Evaluador procesa el AST, produce OBJETOS. Cada valor del
# lenguaje (un número, un string, una función, etc.) es representado
# como una instancia de una de las clases definidas aquí.
#
# Jerarquía:
#   Object (abstracta)
#   ├── Integer       ← 42
#   ├── Float         ← 3.14
#   ├── String        ← "hola"
#   ├── Boolean       ← true / false
#   ├── Null          ← ausencia de valor
#   ├── ReturnValue   ← wrapper para propagar 'return' por el call-stack
#   ├── Error         ← errores en tiempo de ejecución
#   └── Function      ← closure (función + entorno capturado)
#
# También se define Environment: el entorno (tabla de símbolos) que
# relaciona nombres de variables con sus valores actuales.
# =============================================================================

from abc import ABC, abstractmethod  # Para clases abstractas
from enum import auto, Enum, unique  # Para el enum de tipos de objeto
from typing import Dict, List, Optional  # Tipos genéricos

# Importación tardía para evitar dependencia circular con ast.py
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from laurasefue.ast import Identifier, BlockStatement


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE OBJETO
# ─────────────────────────────────────────────────────────────────────────────

@unique
class ObjectType(Enum):
    """
    Enumera los tipos de valores que puede producir el evaluador.
    Cada Object instanciado tiene un .object_type que es uno de estos.
    """
    INTEGER      = 'INTEGER'       # Número entero
    FLOAT        = 'FLOAT'         # Número decimal
    STRING       = 'STRING'        # Cadena de texto
    BOOLEAN      = 'BOOLEAN'       # Booleano (true/false)
    NULL         = 'NULL'          # Sin valor
    RETURN_VALUE = 'RETURN_VALUE'  # Envuelve un valor retornado con 'return'
    ERROR        = 'ERROR'         # Error en tiempo de ejecución
    FUNCTION     = 'FUNCTION'      # Objeto función (closure)


# ─────────────────────────────────────────────────────────────────────────────
# CLASE BASE
# ─────────────────────────────────────────────────────────────────────────────

class Object(ABC):
    """
    Clase base abstracta para todos los valores del lenguaje.

    Todo lo que el evaluador puede producir (número, string, función, etc.)
    es un Object. Esto permite que el evaluador maneje todos los valores
    de forma uniforme con tipado estático de Python.
    """

    @abstractmethod
    def object_type(self) -> ObjectType:
        """Retorna el tipo de objeto (ObjectType enum)."""
        pass

    @abstractmethod
    def inspect(self) -> str:
        """Retorna una representación legible del valor (para print y debug)."""
        pass

    def __str__(self) -> str:
        return self.inspect()


# ─────────────────────────────────────────────────────────────────────────────
# TIPOS DE DATO
# ─────────────────────────────────────────────────────────────────────────────

class Integer(Object):
    """
    Objeto que representa un número entero.

    Ejemplo de uso:  let x = 42;  → en tiempo de ejecución, x = Integer(42)
    """

    def __init__(self, value: int) -> None:
        self.value = value   # El valor Python int

    def object_type(self) -> ObjectType:
        return ObjectType.INTEGER

    def inspect(self) -> str:
        return str(self.value)


class Float(Object):
    """
    Objeto que representa un número de punto flotante.

    Ejemplo: let pi = 3.14;  → Float(3.14)
    """

    def __init__(self, value: float) -> None:
        self.value = value   # El valor Python float

    def object_type(self) -> ObjectType:
        return ObjectType.FLOAT

    def inspect(self) -> str:
        return str(self.value)


class String(Object):
    """
    Objeto que representa una cadena de texto.

    Ejemplo: let saludo = "hola";  → String("hola")
    Soporta concatenación con +.
    """

    def __init__(self, value: str) -> None:
        self.value = value   # El string Python

    def object_type(self) -> ObjectType:
        return ObjectType.STRING

    def inspect(self) -> str:
        return self.value


class Boolean(Object):
    """
    Objeto que representa un valor booleano: true o false.

    Para eficiencia, el evaluador reutiliza dos instancias globales
    (TRUE y FALSE definidas más abajo) en lugar de crear una nueva
    instancia cada vez que aparece true o false.
    """

    def __init__(self, value: bool) -> None:
        self.value = value   # El bool Python

    def object_type(self) -> ObjectType:
        return ObjectType.BOOLEAN

    def inspect(self) -> str:
        return 'true' if self.value else 'false'


class Null(Object):
    """
    Objeto que representa la ausencia de valor.

    Similar a None en Python o null en otros lenguajes.
    Se retorna cuando una función no tiene return explícito o
    cuando se accede a algo indefinido.
    """

    def object_type(self) -> ObjectType:
        return ObjectType.NULL

    def inspect(self) -> str:
        return 'null'


# ─────────────────────────────────────────────────────────────────────────────
# OBJETOS ESPECIALES DE CONTROL
# ─────────────────────────────────────────────────────────────────────────────

class ReturnValue(Object):
    """
    Objeto especial que ENVUELVE un valor retornado con 'return'.

    Problema que resuelve: cuando el evaluador encuentra un 'return expr;'
    dentro de un bloque de sentencias, necesita interrumpir la ejecución
    del bloque y propagar el valor hacia arriba por la pila de llamadas,
    hasta llegar a la invocación de función que corresponda.

    Para ello, en lugar de retornar el valor directamente, lo envolvemos
    en ReturnValue. El evaluador de bloques y de llamadas a funciones
    detecta ReturnValue y actúa en consecuencia:
      - BlockStatement: lo propaga hacia arriba sin seguir evaluando.
      - CallExpression: lo desenvuelve y extrae el .value.

    Ejemplo:
        function(n) {
            if (n == 0) {
                return 1;   ← produce ReturnValue(Integer(1))
            }                ← el bloque del if propaga ReturnValue
            return n * factorial(n - 1);  ← nunca se llega aquí si n==0
        }
    """

    def __init__(self, value: Object) -> None:
        self.value = value   # El valor real envuelto

    def object_type(self) -> ObjectType:
        return ObjectType.RETURN_VALUE

    def inspect(self) -> str:
        return self.value.inspect()


class Error(Object):
    """
    Objeto que representa un error en tiempo de ejecución.

    Cuando el evaluador detecta una operación inválida (división por cero,
    variable no definida, tipos incompatibles, etc.) crea un Error y
    lo propaga hacia arriba, deteniendo la evaluación del programa.

    Ejemplo de errores:
      - Usar una variable que no fue declarada: "variable no definida: z"
      - Dividir por cero: "división por cero"
      - Operación entre tipos incompatibles: "operación no soportada: STRING + INTEGER"
    """

    def __init__(self, message: str) -> None:
        self.message = message   # Descripción del error

    def object_type(self) -> ObjectType:
        return ObjectType.ERROR

    def inspect(self) -> str:
        return f'[ERROR] {self.message}'


class Function(Object):
    """
    Objeto que representa una FUNCIÓN en tiempo de ejecución.

    Almacena:
      - parameters: lista de Identifier (parámetros formales)
      - body:       BlockStatement (el cuerpo de la función)
      - env:        el Environment en que fue DEFINIDA (closure!)

    El entorno capturado (closure) es crucial para la recursión y para
    que las funciones anidadas puedan acceder a variables del ámbito padre.

    Ciclo de vida de una llamada a función:
      1. El evaluador evalúa FunctionLiteral → crea un objeto Function
         capturando el entorno actual.
      2. Al llamar la función (CallExpression), el evaluador:
         a. Crea un nuevo entorno extendido del entorno capturado.
         b. Enlaza cada parámetro formal con el argumento real.
         c. Evalúa el body en ese nuevo entorno.
         d. Desenvuelve el ReturnValue si existe.
      3. Con esto, la recursión funciona: la función puede llamarse a
         sí misma porque su nombre vive en el entorno donde fue definida.
    """

    def __init__(
        self,
        parameters: List['Identifier'],
        body: 'BlockStatement',
        env: 'Environment',
        name: str = ''
    ) -> None:
        self.parameters = parameters   # Lista de Identifier (parámetros)
        self.body = body               # BlockStatement (cuerpo)
        self.env = env                 # Entorno capturado (closure)
        self.name = name               # Nombre de la función (si tiene)

    def object_type(self) -> ObjectType:
        return ObjectType.FUNCTION

    def inspect(self) -> str:
        params = ', '.join(p.value for p in self.parameters)
        name_str = f' {self.name}' if self.name else ''
        return f'function{name_str}({params}) {{ ... }}'


# ─────────────────────────────────────────────────────────────────────────────
# ENTORNO (tabla de símbolos)
# ─────────────────────────────────────────────────────────────────────────────

class Environment:
    """
    Representa el entorno de ejecución: una tabla de variables → valores.

    Los entornos pueden estar ANIDADOS: cada llamada a función crea un
    entorno hijo que, cuando no encuentra una variable localmente, la
    busca en el entorno padre (outer).

    Esta cadena de entornos implementa el alcance léxico (lexical scoping)
    y permite la recursión y las clausuras (closures).

    Ejemplo de cadena de entornos para una función recursiva:
      entorno_global:  { factorial → Function }
                              ↑ outer
      entorno_local1:  { n → Integer(5) }   ← primera llamada
                              ↑ outer
      entorno_local2:  { n → Integer(4) }   ← llamada recursiva
    """

    def __init__(self, outer: Optional['Environment'] = None) -> None:
        # Tabla de símbolos local (nombre → valor)
        self._store: Dict[str, Object] = {}

        # Entorno padre; None si es el entorno global
        self._outer = outer

    def get(self, name: str) -> Optional[Object]:
        """
        Busca una variable por nombre.

        Primero busca en el entorno local; si no está, busca en el padre.
        Retorna None si no se encuentra en ningún nivel.
        """
        obj = self._store.get(name)
        if obj is None and self._outer is not None:
            return self._outer.get(name)
        return obj

    def set(self, name: str, value: Object) -> Object:
        """
        Asigna o actualiza una variable.

        Estrategia:
          1. Si la variable YA EXISTE en este entorno o en algún entorno padre,
             la actualiza en el entorno más cercano donde fue definida.
             Esto permite que 'let s = s + 1' dentro de un for actualice
             la 's' del entorno exterior (el que la declaró originalmente).
          2. Si la variable NO EXISTE en ningún nivel (es nueva), se crea
             en el entorno LOCAL actual.

        Esta semántica es importante para los bucles (for/while): si se
        declara 'let i = 0' antes del bucle y se hace 'let i = i + 1'
        dentro, se actualiza la misma 'i' exterior.
        """
        # Busca el entorno más cercano que ya tenga esta variable
        env = self._find_env(name)
        if env is not None:
            # La variable existe en algún nivel → actualizar allí
            env._store[name] = value
        else:
            # Variable nueva → crearla en el entorno local
            self._store[name] = value
        return value

    def _find_env(self, name: str) -> 'Optional[Environment]':
        """
        Busca el entorno más cercano (local → padre → abuelo → ...) que
        contenga la variable con el nombre dado.

        Retorna ese Environment, o None si no se encuentra en ningún nivel.
        """
        if name in self._store:
            return self
        if self._outer is not None:
            return self._outer._find_env(name)
        return None

    @classmethod
    def new_enclosed(cls, outer: 'Environment') -> 'Environment':
        """
        Crea un nuevo entorno hijo que encadena con el padre dado.

        Se usa cada vez que se llama a una función: el nuevo entorno
        tendrá acceso a las variables del padre, pero sus propias
        variables no "contaminarán" el entorno padre.
        """
        env = cls(outer=outer)
        return env


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES GLOBALES (singletons para rendimiento)
# ─────────────────────────────────────────────────────────────────────────────

# En lugar de crear un nuevo Boolean cada vez, reutilizamos estas instancias.
# El evaluador las retorna directamente cuando ve true o false.
TRUE  = Boolean(True)
FALSE = Boolean(False)
NULL  = Null()
