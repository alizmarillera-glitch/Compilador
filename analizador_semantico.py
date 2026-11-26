"""
Fase 3 - Análisis semántico.

Una frase puede ser gramaticalmente correcta y aun así no tener sentido.
Aquí se comprueba el significado del programa:

  * toda variable se declara antes de usarse y no se declara dos veces en el
    mismo ámbito (cada bloque { } abre un ámbito nuevo);
  * los tipos son compatibles en declaraciones, asignaciones y operaciones;
  * las condiciones de `si` y `mientras` son booleanas;
  * no hay división entre cero evidente (literal 0).

Además "anota" el árbol: cada expresión recibe su `tipo` y cada uso de variable
queda enlazado a su `Simbolo` (tabla de símbolos), que el generador de código
usa para asignar la posición de memoria.
"""
from dataclasses import dataclass

from nodos import (Asignacion, Binaria, Bloque, Declaracion, Escribir, Literal,
                   Mientras, Si, Unaria, Variable)

NUMERICOS = ("entero", "decimal")


@dataclass
class Simbolo:
    nombre: str
    tipo: str
    id: int  # identificador único (posición en memoria de la máquina virtual)
    linea: int


class ErrorSemantico(Exception):
    def __init__(self, errores):
        self.errores = errores
        super().__init__("\n".join(errores))


class AnalizadorSemantico:
    def __init__(self):
        self.ambitos = [{}]  # pila de tablas de símbolos
        self.errores = []
        self.contador = 0

    def analizar(self, programa):
        for sentencia in programa.sentencias:
            self._sentencia(sentencia)
        if self.errores:
            raise ErrorSemantico(self.errores)
        return programa

    # -- utilidades
    def _error(self, nodo, mensaje):
        self.errores.append(
            f"Error semántico (línea {nodo.linea}, columna {nodo.columna}): {mensaje}")

    def _buscar(self, nombre):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    @staticmethod
    def _compatible(destino, origen):
        # "error" evita encadenar mensajes cuando ya se reportó un problema.
        return origen == "error" or destino == origen or (destino == "decimal" and origen == "entero")

    # -- sentencias
    def _sentencia(self, n):
        if isinstance(n, Declaracion):
            # Se analiza el valor antes de declarar: `var x: entero = x;` es un error.
            tipo_valor = self._expr(n.valor)
            if n.nombre in self.ambitos[-1]:
                previo = self.ambitos[-1][n.nombre]
                self._error(n, f"la variable '{n.nombre}' ya fue declarada en este ámbito "
                               f"(línea {previo.linea})")
            else:
                simbolo = Simbolo(n.nombre, n.tipo_declarado, self.contador, n.linea)
                self.contador += 1
                self.ambitos[-1][n.nombre] = simbolo
                n.simbolo = simbolo
            if not self._compatible(n.tipo_declarado, tipo_valor):
                self._error(n, f"no se puede asignar un valor de tipo {tipo_valor} "
                               f"a la variable '{n.nombre}' de tipo {n.tipo_declarado}")
        elif isinstance(n, Asignacion):
            tipo_valor = self._expr(n.valor)
            simbolo = self._buscar(n.nombre)
            if simbolo is None:
                self._error(n, f"la variable '{n.nombre}' no ha sido declarada")
            else:
                n.simbolo = simbolo
                if not self._compatible(simbolo.tipo, tipo_valor):
                    self._error(n, f"no se puede asignar un valor de tipo {tipo_valor} "
                                   f"a la variable '{n.nombre}' de tipo {simbolo.tipo}")
        elif isinstance(n, Escribir):
            self._expr(n.expresion)
        elif isinstance(n, Si):
            self._condicion(n.condicion, "si")
            self._sentencia(n.entonces)
            if n.sino is not None:
                self._sentencia(n.sino)
        elif isinstance(n, Mientras):
            self._condicion(n.condicion, "mientras")
            self._sentencia(n.cuerpo)
        elif isinstance(n, Bloque):
            self.ambitos.append({})
            for sentencia in n.sentencias:
                self._sentencia(sentencia)
            self.ambitos.pop()

    def _condicion(self, expresion, palabra):
        tipo = self._expr(expresion)
        if tipo not in ("booleano", "error"):
            self._error(expresion, f"la condición de '{palabra}' debe ser booleana, "
                                   f"pero es de tipo {tipo}")

    # -- expresiones: devuelven el tipo y lo guardan en el nodo
    def _fijar(self, nodo, tipo):
        nodo.tipo = tipo
        return tipo

    def _expr(self, n):
        if isinstance(n, Literal):
            return n.tipo
        if isinstance(n, Variable):
            simbolo = self._buscar(n.nombre)
            if simbolo is None:
                self._error(n, f"la variable '{n.nombre}' no ha sido declarada")
                return self._fijar(n, "error")
            n.simbolo = simbolo
            return self._fijar(n, simbolo.tipo)
        if isinstance(n, Unaria):
            return self._unaria(n)
        if isinstance(n, Binaria):
            return self._binaria(n)
        raise AssertionError(f"nodo de expresión desconocido: {n!r}")

    def _unaria(self, n):
        tipo = self._expr(n.operando)
        if n.op == "no":
            if tipo in ("booleano", "error"):
                return self._fijar(n, "booleano")
            self._error(n, f"el operador 'no' requiere un booleano, pero recibió {tipo}")
            return self._fijar(n, "booleano")
        # operador "-"
        if tipo in NUMERICOS or tipo == "error":
            return self._fijar(n, tipo)
        self._error(n, f"el operador '-' requiere un número, pero recibió {tipo}")
        return self._fijar(n, "error")

    def _binaria(self, n):
        ti = self._expr(n.izq)
        td = self._expr(n.der)
        op = n.op
        es_booleana = op in ("<", "<=", ">", ">=", "==", "!=", "y", "o")

        if "error" in (ti, td):
            return self._fijar(n, "booleano" if es_booleana else "error")

        ambos_numericos = ti in NUMERICOS and td in NUMERICOS
        mayor = "decimal" if "decimal" in (ti, td) else "entero"

        if op == "+":
            if "cadena" in (ti, td):  # concatenación
                return self._fijar(n, "cadena")
            if ambos_numericos:
                return self._fijar(n, mayor)
        elif op in ("-", "*", "/"):
            if ambos_numericos:
                if op == "/":
                    self._revisar_division_por_cero(n)
                return self._fijar(n, mayor)
        elif op == "%":
            if ti == "entero" and td == "entero":
                self._revisar_division_por_cero(n)
                return self._fijar(n, "entero")
        elif op in ("<", "<=", ">", ">="):
            if ambos_numericos:
                return self._fijar(n, "booleano")
        elif op in ("==", "!="):
            if ambos_numericos or ti == td:
                return self._fijar(n, "booleano")
        elif op in ("y", "o"):
            if ti == "booleano" and td == "booleano":
                return self._fijar(n, "booleano")

        self._error(n, f"no se puede aplicar '{op}' a operandos de tipo {ti} y {td}")
        return self._fijar(n, "booleano" if es_booleana else "error")

    def _revisar_division_por_cero(self, n):
        if isinstance(n.der, Literal) and n.der.tipo in NUMERICOS and n.der.valor == 0:
            self._error(n, "división entre cero")
