# Compilador Mini

Compilador educativo escrito en **Python** para un lenguaje pequeño con palabras clave en español. Toma un programa, lo pasa por las fases clásicas de un compilador, lo traduce a **bytecode** para una máquina de pila y lo ejecuta en una máquina virtual propia.

Proyecto académico para entender cómo funciona un compilador por dentro, sin usar generadores de analizadores: cada fase está escrita a mano.

## Fases

| # | Fase | Archivo | Qué hace |
|---|------|---------|----------|
| 1 | Análisis léxico | `analizador_lexico.py` | Convierte el texto en tokens (palabras reservadas, identificadores, números, cadenas, símbolos) con línea y columna. |
| 2 | Análisis sintáctico | `analizador_sintactico.py` | Parser descendente recursivo: verifica la gramática y construye el árbol (AST). Respeta la precedencia de operadores. |
| 3 | Análisis semántico | `analizador_semantico.py` | Tabla de símbolos con ámbitos, verificación de tipos, variables declaradas, condiciones booleanas, división entre cero evidente. Reporta todos los errores encontrados. |
| 4 | Generación de código | `generador_codigo.py` | Traduce el AST a bytecode de pila; `si` y `mientras` se convierten en saltos. |
| 5 | Ejecución | `maquina_virtual.py` | Máquina virtual de pila que ejecuta el bytecode. |

Apoyan: `nodos.py` (definición del AST) y `main.py` (línea de comandos).

## El lenguaje

Tipos: `entero`, `decimal`, `booleano`, `cadena`.

```
// Comentario de una línea
var precio: decimal = 20.5;
var cantidad: entero = 3;
var total: decimal = precio * cantidad;

escribir("Total: " + total);

si (total > 100) {
    escribir("Descuento grande");
} sino si (total > 50 y no (cantidad == 0)) {
    escribir("Descuento normal");
} sino {
    escribir("Sin descuento");
}

var n: entero = 3;
mientras (n > 0) {
    escribir(n);
    n = n - 1;
}
```

- **Operadores aritméticos:** `+ - * / %` (la división entre enteros es entera; `%` solo entre enteros).
- **Comparación:** `< <= > >= == !=`
- **Lógicos:** `y`, `o`, `no`
- **Concatenación:** `+` con una cadena convierte el otro valor a texto.
- Un `entero` se convierte solo a `decimal` cuando hace falta; al revés no.
- Cada bloque `{ }` abre un ámbito nuevo.

## Uso

Requiere Python 3.8 o superior. No necesita instalar nada.

```
python main.py fibonacci.mini                 # compila y ejecuta
python main.py fibonacci.mini --tokens        # muestra los tokens
python main.py fibonacci.mini --ast           # muestra el árbol con tipos
python main.py fibonacci.mini --bytecode      # muestra el bytecode
python main.py fibonacci.mini --no-ejecutar   # solo compila
```

Pruebas automáticas:

```
python -m unittest -v
```

## Ejemplo

`cuenta_regresiva.mini`:

```
var n: entero = 3;
mientras (n > 0) {
    escribir(n);
    n = n - 1;
}
```

`python main.py cuenta_regresiva.mini --bytecode`:

```
=== BYTECODE ===
0000  PUSH   3
0001  STORE  0
0002  LOAD   0
0003  PUSH   0
0004  GT
0005  JMPF   13
0006  LOAD   0
0007  PRINT
0008  LOAD   0
0009  PUSH   1
0010  SUB
0011  STORE  0
0012  JMP    2
0013  HALT
=== SALIDA ===
3
2
1
```

### Errores

Los errores indican fase, línea y columna. El análisis semántico muestra todos los que encuentra. `python main.py error_semantico.mini`:

```
Error semántico (línea 4, columna 1): la variable 'x' ya fue declarada en este ámbito (línea 3)
Error semántico (línea 5, columna 1): no se puede asignar un valor de tipo entero a la variable 'texto' de tipo cadena
Error semántico (línea 6, columna 1): la variable 'z' no ha sido declarada
Error semántico (línea 7, columna 5): la condición de 'si' debe ser booleana, pero es de tipo entero
```

## Archivos de ejemplo

- `fibonacci.mini`: serie de Fibonacci con un bucle.
- `primos.mini`: números primos, bucles anidados y concatenación.
- `calculos.mini`: tipos, lógica, `si / sino si / sino` y ámbitos.
- `cuenta_regresiva.mini`: el programa mínimo de arriba.
- `error_semantico.mini`: programa con errores a propósito.

## Limitaciones y posibles mejoras

- No hay funciones, arreglos ni lectura de datos del usuario (`leer`).
- Solo se reporta un error léxico o sintáctico a la vez (se detiene en el primero); los semánticos sí se reportan juntos.
- El bytecode se ejecuta en una máquina virtual; una mejora sería generar código para otro destino (por ejemplo ensamblador o C).
