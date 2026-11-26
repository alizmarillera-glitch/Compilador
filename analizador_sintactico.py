"""
Fase 2 - Análisis sintáctico.

Parser descendente recursivo: recibe los tokens y construye el árbol (AST),
verificando que el programa respete la gramática del lenguaje.

Gramática (EBNF):

    programa      := sentencia* EOF
    sentencia     := declaracion | asignacion | si | mientras | escribir | bloque
    declaracion   := "var" ID ":" TIPO "=" expresion ";"
    asignacion    := ID "=" expresion ";"
    si            := "si" "(" expresion ")" bloque [ "sino" ( si | bloque ) ]
    mientras      := "mientras" "(" expresion ")" bloque
    escribir      := "escribir" "(" expresion ")" ";"
    bloque        := "{" sentencia* "}"

    expresion     := o
    o             := y ( "o" y )*
    y             := igualdad ( "y" igualdad )*
    igualdad      := relacional ( ("==" | "!=") relacional )*
    relacional    := suma ( ("<" | "<=" | ">" | ">=") suma )*
    suma          := termino ( ("+" | "-") termino )*
    termino       := unario ( ("*" | "/" | "%") unario )*
    unario        := ("-" | "no") unario | primario
    primario      := LIT_ENTERO | LIT_DECIMAL | LIT_CADENA
                   | "verdadero" | "falso" | ID | "(" expresion ")"

Cada nivel de la gramática es un método: así se respeta la precedencia de
operadores (de menor a mayor: o, y, igualdad, comparación, suma, producto, unario).
"""
from analizador_lexico import TIPOS_DE_DATO
from nodos import (Asignacion, Binaria, Bloque, Declaracion, Escribir, Literal,
                   Mientras, Programa, Si, Unaria, Variable)


class ErrorSintactico(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -- utilidades
    def _actual(self):
        return self.tokens[self.pos]

    def _avanzar(self):
        token = self.tokens[self.pos]
        if token.tipo != "EOF":
            self.pos += 1
        return token

    def _error(self, token, mensaje):
        raise ErrorSintactico(
            f"Error sintáctico (línea {token.linea}, columna {token.columna}): {mensaje}")

    @staticmethod
    def _describir(token):
        if token.tipo == "EOF":
            return "el fin del archivo"
        return f"'{token.valor}'"

    def _consumir(self, tipo, mensaje=None):
        token = self._actual()
        if token.tipo == tipo:
            return self._avanzar()
        if tipo == ";" and self.pos > 0:
            # Un ';' faltante se nota en la línea anterior, no en la siguiente.
            self._error(self.tokens[self.pos - 1], "falta ';' al final de la sentencia")
        if mensaje is None:
            mensaje = f"se esperaba '{tipo}' pero se encontró {self._describir(token)}"
        self._error(token, mensaje)

    # -- programa y sentencias
    def parsear(self):
        sentencias = []
        while self._actual().tipo != "EOF":
            sentencias.append(self._sentencia())
        return Programa(sentencias)

    def _sentencia(self):
        token = self._actual()
        if token.tipo == "var":
            return self._declaracion()
        if token.tipo == "si":
            return self._si()
        if token.tipo == "mientras":
            return self._mientras()
        if token.tipo == "escribir":
            return self._escribir()
        if token.tipo == "{":
            return self._bloque()
        if token.tipo == "ID":
            return self._asignacion()
        self._error(token, f"sentencia no válida: no se esperaba {self._describir(token)} aquí")

    def _bloque(self):
        self._consumir("{")
        sentencias = []
        while self._actual().tipo not in ("}", "EOF"):
            sentencias.append(self._sentencia())
        self._consumir("}", "falta cerrar el bloque con '}'")
        return Bloque(sentencias)

    def _declaracion(self):
        inicio = self._consumir("var")
        nombre = self._consumir("ID", "se esperaba el nombre de la variable después de 'var'")
        self._consumir(":")
        tipo = self._actual()
        if tipo.tipo not in TIPOS_DE_DATO:
            self._error(tipo, "se esperaba un tipo (entero, decimal, booleano o cadena)")
        self._avanzar()
        self._consumir("=")
        valor = self._expresion()
        self._consumir(";")
        return Declaracion(nombre.valor, tipo.tipo, valor, inicio.linea, inicio.columna)

    def _asignacion(self):
        nombre = self._consumir("ID")
        self._consumir("=", f"se esperaba '=' después de '{nombre.valor}'")
        valor = self._expresion()
        self._consumir(";")
        return Asignacion(nombre.valor, valor, nombre.linea, nombre.columna)

    def _si(self):
        inicio = self._consumir("si")
        self._consumir("(")
        condicion = self._expresion()
        self._consumir(")")
        entonces = self._bloque()
        sino = None
        if self._actual().tipo == "sino":
            self._avanzar()
            sino = self._si() if self._actual().tipo == "si" else self._bloque()
        return Si(condicion, entonces, sino, inicio.linea, inicio.columna)

    def _mientras(self):
        inicio = self._consumir("mientras")
        self._consumir("(")
        condicion = self._expresion()
        self._consumir(")")
        cuerpo = self._bloque()
        return Mientras(condicion, cuerpo, inicio.linea, inicio.columna)

    def _escribir(self):
        inicio = self._consumir("escribir")
        self._consumir("(")
        expresion = self._expresion()
        self._consumir(")")
        self._consumir(";")
        return Escribir(expresion, inicio.linea, inicio.columna)

    # -- expresiones (un método por nivel de precedencia)
    def _binaria(self, siguiente_nivel, operadores):
        izq = siguiente_nivel()
        while self._actual().tipo in operadores:
            op = self._avanzar()
            der = siguiente_nivel()
            izq = Binaria(op.tipo, izq, der, op.linea, op.columna)
        return izq

    def _expresion(self):
        return self._binaria(self._y, ("o",))

    def _y(self):
        return self._binaria(self._igualdad, ("y",))

    def _igualdad(self):
        return self._binaria(self._relacional, ("==", "!="))

    def _relacional(self):
        return self._binaria(self._suma, ("<", "<=", ">", ">="))

    def _suma(self):
        return self._binaria(self._termino, ("+", "-"))

    def _termino(self):
        return self._binaria(self._unario, ("*", "/", "%"))

    def _unario(self):
        if self._actual().tipo in ("-", "no"):
            op = self._avanzar()
            return Unaria(op.tipo, self._unario(), op.linea, op.columna)
        return self._primario()

    def _primario(self):
        token = self._actual()
        if token.tipo == "LIT_ENTERO":
            self._avanzar()
            return Literal(token.valor, "entero", token.linea, token.columna)
        if token.tipo == "LIT_DECIMAL":
            self._avanzar()
            return Literal(token.valor, "decimal", token.linea, token.columna)
        if token.tipo == "LIT_CADENA":
            self._avanzar()
            return Literal(token.valor, "cadena", token.linea, token.columna)
        if token.tipo in ("verdadero", "falso"):
            self._avanzar()
            return Literal(token.tipo == "verdadero", "booleano", token.linea, token.columna)
        if token.tipo == "ID":
            self._avanzar()
            return Variable(token.valor, token.linea, token.columna)
        if token.tipo == "(":
            self._avanzar()
            expresion = self._expresion()
            self._consumir(")", "falta cerrar el paréntesis ')'")
            return expresion
        self._error(token, f"se esperaba una expresión pero se encontró {self._describir(token)}")
