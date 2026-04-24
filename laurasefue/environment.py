# =============================================================================
# environment.py — Entorno de Variables (Memoria del Intérprete)
#
# El Environment (entorno) es la estructura que almacena los valores de las
# variables durante la ejecución del programa. Funciona como una tabla de
# símbolos dinámica.
#
# Soporte de SCOPES (alcances):
#   Cada vez que se llama a una función se crea un entorno nuevo ("inner")
#   que apunta al entorno en el que se definió la función ("outer").
#   Al buscar una variable, primero se busca en el entorno actual; si no se
#   encuentra, se busca recursivamente en el entorno externo.
#
#   Esto implementa el alcance léxico (lexical scoping / closures).
#
# Ejemplo:
#   global_env  →  { x: 10 }
#   func_env    →  { y: 5, __outer__: global_env }
#   Dentro de func_env: get('x') → 10  (encontrado en global_env)
# =============================================================================

from typing import Dict, Optional
from laurasefue.object_system import Object


class Environment:
    """
    Entorno de ejecución: almacena el binding nombre → valor.

    Parámetro `outer`:
      Si se proporciona, este entorno es un entorno hijo (scope anidado).
      Las búsquedas que fallen en este entorno se delegan al outer.
    """

    def __init__(self, outer: Optional['Environment'] = None) -> None:
        # Tabla de símbolos: nombre de variable → objeto del lenguaje
        self._store: Dict[str, Object] = {}

        # Referencia al entorno externo (None si es el entorno global)
        self._outer = outer

    # ─── Lectura ──────────────────────────────────────────────────────────────

    def get(self, name: str) -> Optional[Object]:
        """
        Busca el valor de una variable por nombre.

        Primero busca en este entorno; si no lo encuentra y tiene un entorno
        externo (outer), delega la búsqueda hacia afuera (lexical scoping).

        Retorna None si la variable no existe en ningún entorno de la cadena.
        """
        value = self._store.get(name)
        if value is None and self._outer is not None:
            value = self._outer.get(name)
        return value

    # ─── Escritura ────────────────────────────────────────────────────────────

    def set(self, name: str, value: Object) -> Object:
        """
        Define o actualiza una variable en ESTE entorno (no en el outer).

        Esto es coherente con la semántica de `let`: cada `let` declara
        una variable nueva en el scope actual, sin modificar scopes externos.

        Retorna el valor asignado (conveniente para encadenar llamadas).
        """
        self._store[name] = value
        return value

    # ─── Representación (debug) ───────────────────────────────────────────────

    def __repr__(self) -> str:
        items = ', '.join(f'{k}={v.inspect()}' for k, v in self._store.items())
        return f'Environment({{{items}}})'


def new_enclosed_environment(outer: Environment) -> Environment:
    """
    Crea un nuevo entorno hijo que hereda del entorno dado.

    Usar al entrar a la ejecución de una función para crear un scope
    aislado que aun tiene acceso al entorno léxico exterior.
    """
    return Environment(outer=outer)
