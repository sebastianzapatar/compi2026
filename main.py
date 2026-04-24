import sys
import os
from laurasefue.repl import start_repl
from laurasefue.lexer import Lexer
from laurasefue.parser import Parser
from laurasefue.evaluator import evaluate
from laurasefue.environment import Environment
from laurasefue.object_system import ObjectType, NULL

def run_file(filepath: str) -> None:
    """Lee y evalúa un archivo de código fuente de LauraSeFue."""
    if not os.path.exists(filepath):
        print(f"Error: El archivo '{filepath}' no existe.")
        sys.exit(1)
        
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
        
    lexer = Lexer(source)
    parser = Parser(lexer)
    program = parser.parse_program()
    
    if parser.errors:
        print("Errores de parseo:")
        for error in parser.errors:
            print(f"  ✗ {error}")
        sys.exit(1)
        
    env = Environment()
    result = evaluate(program, env)
    
    # Si hubo un error en tiempo de ejecución, imprimirlo
    if result is not None and result.type == ObjectType.ERROR:
        print(f"Error en ejecución: {result.inspect()}")
        sys.exit(1)
        
    # Opcional: imprimir el resultado final si no es nulo
    if result is not None and result is not NULL and result.type != ObjectType.NULL:
        print(result.inspect())

def main() -> None:
    """Punto de entrada principal."""
    # Si se pasa un argumento, intentar leerlo como archivo
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        run_file(filepath)
    else:
        # Si no hay argumentos, iniciar el REPL interactivo
        print("Laura se fue Laura no esta :'(")
        start_repl()

if __name__ == "__main__":
    main()