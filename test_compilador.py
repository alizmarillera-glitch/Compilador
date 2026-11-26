"""Pruebas del compilador. Ejecutar con:  python -m unittest -v"""
import unittest

from analizador_lexico import ErrorLexico, Lexer
from analizador_semantico import ErrorSemantico
from analizador_sintactico import ErrorSintactico
from main import compilar
from maquina_virtual import ErrorEjecucion, MaquinaVirtual


def correr(codigo, **opciones):
    salida = []
    MaquinaVirtual(compilar(codigo), salida.append, **opciones).ejecutar()
    return salida


class PruebasLexico(unittest.TestCase):
    def test_tokens_de_una_declaracion(self):
        tokens = Lexer("var x: entero = 5;").tokenizar()
        self.assertEqual([t.tipo for t in tokens],
                         ["var", "ID", ":", "entero", "=", "LIT_ENTERO", ";", "EOF"])

    def test_comentarios_se_ignoran_y_se_cuentan_lineas(self):
        tokens = Lexer("// hola\nvar").tokenizar()
        self.assertEqual([t.tipo for t in tokens], ["var", "EOF"])
        self.assertEqual(tokens[0].linea, 2)

    def test_numero_decimal_y_operadores_dobles(self):
        tokens = Lexer("3.14 <= 2").tokenizar()
        self.assertEqual([t.tipo for t in tokens], ["LIT_DECIMAL", "<=", "LIT_ENTERO", "EOF"])

    def test_caracter_invalido(self):
        with self.assertRaises(ErrorLexico):
            Lexer("var x = @;").tokenizar()

    def test_cadena_sin_cerrar(self):
        with self.assertRaises(ErrorLexico):
            Lexer('escribir("hola);').tokenizar()


class PruebasSintaxis(unittest.TestCase):
    def test_falta_punto_y_coma(self):
        with self.assertRaises(ErrorSintactico) as ctx:
            compilar("var x: entero = 5")
        self.assertIn("falta ';'", str(ctx.exception))

    def test_falta_cerrar_bloque(self):
        with self.assertRaises(ErrorSintactico):
            compilar("mientras (verdadero) { escribir(1);")

    def test_expresion_incompleta(self):
        with self.assertRaises(ErrorSintactico):
            compilar("var x: entero = 5 + ;")


class PruebasSemantica(unittest.TestCase):
    def mensaje(self, codigo):
        with self.assertRaises(ErrorSemantico) as ctx:
            compilar(codigo)
        return str(ctx.exception)

    def test_variable_no_declarada(self):
        self.assertIn("no ha sido declarada", self.mensaje("escribir(z);"))

    def test_tipos_incompatibles(self):
        self.assertIn("no se puede asignar", self.mensaje('var x: entero = "hola";'))

    def test_decimal_no_cabe_en_entero(self):
        self.assertIn("no se puede asignar", self.mensaje("var x: entero = 2.5;"))

    def test_redeclaracion(self):
        self.assertIn("ya fue declarada",
                      self.mensaje("var x: entero = 1; var x: entero = 2;"))

    def test_condicion_no_booleana(self):
        self.assertIn("debe ser booleana", self.mensaje("si (1) { }"))

    def test_division_por_cero_literal(self):
        self.assertIn("división entre cero", self.mensaje("escribir(5 / 0);"))

    def test_operandos_invalidos(self):
        self.assertIn("no se puede aplicar", self.mensaje("escribir(verdadero - 1);"))

    def test_reporta_varios_errores_juntos(self):
        mensaje = self.mensaje("escribir(a); escribir(b);")
        self.assertEqual(mensaje.count("Error semántico"), 2)


class PruebasEjecucion(unittest.TestCase):
    def test_precedencia(self):
        self.assertEqual(correr("escribir(2 + 3 * 4);"), ["14"])
        self.assertEqual(correr("escribir((2 + 3) * 4);"), ["20"])

    def test_division_entera_trunca_hacia_cero(self):
        self.assertEqual(correr("escribir(7 / 2); escribir(-7 / 2); escribir(7 % 3);"),
                         ["3", "-3", "1"])

    def test_decimales(self):
        self.assertEqual(correr("escribir(7 / 2.0);"), ["3.5"])
        self.assertEqual(correr("var d: decimal = 5; escribir(d);"), ["5.0"])

    def test_concatenacion(self):
        self.assertEqual(correr('escribir("a" + 1 + verdadero);'), ["a1verdadero"])

    def test_logica(self):
        self.assertEqual(correr("escribir(1 < 2 y no (3 == 4));"), ["verdadero"])
        self.assertEqual(correr("escribir(falso o falso);"), ["falso"])

    def test_si_sino_si_sino(self):
        codigo = """
        var n: entero = 5;
        si (n > 10) { escribir("grande"); }
        sino si (n > 3) { escribir("medio"); }
        sino { escribir("chico"); }
        """
        self.assertEqual(correr(codigo), ["medio"])

    def test_ambitos(self):
        codigo = "var x: entero = 1; { var x: entero = 2; escribir(x); } escribir(x);"
        self.assertEqual(correr(codigo), ["2", "1"])

    def test_fibonacci(self):
        with open("fibonacci.mini", encoding="utf-8") as f:
            self.assertEqual(correr(f.read()),
                             ["0", "1", "1", "2", "3", "5", "8", "13", "21", "34"])

    def test_primos(self):
        with open("primos.mini", encoding="utf-8") as f:
            salida = correr(f.read())
        self.assertEqual(salida, [f"Primo: {p}" for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29)])

    def test_division_por_cero_en_ejecucion(self):
        with self.assertRaises(ErrorEjecucion):
            correr("var a: entero = 0; escribir(10 / a);")

    def test_bucle_infinito_se_detiene(self):
        with self.assertRaises(ErrorEjecucion):
            correr("mientras (verdadero) { }", limite_pasos=1000)


if __name__ == "__main__":
    unittest.main()
