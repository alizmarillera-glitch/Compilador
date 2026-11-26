"""
Compilador Mini - punto de entrada.

Uso:
    python main.py programa.mini                 compila y ejecuta
    python main.py programa.mini --tokens        muestra los tokens (fase léxica)
    python main.py programa.mini --ast           muestra el árbol con tipos (fases sintáctica y semántica)
    python main.py programa.mini --bytecode      muestra el bytecode generado
    python main.py programa.mini --no-ejecutar   solo compila (no ejecuta)
"""
import argparse
import sys

from analizador_lexico import ErrorLexico, Lexer
from analizador_semantico import AnalizadorSemantico, ErrorSemantico
from analizador_sintactico import ErrorSintactico, Parser
from generador_codigo import GeneradorCodigo, formatear_codigo
from maquina_virtual import ErrorEjecucion, MaquinaVirtual
from nodos import volcar


def compilar(codigo):
    """Pasa el código fuente por todas las fases y devuelve el bytecode."""
    tokens = Lexer(codigo).tokenizar()
    arbol = Parser(tokens).parsear()
    AnalizadorSemantico().analizar(arbol)
    return GeneradorCodigo().generar(arbol)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Compilador Mini: compila y ejecuta archivos .mini")
    ap.add_argument("archivo", help="archivo de código fuente (.mini)")
    ap.add_argument("--tokens", action="store_true", help="muestra los tokens")
    ap.add_argument("--ast", action="store_true", help="muestra el árbol sintáctico con tipos")
    ap.add_argument("--bytecode", action="store_true", help="muestra el bytecode generado")
    ap.add_argument("--no-ejecutar", action="store_true", help="solo compila, no ejecuta")
    args = ap.parse_args(argv)

    try:
        # utf-8-sig tolera el BOM que a veces agrega el Bloc de notas de Windows
        with open(args.archivo, encoding="utf-8-sig") as f:
            codigo = f.read()
    except OSError as e:
        print(f"No se pudo abrir '{args.archivo}': {e}", file=sys.stderr)
        return 1

    try:
        tokens = Lexer(codigo).tokenizar()
        if args.tokens:
            print("=== TOKENS ===")
            for token in tokens:
                print(token)

        arbol = Parser(tokens).parsear()
        AnalizadorSemantico().analizar(arbol)
        if args.ast:
            print("=== AST (con tipos) ===")
            print(volcar(arbol), end="")

        bytecode = GeneradorCodigo().generar(arbol)
        if args.bytecode:
            print("=== BYTECODE ===")
            print(formatear_codigo(bytecode))

        if not args.no_ejecutar:
            if args.tokens or args.ast or args.bytecode:
                print("=== SALIDA ===")
            MaquinaVirtual(bytecode).ejecutar()
    except (ErrorLexico, ErrorSintactico, ErrorSemantico, ErrorEjecucion) as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
