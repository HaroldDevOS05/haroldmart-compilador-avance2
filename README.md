# Haroldmart · Lenguaje de reglas de promociones — Avance 2 (análisis sintáctico)

**Compiladores (IDS601) · 6.º semestre · UNEDL 2026B** · Harold Figueroa Márquez

Este repositorio contiene el **Avance 2**: la gramática LL(1) final de mi lenguaje (verificada con un programa), el parser
descendente recursivo que imprime el árbol de cada regla, la recuperación de errores (modo pánico y nivel de frase) que
reporta **todos** los errores con su línea, y las pruebas con sus salidas reales. También incluye el escáner del Avance 1
(que el parser usa) y, como adelanto del Avance 3, la tabla de símbolos.

**Contenido:** [1 Negocio](#1-mi-negocio-y-mi-lenguaje) · [2 Tokens](#2-tokens-avance-1) · [3 Gramática](#3-gramática-final) ·
[4 Verificación](#4-verificación-de-la-gramática) · [5 Tabla LL(1)](#5-first-follow-y-tabla-ll1) ·
[6 Comparación](#6-comparación-con-recursión-izquierda-y-sin-factorizar) · [7 Parser](#7-parser-descendente-recursivo) ·
[8 Recuperación](#8-recuperación-de-errores) · [9 Pruebas](#9-pruebas-y-salidas-reales) ·
[10 Tabla de símbolos](#10-tabla-de-símbolos-adelanto-del-avance-3) · [11 Cotejo](#11-lista-de-cotejo) · [12 Cómo correr](#12-estructura-y-cómo-correr-todo)

---

## 1. Mi negocio y mi lenguaje

Haroldmart es un supermercado cuyo administrador cambia las promociones cada semana (descuentos por monto de compra,
paquetes, rebajas, envío gratis, precios de mayoreo, descuento para adultos mayores). Para no depender de un programador en
cada cambio, el lenguaje le permite escribir esas reglas en español sencillo, por ejemplo:

```
SI total_compra > $1000 ENTONCES descuento = 5
SI total_compra >= $500 ENTONCES envio = $0 SINO envio = $50
MIENTRAS productos_limpieza >= 3 HACER regalo = 1
```

## 2. Tokens (Avance 1)

El parser trabaja con los tokens que entrega `src/escaner_Haroldmart.py` (el escáner del Avance 1, con un AFD por token).
Los terminales de la gramática se llaman igual que estos tipos de token.

| Token | Expresión regular | Ejemplos |
|---|---|---|
| `SI`, `ENTONCES`, `SINO`, `MIENTRAS`, `HACER`, `ESCRIBIR` (más `PARA`, `SEGUN`, `CASO`, `FUNCION`, `RETORNAR`, `PROCEDIMIENTO`, `FIN`, `ROMPER`, `CONTINUAR`, `LEER`, reservadas pero sin uso todavía en la gramática) | palabra exacta, en mayúsculas | `SI`, `HACER` |
| `ID` | `letra (letra \| dígito \| _)*` | `total_compra`, `descuento_5` |
| `NUM` | `dígito+ ( . dígito+ )?` | `10`, `0.5` |
| `PRECIO` | `$ dígito+ ( . dígito+ )?` | `$1000`, `$28.50` |
| `CADENA` | `" (cualquier carácter excepto " y salto de línea)* "` | `"Promoción aplicada"` |
| `MAYOR` `MENOR` `MAYORIGUAL` `MENORIGUAL` `ASIGNA` | `>` `<` `>=` `<=` `=` | |
| (se ignoran) | espacios, tabs, saltos de línea, comentarios `// ...` | |

## 3. Gramática final

Una regla puede ser una condición (`SI … ENTONCES … [SINO …]`), un ciclo (`MIENTRAS … HACER …`), una asignación suelta o un
mensaje (`ESCRIBIR`). La acción de un `SI` o de un `MIENTRAS` es una asignación o un `ESCRIBIR`. ε significa «vacío».

```
   1. Programa → Regla Programa
   2. Programa → ε
   3. Regla → Si
   4. Regla → Mientras
   5. Regla → Asig
   6. Regla → Escribir
   7. Si → SI Cond ENTONCES Accion Sino
   8. Sino → SINO Accion
   9. Sino → ε
  10. Mientras → MIENTRAS Cond HACER Accion
  11. Accion → Asig
  12. Accion → Escribir
  13. Asig → ID ASIGNA Valor
  14. Escribir → ESCRIBIR Valor
  15. Cond → ID Oprel Valor
  16. Oprel → MAYOR
  17. Oprel → MENOR
  18. Oprel → MAYORIGUAL
  19. Oprel → MENORIGUAL
  20. Valor → NUM
  21. Valor → PRECIO
  22. Valor → CADENA
```

Decisiones de diseño:

- **Sin recursión izquierda:** la lista de reglas es `Programa → Regla Programa | ε` (recursión por la derecha).
- **Sin ambigüedad del SINO:** `Si → SI Cond ENTONCES Accion Sino` con `Sino → SINO Accion | ε`. Como la acción nunca es otro `Si`, el
  `SINO` siempre pertenece al `SI` inmediato anterior (no hay «else colgante»).
- **Operadores de comparación** agrupados en el no terminal `Oprel` para que `Cond` quede en una sola regla.
- **`Valor`** acepta número, precio (`$`) o cadena; así la tabla de símbolos puede distinguir el tipo de cada variable.

## 4. Verificación de la gramática

Salida real de `python src/verificar_gramatica.py` (programa `verificar_base.py` del profesor, con mi gramática). La primera
gramática es la **final**; las otras dos son las comparaciones de la sección 6.

```
== MI GRAMÁTICA (final) (22 reglas)
   Recursión izquierda: no
   Conflictos LL(1):    0
   Conflictos SLR:      0 (en 36 estados)
   → SIRVE para nuestro parser LL(1) · SIRVE para SLR
== VERSIÓN A: con recursión izquierda (Programa → Programa Regla) (22 reglas)
   Recursión izquierda: Programa
   Conflictos LL(1):    4
      celda [Programa, ESCRIBIR]: reglas 1, 2
      celda [Programa, ID]: reglas 1, 2
      celda [Programa, MIENTRAS]: reglas 1, 2
   Conflictos SLR:      0 (en 35 estados)
   → NO sirve para LL(1) · SIRVE para SLR
== VERSIÓN B: sin factorizar el SINO (dos reglas Si que empiezan igual) (21 reglas)
   Recursión izquierda: no
   Conflictos LL(1):    1
      celda [Si, SI]: reglas 20, 21
   Conflictos SLR:      0 (en 35 estados)
   → NO sirve para LL(1) · SIRVE para SLR

```

**Mi gramática final: «Recursión izquierda: no» y «Conflictos LL(1): 0»**, y además no tiene conflictos SLR.

## 5. FIRST, FOLLOW y tabla LL(1)

```
FIRST:
  FIRST(Programa) = { SI, MIENTRAS, ID, ESCRIBIR, ε }
  FIRST(Regla) = { SI, MIENTRAS, ID, ESCRIBIR }
  FIRST(Si) = { SI }
  FIRST(Sino) = { SINO, ε }
  FIRST(Mientras) = { MIENTRAS }
  FIRST(Accion) = { ID, ESCRIBIR }
  FIRST(Asig) = { ID }
  FIRST(Escribir) = { ESCRIBIR }
  FIRST(Cond) = { ID }
  FIRST(Oprel) = { MAYOR, MENOR, MAYORIGUAL, MENORIGUAL }
  FIRST(Valor) = { NUM, PRECIO, CADENA }

FOLLOW:
  FOLLOW(Programa) = { $ }
  FOLLOW(Regla) = { SI, MIENTRAS, ID, ESCRIBIR, $ }
  FOLLOW(Si) = { SI, MIENTRAS, ID, ESCRIBIR, $ }
  FOLLOW(Sino) = { SI, MIENTRAS, ID, ESCRIBIR, $ }
  FOLLOW(Mientras) = { SI, MIENTRAS, ID, ESCRIBIR, $ }
  FOLLOW(Accion) = { SI, SINO, MIENTRAS, ID, ESCRIBIR, $ }
  FOLLOW(Asig) = { SI, SINO, MIENTRAS, ID, ESCRIBIR, $ }
  FOLLOW(Escribir) = { SI, SINO, MIENTRAS, ID, ESCRIBIR, $ }
  FOLLOW(Cond) = { ENTONCES, HACER }
  FOLLOW(Oprel) = { NUM, PRECIO, CADENA }
  FOLLOW(Valor) = { SI, ENTONCES, SINO, MIENTRAS, HACER, ID, ESCRIBIR, $ }
```

**Tabla LL(1)** (cada celda es el número de la regla de la sección 3 que se usa; celda vacía = error sintáctico). Ninguna celda tiene
más de una regla, por eso la gramática es LL(1):

| | SI | ENTONCES | SINO | MIENTRAS | HACER | ID | ASIGNA | ESCRIBIR | MAYOR | MENOR | MAYORIGUAL | MENORIGUAL | NUM | PRECIO | CADENA | $ |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Programa** | 1 |   |   | 1 |   | 1 |   | 1 |   |   |   |   |   |   |   | 2 |
| **Regla** | 3 |   |   | 4 |   | 5 |   | 6 |   |   |   |   |   |   |   |   |
| **Si** | 7 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| **Sino** | 9 |   | 8 | 9 |   | 9 |   | 9 |   |   |   |   |   |   |   | 9 |
| **Mientras** |   |   |   | 10 |   |   |   |   |   |   |   |   |   |   |   |   |
| **Accion** |   |   |   |   |   | 11 |   | 12 |   |   |   |   |   |   |   |   |
| **Asig** |   |   |   |   |   | 13 |   |   |   |   |   |   |   |   |   |   |
| **Escribir** |   |   |   |   |   |   |   | 14 |   |   |   |   |   |   |   |   |
| **Cond** |   |   |   |   |   | 15 |   |   |   |   |   |   |   |   |   |   |
| **Oprel** |   |   |   |   |   |   |   |   | 16 | 17 | 18 | 19 |   |   |   |   |
| **Valor** |   |   |   |   |   |   |   |   |   |   |   |   | 20 | 21 | 22 |   |

## 6. Comparación con recursión izquierda y sin factorizar

Para entender qué acepta cada método, agregué dos versiones de la gramática en `verificar_gramatica.py`:

| Versión | Recursión izquierda | Conflictos LL(1) | Conflictos SLR |
|---|---|---|---|
| **Final** (`Programa → Regla Programa \| ε`) | no | **0** | **0** |
| **A**: `Programa → Programa Regla \| ε` | sí (`Programa`) | 4 (celdas `[Programa, SI]`, `[Programa, MIENTRAS]`, `[Programa, ID]`, `[Programa, ESCRIBIR]`) | 0 |
| **B**: sin factorizar `Si → SI Cond ENTONCES Accion \| SI Cond ENTONCES Accion SINO Accion` | no | 1 (`[Si, SI]`: reglas 20 y 21) | 0 |

**Por qué LR sí acepta la versión A y LL(1) no.** Un parser LL(1) decide qué regla usar mirando *un solo token antes de empezar* a
reconocer el no terminal. En `Programa → Programa Regla | ε`, con el token `SI` las dos reglas siguen siendo posibles (conflicto) y, si
eligiera la primera, la función `programa()` se llamaría a sí misma sin consumir nada: recursión infinita. Un parser LR (SLR, LALR)
trabaja de abajo hacia arriba con una pila: lee y apila los símbolos y solo *reduce* cuando ya vio todo el lado derecho de una regla, así
que no necesita adivinar al principio y la recursión izquierda no lo cicla (incluso es lo más eficiente para él). De la misma forma,
la versión B no es LL(1) porque las dos reglas de `Si` empiezan igual y hay que **factorizar** (sacar lo común: `Sino`), pero un parser LR
la acepta porque espera a ver si después de la acción viene `SINO` antes de reducir.

**LALR y yacc/bison.** LALR(1) es el método ascendente que usan `yacc` y `bison`: construye los estados del autómata LR y junta los que tienen
el mismo núcleo, con lo que la tabla es tan pequeña como la de SLR pero más precisa (usa el token de anticipación de cada estado). Acepta más
gramáticas que LL(1) y SLR. Se usa porque esas herramientas **generan el parser automáticamente** a partir de la gramática, mientras que en
nuestro LL(1) a mano escribimos una función por cada no terminal.

## 7. Parser descendente recursivo

`src/parser_Haroldmart.py`: **una función por cada no terminal** (11 no terminales, 11 funciones). Cada función mira el token actual
(según la tabla LL(1)), consume los terminales con `emparejar()` y llama a las funciones de los no terminales; regresa un nodo del árbol.

| No terminal | Función | Se decide con el token |
|---|---|---|
| `Programa` | `programa()` | ε si llega `$`; si no, `Regla` (la recursión final es un ciclo `while`) |
| `Regla` | `regla()` | `SI`, `MIENTRAS`, `ID`, `ESCRIBIR` |
| `Si` | `si()` | `SI` |
| `Sino` | `sino()` | `SINO`; cualquier otro (los de FOLLOW) = ε |
| `Mientras` | `mientras()` | `MIENTRAS` |
| `Accion` | `accion()` | `ID` o `ESCRIBIR` |
| `Asig` | `asig()` | `ID` |
| `Escribir` | `escribir()` | `ESCRIBIR` |
| `Cond` | `cond()` | `ID` |
| `Oprel` | `oprel()` | `>`, `<`, `>=`, `<=` |
| `Valor` | `valor()` | `NUM`, `PRECIO`, `CADENA` |

El parser de `parser_Haroldmart.py` se detiene en el **primer** error (como el `parser_base.py` del profesor). Los mensajes dicen
la línea y qué se esperaba en palabras del negocio («un operador de comparación», «una variable», «un precio»). Si una regla se
queda a medias al final del renglón, el error se reporta en ese renglón y no en el siguiente.

## 8. Recuperación de errores

`src/parser_con_recuperacion.py` (hereda de `Parser`) para que el programa **no se detenga** y reporte todos los errores:

- **Modo pánico** (`modo_panico`): tras un error, salta tokens hasta el inicio de una regla en un renglón posterior (`SI`, `MIENTRAS`,
  `ESCRIBIR` o una variable) o hasta el fin, y sigue revisando. Compara con la línea donde *empezó* la regla, así no se salta reglas buenas.
- **Nivel de frase** (`emparejar`): si falta `ENTONCES` (o `HACER`) y ya viene la acción, lo avisa y lo «supone» sin avanzar, para seguir con esa regla.
- **Errores léxicos y sintácticos juntos:** el escáner reporta sus errores y el parser los suyos; salen ordenados por línea. Un error
  de sintaxis en un renglón que ya tiene un error léxico se omite (es consecuencia del símbolo desconocido) y se avisa cuántos fueron.

## 9. Pruebas y salidas reales

Las salidas completas están en la carpeta [`salidas/`](salidas). Aquí van resumidas (inicio y fin).

### 9.1 Tres reglas reales de mi negocio (descuento, envío gratis, cotización)

`pruebas/avance2_tres_reglas.txt`:

```
// Avance 2: tres reglas reales de Haroldmart
// 1) Descuento por monto de compra
SI total_compra > $1000 ENTONCES descuento = 5
// 2) Envío gratis a domicilio
SI total_compra >= $500 ENTONCES envio = $0 SINO envio = $50
// 3) Cotización de mayoreo
SI piezas > 100 ENTONCES precio_unitario = $8.50 SINO precio_unitario = $10
```

`python src/parser_con_recuperacion.py pruebas/avance2_tres_reglas.txt` imprime el árbol de cada regla:

```
Programa
├─ Regla
│  └─ Si
│     ├─ SI: SI
│     ├─ Cond
│     │  ├─ ID: total_compra
│     │  ├─ Oprel
│     │  │  └─ MAYOR: >
│     │  └─ Valor
│     │     └─ PRECIO: $1000
│     ├─ ENTONCES: ENTONCES
│     └─ Accion
│        └─ Asig
│           ├─ ID: descuento
│           ├─ ASIGNA: =
│           └─ Valor
   …
               ├─ ID: precio_unitario
               ├─ ASIGNA: =
               └─ Valor
                  └─ PRECIO: $10

Reglas reconocidas: 3 · errores: 0
```

También reconoce el archivo completo de promociones del Avance 1 (`pruebas/reglas_ok.txt`: `MIENTRAS`, `ESCRIBIR`, decimales, cadenas):

```
Reglas reconocidas: 7 · errores: 0
```

### 9.2 Archivo con errores de sintaxis (varios renglones)

`pruebas/errores_sintacticos.txt`:

```
// Prueba con errores de SINTAXIS (los tokens son válidos, la estructura de la regla no)
SI total_compra > $1000 ENTONCES descuento = 5
SI total_compra >= $500 envio = $0 SINO envio = $50
SI piezas 100 ENTONCES precio_unitario = $8.50
MIENTRAS productos_limpieza >= 3 HACER regalo = 1
SINO descuento = 0
SI edad >= 60 ENTONCES descuento_adulto =
SI descuento > 0 ENTONCES ESCRIBIR "Promoción aplicada"
```

`python src/parser_con_recuperacion.py pruebas/errores_sintacticos.txt` (reporta todos, con su línea, y sigue):

```
Reglas reconocidas: 4 · errores: 4 (0 léxicos, 4 sintácticos)
  Línea 3: se esperaba ENTONCES antes de 'envio' (lo supuse para seguir)
  Línea 4: error de sintaxis, se esperaba un operador de comparación (>, <, >=, <=) y llegó '100' (NUM)
  Línea 6: error de sintaxis, se esperaba SI, MIENTRAS, ESCRIBIR o una variable al inicio de la regla y llegó 'SINO'
  Línea 7: error de sintaxis, se esperaba un valor (número, precio con $ o cadena entre comillas) y la línea terminó
```

La línea 3 usa el nivel de frase (falta `ENTONCES`, lo supone y sigue); la línea 6 trae un `SINO` suelto; la línea 7 se queda sin valor.
Las reglas correctas de las líneas 2, 5 y 8 sí se revisan después de los errores. Para comparar, el parser de primer error (`parser_Haroldmart.py`) solo reporta:

```
Línea 3: error de sintaxis, se esperaba ENTONCES y llegó 'envio' (ID)
El análisis se detiene en el primer error; parser_con_recuperacion.py muestra todos.
```

### 9.3 Archivo con errores léxicos

`pruebas/errores_lexicos.txt` (los mismos de la prueba del Avance 1):

```
// Prueba con errores léxicos a propósito
SI total_compra > $1000 ENTONCES descuento = 5
SI edad # 60 ENTONCES descuento_adulto = 15
MIENTRAS productos_limpieza >= 3 HACER regalo = 1 @
SI precio_leche > $ ENTONCES precio_leche = $25.90
SI piezas_pan < 6. ENTONCES rebaja_pan = 0.5
SI descuento > 0 ENTONCES ESCRIBIR "Promoción aplicada
SI total_compra > $500 / 2 ENTONCES descuento = 2
```

```
Reglas reconocidas: 1 · errores: 6 (6 léxicos, 0 sintácticos)
  Línea 3: error léxico, símbolo inesperado '#'
  Línea 4: error léxico, símbolo inesperado '@'
  Línea 5: error léxico, precio incompleto '$' (falta un número después de '$')
  Línea 6: error léxico, número decimal incompleto '6.' (falta un dígito después del punto)
  Línea 7: error léxico, cadena sin cerrar "Promoción aplicada (falta la comilla de cierre)
  Línea 8: error léxico, '/' sola (los comentarios empiezan con //)
  (se omitieron 5 errores de sintaxis en renglones que ya tienen un error léxico: son consecuencia)
```

### 9.4 Archivo de ejemplo de clase (2 errores en renglones distintos)

`pruebas/errores_ejemplo_clase.txt`:

```
SI total > 500 ENTONCES descuento = 10
SI piezas > 3 envio = 0
SI puntos 100 ENTONCES cupones = 1
MIENTRAS puntos > 100 HACER cupones = 1
```

```
Reglas reconocidas: 3 · errores: 2 (0 léxicos, 2 sintácticos)
  Línea 2: se esperaba ENTONCES antes de 'envio' (lo supuse para seguir)
  Línea 3: error de sintaxis, se esperaba un operador de comparación (>, <, >=, <=) y llegó '100' (NUM)
```

## 10. Tabla de símbolos (adelanto del Avance 3)

`src/tabla_simbolos.py` recorre el árbol y anota, por variable, su tipo (`num`, `dinero` o `cadena`), si es **resultado** (se asigna) o
**dato de la venta** (solo se usa en condiciones) y las líneas donde se define y se usa. Si una variable cambia de tipo, avisa.

`python src/tabla_simbolos.py pruebas/reglas_ok.txt`:

```
Nombre             Tipo     Clase             Definida en  Usada en
total_compra       dinero   dato de la venta  —            3, 4
descuento          num      resultado         3, 4         13
edad               num      dato de la venta  —            6
descuento_adulto   num      resultado         6            —
productos_limpieza num      dato de la venta  —            8
regalo             num      resultado         8            —
precio_leche       dinero   resultado         10           10
piezas_pan         num      dato de la venta  —            11
rebaja_pan         num      resultado         11           —
Total: 9 variables
```

`python src/tabla_simbolos.py pruebas/tipos_distintos.txt`:

```
Nombre             Tipo     Clase             Definida en  Usada en
total_compra       dinero   dato de la venta  —            2
descuento          num      resultado         2, 3         4
edad               num      dato de la venta  —            3
Total: 3 variables
Aviso: Línea 3: 'descuento' era num y ahora recibe dinero ($100)
```

## 11. Lista de cotejo

- [x] Gramática LL(1) final, verificada (sin recursión izquierda ni conflictos) y documentada (secciones 3 a 6).
- [x] Parser descendente recursivo: una función por no terminal (sección 7).
- [x] Con una regla correcta imprime el árbol (sección 9.1).
- [x] Con errores imprime la **lista** de errores con línea y no se detiene (secciones 9.2 a 9.4).
- [x] Probado con 3 reglas reales de mi negocio: descuento, envío gratis y cotización (sección 9.1).
- [x] Todo está en mi repositorio de GitHub.
- [x] Comparé una versión con recursión izquierda y sé cuántos conflictos LL(1) y SLR tiene (sección 6); sé explicar qué es LALR (sección 6).
- [x] Recuperación de errores con modo pánico y nivel de frase, y 2 archivos de prueba con errores (léxico y sintáctico) con su salida.

## 12. Estructura y cómo correr todo

Se necesita Python 3 (sin librerías externas). Desde la carpeta del proyecto:

```
python src/verificar_gramatica.py --tabla                       # verifica la gramática y muestra FIRST, FOLLOW y tabla LL(1)
python src/parser_con_recuperacion.py pruebas/avance2_tres_reglas.txt
python src/parser_con_recuperacion.py pruebas/errores_sintacticos.txt
python src/parser_con_recuperacion.py pruebas/errores_lexicos.txt
python src/parser_Haroldmart.py pruebas/avance2_tres_reglas.txt  # parser simple: se detiene en el primer error
python src/tabla_simbolos.py pruebas/reglas_ok.txt
python src/escaner_Haroldmart.py pruebas/reglas_ok.txt          # escáner del Avance 1 (agrega --traza para ver los AFD)
```

```
src/
  escaner_Haroldmart.py        escáner del Avance 1 (un AFD por token)
  parser_Haroldmart.py         parser descendente recursivo, una función por no terminal
  parser_con_recuperacion.py   modo pánico + nivel de frase + errores léxicos y sintácticos juntos
  verificar_gramatica.py       recursión izquierda, conflictos LL(1) y SLR, FIRST/FOLLOW y tabla LL(1)
  tabla_simbolos.py            tabla de símbolos (Avance 3)
pruebas/                       archivos de entrada (reglas correctas y con errores)
salidas/                       salida real de cada prueba
```
