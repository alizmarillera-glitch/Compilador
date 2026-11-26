"""
Nodos del árbol sintáctico abstracto (AST).

El analizador sintáctico construye estos nodos; el analizador semántico los
recorre para comprobar tipos (y les agrega `tipo` y `simbolo`); el generador
de código los recorre para producir las instrucciones.
"""
from dataclasses import dataclass, fields, is_dataclass


# ---------------------------------------------------------------- sentencias
@dataclass
class Programa:
    sentencias: list


@dataclass
class Bloque:
    sentencias: list


@dataclass
class Declaracion:
    nombre: str
    tipo_declarado: str
    valor: object
    linea: int = 0
    columna: int = 0
    simbolo: object = None  # lo llena el análisis semántico


@dataclass
class Asignacion:
    nombre: str
    valor: object
    linea: int = 0
    columna: int = 0
    simbolo: object = None


@dataclass
class Si:
    condicion: object
    entonces: object  # Bloque
    sino: object = None  # Bloque, otro Si (sino si) o None
    linea: int = 0
    columna: int = 0


@dataclass
class Mientras:
    condicion: object
    cuerpo: object  # Bloque
    linea: int = 0
    columna: int = 0


@dataclass
class Escribir:
    expresion: object
    linea: int = 0
    columna: int = 0


# --------------------------------------------------------------- expresiones
@dataclass
class Literal:
    valor: object
    tipo: str  # entero, decimal, cadena o booleano
    linea: int = 0
    columna: int = 0


@dataclass
class Variable:
    nombre: str
    linea: int = 0
    columna: int = 0
    tipo: object = None
    simbolo: object = None


@dataclass
class Unaria:
    op: str
    operando: object
    linea: int = 0
    columna: int = 0
    tipo: object = None


@dataclass
class Binaria:
    op: str
    izq: object
    der: object
    linea: int = 0
    columna: int = 0
    tipo: object = None


# ------------------------------------------------------------------ utilidad
def volcar(nodo, sangria=0):
    """Devuelve el árbol como texto indentado (útil para depurar y mostrar)."""
    pad = "  " * sangria
    if isinstance(nodo, list):
        return "".join(volcar(n, sangria) for n in nodo)
    if not is_dataclass(nodo):
        return f"{pad}{nodo!r}\n"

    simples, hijos = [], []
    for campo in fields(nodo):
        if campo.name in ("linea", "columna", "simbolo"):
            continue
        valor = getattr(nodo, campo.name)
        if is_dataclass(valor) or isinstance(valor, list):
            hijos.append((campo.name, valor))
        elif valor is not None:
            simples.append(f"{campo.name}={valor!r}")

    texto = pad + type(nodo).__name__
    if simples:
        texto += "(" + ", ".join(simples) + ")"
    texto += "\n"
    for nombre, hijo in hijos:
        texto += f"{pad}  {nombre}:\n" + volcar(hijo, sangria + 2)
    return texto
