"""
Fase 5 - Máquina virtual.

Ejecuta el bytecode generado. Usa una pila para los valores intermedios y un
diccionario como memoria de variables (la clave es el id del símbolo).
"""


class ErrorEjecucion(Exception):
    pass


def formatear_valor(valor):
    if isinstance(valor, bool):
        return "verdadero" if valor else "falso"
    return str(valor)


def _div_entera(a, b):
    if b == 0:
        raise ErrorEjecucion("Error de ejecución: división entre cero")
    cociente = abs(a) // abs(b)  # trunca hacia cero, como en C o Java
    return cociente if (a >= 0) == (b > 0) else -cociente


def _mod_entero(a, b):
    if b == 0:
        raise ErrorEjecucion("Error de ejecución: división entre cero")
    return a - b * _div_entera(a, b)


def _div_decimal(a, b):
    if b == 0:
        raise ErrorEjecucion("Error de ejecución: división entre cero")
    return a / b


OPERACIONES_BINARIAS = {
    "ADD": lambda a, b: a + b,
    "SUB": lambda a, b: a - b,
    "MUL": lambda a, b: a * b,
    "DIV": _div_entera,
    "FDIV": _div_decimal,
    "MOD": _mod_entero,
    "LT": lambda a, b: a < b,
    "LE": lambda a, b: a <= b,
    "GT": lambda a, b: a > b,
    "GE": lambda a, b: a >= b,
    "EQ": lambda a, b: a == b,
    "NE": lambda a, b: a != b,
    "AND": lambda a, b: a and b,
    "OR": lambda a, b: a or b,
}


class MaquinaVirtual:
    def __init__(self, codigo, salida=print, limite_pasos=10_000_000):
        self.codigo = codigo
        self.salida = salida
        self.limite_pasos = limite_pasos

    def ejecutar(self):
        codigo = self.codigo
        pila = []
        memoria = {}
        pc = 0
        pasos = 0

        while True:
            pasos += 1
            if pasos > self.limite_pasos:
                raise ErrorEjecucion(
                    "Error de ejecución: se superó el límite de pasos (¿bucle infinito?)")
            operacion, argumento = codigo[pc]
            pc += 1

            if operacion == "PUSH":
                pila.append(argumento)
            elif operacion == "LOAD":
                pila.append(memoria[argumento])
            elif operacion == "STORE":
                memoria[argumento] = pila.pop()
            elif operacion == "ITOF":
                pila.append(float(pila.pop()))
            elif operacion == "NEG":
                pila.append(-pila.pop())
            elif operacion == "NOT":
                pila.append(not pila.pop())
            elif operacion in OPERACIONES_BINARIAS:
                b = pila.pop()
                a = pila.pop()
                pila.append(OPERACIONES_BINARIAS[operacion](a, b))
            elif operacion == "CONCAT":
                b = pila.pop()
                a = pila.pop()
                pila.append(formatear_valor(a) + formatear_valor(b))
            elif operacion == "JMP":
                pc = argumento
            elif operacion == "JMPF":
                if not pila.pop():
                    pc = argumento
            elif operacion == "PRINT":
                self.salida(formatear_valor(pila.pop()))
            elif operacion == "HALT":
                return
            else:
                raise ErrorEjecucion(f"Error de ejecución: instrucción desconocida '{operacion}'")
