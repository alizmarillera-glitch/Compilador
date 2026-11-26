"""
Fase 4 - Generación de código.

Recorre el AST (ya verificado) y lo traduce a bytecode para una máquina de
pila. Cada instrucción es una tupla (operación, argumento).

    PUSH v     apila el valor v            LOAD i     apila la variable i
    STORE i    desapila y guarda en i      ITOF       convierte entero -> decimal
    ADD SUB MUL DIV FDIV MOD               aritmética (DIV entera, FDIV decimal)
    LT LE GT GE EQ NE                      comparaciones
    AND OR NOT NEG                         lógicos y menos unario
    CONCAT                                 une dos valores como texto
    JMP d      salta a la instrucción d    JMPF d     salta a d si el tope es falso
    PRINT      desapila e imprime          HALT       termina

Las estructuras de control (si, mientras) se convierten en saltos (JMP/JMPF);
los destinos se "parchean" cuando ya se conoce dónde termina cada bloque.
"""
from nodos import (Asignacion, Binaria, Bloque, Declaracion, Escribir, Literal,
                   Mientras, Si, Unaria, Variable)

OPERACION_ARITMETICA = {"+": "ADD", "-": "SUB", "*": "MUL", "%": "MOD"}
OPERACION_COMPARACION = {"<": "LT", "<=": "LE", ">": "GT", ">=": "GE", "==": "EQ", "!=": "NE"}


class GeneradorCodigo:
    def __init__(self):
        self.codigo = []

    def generar(self, programa):
        for sentencia in programa.sentencias:
            self._sentencia(sentencia)
        self._emitir("HALT")
        return self.codigo

    # -- utilidades
    def _emitir(self, operacion, argumento=None):
        self.codigo.append((operacion, argumento))
        return len(self.codigo) - 1

    def _parchear(self, indice, destino):
        operacion, _ = self.codigo[indice]
        self.codigo[indice] = (operacion, destino)

    def _expr_como(self, nodo, tipo_destino):
        """Genera la expresión y la convierte a decimal si hace falta."""
        self._expr(nodo)
        if nodo.tipo == "entero" and tipo_destino == "decimal":
            self._emitir("ITOF")

    # -- sentencias
    def _sentencia(self, n):
        if isinstance(n, Declaracion):
            self._expr_como(n.valor, n.simbolo.tipo)
            self._emitir("STORE", n.simbolo.id)
        elif isinstance(n, Asignacion):
            self._expr_como(n.valor, n.simbolo.tipo)
            self._emitir("STORE", n.simbolo.id)
        elif isinstance(n, Escribir):
            self._expr(n.expresion)
            self._emitir("PRINT")
        elif isinstance(n, Bloque):
            for sentencia in n.sentencias:
                self._sentencia(sentencia)
        elif isinstance(n, Si):
            self._expr(n.condicion)
            salto_falso = self._emitir("JMPF")
            self._sentencia(n.entonces)
            if n.sino is None:
                self._parchear(salto_falso, len(self.codigo))
            else:
                salto_fin = self._emitir("JMP")
                self._parchear(salto_falso, len(self.codigo))
                self._sentencia(n.sino)
                self._parchear(salto_fin, len(self.codigo))
        elif isinstance(n, Mientras):
            inicio = len(self.codigo)
            self._expr(n.condicion)
            salto_falso = self._emitir("JMPF")
            self._sentencia(n.cuerpo)
            self._emitir("JMP", inicio)
            self._parchear(salto_falso, len(self.codigo))

    # -- expresiones
    def _expr(self, n):
        if isinstance(n, Literal):
            self._emitir("PUSH", n.valor)
        elif isinstance(n, Variable):
            self._emitir("LOAD", n.simbolo.id)
        elif isinstance(n, Unaria):
            self._expr(n.operando)
            self._emitir("NOT" if n.op == "no" else "NEG")
        elif isinstance(n, Binaria):
            self._binaria(n)

    def _binaria(self, n):
        op = n.op
        if op in ("y", "o"):
            # No hay efectos secundarios en las expresiones, así que se evalúan ambas.
            self._expr(n.izq)
            self._expr(n.der)
            self._emitir("AND" if op == "y" else "OR")
        elif op == "+" and n.tipo == "cadena":
            self._expr(n.izq)
            self._expr(n.der)
            self._emitir("CONCAT")
        elif op in OPERACION_ARITMETICA or op == "/":
            self._expr_como(n.izq, n.tipo)
            self._expr_como(n.der, n.tipo)
            if op == "/":
                self._emitir("DIV" if n.tipo == "entero" else "FDIV")
            else:
                self._emitir(OPERACION_ARITMETICA[op])
        else:  # comparaciones: si se mezclan entero y decimal, se comparan como decimal
            tipos = (n.izq.tipo, n.der.tipo)
            comun = "decimal" if "decimal" in tipos else n.izq.tipo
            self._expr_como(n.izq, comun)
            self._expr_como(n.der, comun)
            self._emitir(OPERACION_COMPARACION[op])


def formatear_codigo(codigo):
    """Devuelve el bytecode como un listado numerado, legible para personas."""
    lineas = []
    for i, (operacion, argumento) in enumerate(codigo):
        if argumento is None:
            texto = ""
        elif isinstance(argumento, bool):
            texto = "verdadero" if argumento else "falso"
        else:
            texto = repr(argumento)
        lineas.append(f"{i:04d}  {operacion:<7}{texto}".rstrip())
    return "\n".join(lineas)
