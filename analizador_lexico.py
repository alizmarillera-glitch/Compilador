"""
Fase 1 - Análisis léxico.

Convierte el texto del programa en una lista de tokens (las "palabras" del
lenguaje): palabras reservadas, identificadores, números, cadenas y símbolos.
Cada token guarda su línea y columna para poder dar errores claros.
"""
from dataclasses import dataclass

PALABRAS_RESERVADAS = {
    "var", "si", "sino", "mientras", "escribir",
    "verdadero", "falso", "y", "o", "no",
    "entero", "decimal", "booleano", "cadena",
}

TIPOS_DE_DATO = ("entero", "decimal", "booleano", "cadena")

SIMBOLOS_DOBLES = {"==", "!=", "<=", ">="}
SIMBOLOS_SIMPLES = set("+-*/%(){};:=<>")

ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


class ErrorLexico(Exception):
    def __init__(self, mensaje, linea, columna):
        self.linea = linea
        self.columna = columna
        super().__init__(f"Error léxico (línea {linea}, columna {columna}): {mensaje}")


@dataclass(frozen=True)
class Token:
    # Para palabras reservadas y símbolos, `tipo` es el propio texto ("var", "+").
    # Para el resto: ID, LIT_ENTERO, LIT_DECIMAL, LIT_CADENA y EOF.
    tipo: str
    valor: object
    linea: int
    columna: int

    def __str__(self):
        return f"{self.linea}:{self.columna:<4} {self.tipo:<12} {self.valor!r}"


class Lexer:
    def __init__(self, codigo):
        self.codigo = codigo
        self.pos = 0
        self.linea = 1
        self.columna = 1

    # -- utilidades de lectura
    def _actual(self):
        return self.codigo[self.pos] if self.pos < len(self.codigo) else ""

    def _siguiente(self):
        return self.codigo[self.pos + 1] if self.pos + 1 < len(self.codigo) else ""

    def _avanzar(self):
        c = self.codigo[self.pos]
        self.pos += 1
        if c == "\n":
            self.linea += 1
            self.columna = 1
        else:
            self.columna += 1
        return c

    @staticmethod
    def _es_digito(c):
        return c != "" and "0" <= c <= "9"

    # -- proceso principal
    def tokenizar(self):
        tokens = []
        while True:
            self._saltar_espacios_y_comentarios()
            c = self._actual()
            if c == "":
                break
            linea, col = self.linea, self.columna
            if self._es_digito(c):
                tokens.append(self._numero(linea, col))
            elif c.isalpha() or c == "_":
                tokens.append(self._identificador(linea, col))
            elif c == '"':
                tokens.append(self._cadena(linea, col))
            else:
                tokens.append(self._simbolo(linea, col))
        tokens.append(Token("EOF", None, self.linea, self.columna))
        return tokens

    def _saltar_espacios_y_comentarios(self):
        while True:
            c = self._actual()
            if c != "" and c.isspace():
                self._avanzar()
            elif c == "/" and self._siguiente() == "/":
                while self._actual() not in ("", "\n"):
                    self._avanzar()
            else:
                break

    def _numero(self, linea, col):
        inicio = self.pos
        while self._es_digito(self._actual()):
            self._avanzar()
        es_decimal = False
        if self._actual() == "." and self._es_digito(self._siguiente()):
            es_decimal = True
            self._avanzar()
            while self._es_digito(self._actual()):
                self._avanzar()
        texto = self.codigo[inicio:self.pos]
        if self._actual().isalpha() or self._actual() == "_":
            raise ErrorLexico(
                f"un identificador no puede empezar con un número ('{texto}{self._actual()}...')",
                linea, col)
        if es_decimal:
            return Token("LIT_DECIMAL", float(texto), linea, col)
        return Token("LIT_ENTERO", int(texto), linea, col)

    def _identificador(self, linea, col):
        inicio = self.pos
        while self._actual() != "" and (self._actual().isalnum() or self._actual() == "_"):
            self._avanzar()
        palabra = self.codigo[inicio:self.pos]
        if palabra in PALABRAS_RESERVADAS:
            return Token(palabra, palabra, linea, col)
        return Token("ID", palabra, linea, col)

    def _cadena(self, linea, col):
        self._avanzar()  # comilla de apertura
        caracteres = []
        while True:
            c = self._actual()
            if c == "" or c == "\n":
                raise ErrorLexico("cadena sin cerrar (falta la comilla final)", linea, col)
            if c == '"':
                self._avanzar()
                break
            if c == "\\":
                self._avanzar()
                if self._actual() not in ESCAPES:
                    raise ErrorLexico(
                        f"secuencia de escape no válida: '\\{self._actual()}'",
                        self.linea, self.columna)
                caracteres.append(ESCAPES[self._avanzar()])
            else:
                caracteres.append(self._avanzar())
        return Token("LIT_CADENA", "".join(caracteres), linea, col)

    def _simbolo(self, linea, col):
        c = self._actual()
        doble = c + self._siguiente()
        if doble in SIMBOLOS_DOBLES:
            self._avanzar()
            self._avanzar()
            return Token(doble, doble, linea, col)
        if c in SIMBOLOS_SIMPLES:
            self._avanzar()
            return Token(c, c, linea, col)
        raise ErrorLexico(f"carácter inesperado {c!r}", linea, col)
