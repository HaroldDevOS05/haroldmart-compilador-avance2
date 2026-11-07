# Haroldmart · Lenguaje de reglas de promociones — Avance 3 (semántica y código intermedio)

**Compiladores (IDS601) · 6.º semestre · UNEDL 2026B** · Harold Figueroa Márquez

Este repositorio contiene mi compilador de reglas de promociones, en sus tres avances. El **Avance 3** (este) agrega: operaciones en
las reglas (`total_compra * 5%`, `(total_compra - descuento) + envio`), la **tabla de símbolos**, la **notación postfija** y el
**código de tres direcciones**, el **esquema de traducción**, los **atributos con comprobación de tipos** y los dos programas con
errores (léxico y sintáctico) que no detienen el análisis. Del Avance 2 se conservan el parser, la recuperación de errores y la
verificación de la gramática (ahora con la versión 2 del lenguaje).

**Contenido:** [1 Negocio](#1-mi-negocio-y-mi-lenguaje) · [2 Tokens](#2-tokens) · [3 Gramática](#3-gramática-final-versión-2) ·
[4 Verificación](#4-verificación-de-la-gramática) · [5 Tabla LL(1)](#5-first-follow-y-tabla-ll1) · [6 Comparación](#6-comparación-de-versiones-de-la-gramática) ·
[7 Parser y recuperación](#7-parser-y-recuperación-de-errores) · [8 Árbol, postfija y tres direcciones](#8-árbol-postfija-y-código-de-tres-direcciones) ·
[9 Esquema de traducción](#9-esquema-de-traducción) · [10 Atributos y tipos](#10-atributos-val-y-tipo-comprobación-de-tipos) ·
[11 Tabla de símbolos](#11-tabla-de-símbolos) · [12 Programas con errores](#12-los-dos-programas-con-errores) ·
[13 Pruebas cruzadas](#13-pruebas-cruzadas) · [14 Cotejo](#14-lista-de-cotejo-del-avance-3) · [15 Cómo correr](#15-estructura-y-cómo-correr-todo)

---

## 1. Mi negocio y mi lenguaje

Haroldmart es un supermercado cuyo administrador cambia las promociones cada semana. El lenguaje le permite escribir las reglas en
español sencillo. Archivo completo de prueba, `pruebas/promos_v2.txt`:

```
// Promociones de Haroldmart con operaciones (versión 2 del lenguaje)
// 1) Descuento por monto: 5% si la compra pasa de $1000
SI total_compra > $1000 ENTONCES descuento = total_compra * 5% SINO descuento = $0
// 2) Envío gratis desde $500; si no, $2 por kilómetro más una cuota fija de $30
SI total_compra >= $500 ENTONCES envio = $0 SINO envio = km * 2 + $30
// 3) Cotización de mayoreo (más de 100 piezas) y pago final
SI piezas > 100 ENTONCES precio_unitario = $8.50 SINO precio_unitario = $10
cotizacion = precio_unitario * piezas
pago = (total_compra - descuento) + envio
// 4) Adultos mayores con credencial: 15% sobre el pago
SI edad >= 60 ENTONCES descuento_adulto = pago * 15%
// 5) Monedero Haroldmart: se canjean 100 puntos por vuelta
MIENTRAS puntos > 100 HACER puntos = puntos - 100
// 6) Mensaje para el cajero
SI descuento > $0 ENTONCES ESCRIBIR "Promoción aplicada"
```

La **venta de prueba** es lo que mandaría la caja: nombre → (valor, tipo). Hay dos (en `src/evaluar_atributos.py`): la *grande*
(`total_compra = $1200, km = 4, piezas = 120, edad = 65, puntos = 250`) y la *chica* (`$320, 4, 30, 30, 80`).

## 2. Tokens

Escáner del Avance 1 (`src/escaner_Haroldmart.py`, un AFD por token) **sin modificar**. Para las operaciones agregué
`src/escaner_v2.py`, que lo importa y le suma dos AFD nuevos y una extensión (los terminales de la gramática se llaman igual que los tipos de token):

| Token | Expresión regular | Ejemplos | ¿Nuevo? |
|---|---|---|---|
| `SI`, `ENTONCES`, `SINO`, `MIENTRAS`, `HACER`, `ESCRIBIR` (+ reservadas sin uso) | palabra exacta, mayúsculas | `SI` | |
| `ID` | `letra (letra \| dígito \| _)*` | `total_compra` | |
| `NUM` | `dígito+ ( . dígito+ )?` | `10`, `0.5` | |
| `PRECIO` | `$ dígito+ ( . dígito+ )?` | `$1000`, `$8.50` | |
| `PORC` | `dígito+ ( . dígito+ )? %` | `15%`, `5%` | **sí** (AFD de número con `%`) |
| `CADENA` | `" (cualquier carácter excepto " y salto)* "` | `"Promoción aplicada"` | |
| `MAS` `MENOS` `POR` `PARIZQ` `PARDER` | `+` `-` `*` `(` `)` | | **sí** (AFD de operadores aritméticos) |
| `ENTRE` | `/` | `km / 2` | **sí** (el AFD de comentarios `//` ahora acepta un `/` solo) |
| `MAYOR` `MENOR` `MAYORIGUAL` `MENORIGUAL` `ASIGNA` | `>` `<` `>=` `<=` `=` | | |
| (se ignoran) | espacios, saltos de línea, comentarios `// ...` | | |

## 3. Gramática final (versión 2)

Un valor ahora es una **expresión**. La precedencia está en la estructura (`*` y `/` en `Term`, más abajo que `+` y `-`) y la
asociatividad es por la izquierda (`a - b - c` = `(a - b) - c`). Sigue sin recursión izquierda (se usan `ExprR` y `TermR`).

```
   1. Programa → Regla Programa            20. Valor → Expr
   2. Programa → ε                         21. Expr → Term ExprR
   3. Regla → Si                           22. ExprR → MAS Term ExprR
   4. Regla → Mientras                     23. ExprR → MENOS Term ExprR
   5. Regla → Asig                         24. ExprR → ε
   6. Regla → Escribir                     25. Term → Factor TermR
   7. Si → SI Cond ENTONCES Accion Sino    26. TermR → POR Factor TermR
   8. Sino → SINO Accion                   27. TermR → ENTRE Factor TermR
   9. Sino → ε                             28. TermR → ε
  10. Mientras → MIENTRAS Cond HACER Accion 29. Factor → NUM
  11. Accion → Asig                        30. Factor → PRECIO
  12. Accion → Escribir                    31. Factor → PORC
  13. Asig → ID ASIGNA Valor               32. Factor → CADENA
  14. Escribir → ESCRIBIR Valor            33. Factor → ID
  15. Cond → ID Oprel Valor                34. Factor → PARIZQ Expr PARDER
  16-19. Oprel → MAYOR | MENOR | MAYORIGUAL | MENORIGUAL
```

Decisiones: lista de reglas por la derecha; `SINO` factorizado (`Sino → SINO Accion | ε`, sin «else colgante»); los paréntesis solo
agrupan (no aparecen en el árbol).

## 4. Verificación de la gramática

Salida real de `python src/verificar_gramatica.py` (el `verificar_base.py` del profesor con mi gramática). La primera es la
**final**; las demás son las comparaciones de la sección 6.

```
== MI GRAMÁTICA v2 (final, con operaciones) (34 reglas)
   Recursión izquierda: no
   Conflictos LL(1):    0
   Conflictos SLR:      0 (en 58 estados)
   → SIRVE para nuestro parser LL(1) · SIRVE para SLR
== Versión 1 (Avance 2, sin operaciones) (22 reglas)
   Recursión izquierda: no
   Conflictos LL(1):    0
   Conflictos SLR:      0 (en 36 estados)
   → SIRVE para nuestro parser LL(1) · SIRVE para SLR
== VERSIÓN A: con recursión izquierda en la lista de reglas (Programa → Programa Regla) (34 reglas)
   Recursión izquierda: Programa
   Conflictos LL(1):    4
      celda [Programa, ESCRIBIR]: reglas 1, 2
      celda [Programa, ID]: reglas 1, 2
      celda [Programa, MIENTRAS]: reglas 1, 2
   Conflictos SLR:      0 (en 57 estados)
   → NO sirve para LL(1) · SIRVE para SLR
== VERSIÓN B: sin factorizar el SINO (dos reglas Si que empiezan igual) (33 reglas)
   Recursión izquierda: no
   Conflictos LL(1):    1
      celda [Si, SI]: reglas 32, 33
   Conflictos SLR:      0 (en 57 estados)
   → NO sirve para LL(1) · SIRVE para SLR
== VERSIÓN C: Expr con recursión izquierda (Expr → Expr + Term, Term → Term * Factor) (32 reglas)
   Recursión izquierda: Expr, Term
   Conflictos LL(1):    12
      celda [Expr, CADENA]: reglas 21, 22, 23
      celda [Expr, ID]: reglas 21, 22, 23
      celda [Expr, NUM]: reglas 21, 22, 23
   Conflictos SLR:      0 (en 52 estados)
   → NO sirve para LL(1) · SIRVE para SLR
```

**Mi gramática final: sin recursión izquierda, 0 conflictos LL(1) y 0 conflictos SLR.**

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
  FIRST(Valor) = { ID, NUM, PRECIO, PORC, CADENA, PARIZQ }
  FIRST(Expr) = { ID, NUM, PRECIO, PORC, CADENA, PARIZQ }
  FIRST(ExprR) = { MAS, MENOS, ε }
  FIRST(Term) = { ID, NUM, PRECIO, PORC, CADENA, PARIZQ }
  FIRST(TermR) = { POR, ENTRE, ε }
  FIRST(Factor) = { ID, NUM, PRECIO, PORC, CADENA, PARIZQ }

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
  FOLLOW(Oprel) = { ID, NUM, PRECIO, PORC, CADENA, PARIZQ }
  FOLLOW(Valor) = { SI, ENTONCES, SINO, MIENTRAS, HACER, ID, ESCRIBIR, $ }
  FOLLOW(Expr) = { SI, ENTONCES, SINO, MIENTRAS, HACER, ID, ESCRIBIR, PARDER, $ }
  FOLLOW(ExprR) = { SI, ENTONCES, SINO, MIENTRAS, HACER, ID, ESCRIBIR, PARDER, $ }
  FOLLOW(Term) = { SI, ENTONCES, SINO, MIENTRAS, HACER, ID, ESCRIBIR, MAS, MENOS, PARDER, $ }
  FOLLOW(TermR) = { SI, ENTONCES, SINO, MIENTRAS, HACER, ID, ESCRIBIR, MAS, MENOS, PARDER, $ }
  FOLLOW(Factor) = { SI, ENTONCES, SINO, MIENTRAS, HACER, ID, ESCRIBIR, MAS, MENOS, POR, ENTRE, PARDER, $ }
```

Tabla LL(1) (cada celda es el número de regla; vacía = error). Ninguna celda tiene dos reglas:

| | SI | ENTONCES | SINO | MIENTRAS | HACER | ID | ASIGNA | ESCRIBIR | MAYOR | MENOR | MAYORIGUAL | MENORIGUAL | MAS | MENOS | POR | ENTRE | NUM | PRECIO | PORC | CADENA | PARIZQ | PARDER | $ |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| **Programa** | 1 |   |   | 1 |   | 1 |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   | 2 |
| **Regla** | 3 |   |   | 4 |   | 5 |   | 6 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| **Si** | 7 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| **Sino** | 9 |   | 8 | 9 |   | 9 |   | 9 |   |   |   |   |   |   |   |   |   |   |   |   |   |   | 9 |
| **Mientras** |   |   |   | 10 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| **Accion** |   |   |   |   |   | 11 |   | 12 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| **Asig** |   |   |   |   |   | 13 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| **Escribir** |   |   |   |   |   |   |   | 14 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| **Cond** |   |   |   |   |   | 15 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| **Oprel** |   |   |   |   |   |   |   |   | 16 | 17 | 18 | 19 |   |   |   |   |   |   |   |   |   |   |   |
| **Valor** |   |   |   |   |   | 20 |   |   |   |   |   |   |   |   |   |   | 20 | 20 | 20 | 20 | 20 |   |   |
| **Expr** |   |   |   |   |   | 21 |   |   |   |   |   |   |   |   |   |   | 21 | 21 | 21 | 21 | 21 |   |   |
| **ExprR** | 24 | 24 | 24 | 24 | 24 | 24 |   | 24 |   |   |   |   | 22 | 23 |   |   |   |   |   |   |   | 24 | 24 |
| **Term** |   |   |   |   |   | 25 |   |   |   |   |   |   |   |   |   |   | 25 | 25 | 25 | 25 | 25 |   |   |
| **TermR** | 28 | 28 | 28 | 28 | 28 | 28 |   | 28 |   |   |   |   | 28 | 28 | 26 | 27 |   |   |   |   |   | 28 | 28 |
| **Factor** |   |   |   |   |   | 33 |   |   |   |   |   |   |   |   |   |   | 29 | 30 | 31 | 32 | 34 |   |   |


## 6. Comparación de versiones de la gramática

| Versión | Recursión izquierda | Conflictos LL(1) | Conflictos SLR |
|---|---|---|---|
| **Final v2** | no | **0** | **0** (58 estados) |
| Versión 1 (Avance 2, sin operaciones) | no | 0 | 0 (36 estados) |
| **A**: `Programa → Programa Regla \| ε` | sí (`Programa`) | 4 | 0 |
| **B**: `Si` sin factorizar | no | 1 (`[Si, SI]`) | 0 |
| **C (nueva)**: `Expr → Expr + Term`, `Term → Term * Factor` | sí (`Expr`, `Term`) | 12 | 0 (52 estados) |

**Por qué LR sí acepta A y C y LL(1) no.** Un parser LL(1) decide qué regla usar mirando *un solo token antes de empezar* el no terminal. En
`Expr → Expr + Term | Term`, con un `ID` las dos reglas empiezan igual (conflicto) y la función `expr()` se llamaría a sí misma sin consumir
nada: recursión infinita. Un parser LR apila símbolos y *reduce* hasta ver el lado derecho completo, así que no adivina al principio y la
recursión izquierda no lo cicla (incluso le conviene: `Expr → Expr + Term` ya agrupa por la izquierda). Por eso en LL(1) la
recursión izquierda se quita con `ExprR` y el ciclo `while` reconstruye la asociatividad por la izquierda. **LALR(1)** (yacc/bison) une los
estados LR con el mismo núcleo: tabla tan chica como la SLR pero más precisa; acepta más gramáticas que LL(1) y se usa porque esas
herramientas *generan* el parser, mientras que el LL(1) a mano se escribe una función por no terminal.

## 7. Parser y recuperación de errores

- `src/parser_Haroldmart.py` (Avance 2): parser descendente recursivo, una función por no terminal, se detiene en el primer error.
- `src/parser_con_recuperacion.py` (Avance 2): hereda del anterior y agrega **modo pánico** (salta hasta el inicio de la siguiente regla),
  **nivel de frase** (si falta `ENTONCES` o `HACER` lo supone y sigue) y reporta errores léxicos y sintácticos juntos, ordenados por línea.
- `src/parser_v2.py` (**Avance 3**): hereda de los dos y solo reescribe lo nuevo: `valor()`, `expr()`, `term()` y `factor()`. `expr()` y
  `term()` son ciclos `while` (asociatividad izquierda); `factor()` acepta número, precio, porcentaje, cadena, variable o `( Expr )`.
  El árbol es de **sintaxis abstracta**: cada operación es un nodo (`*`, `+`...) con sus dos operandos como hijos.
- **Errores en cascada:** un error de sintaxis en un renglón que ya tiene un error léxico se omite (es consecuencia del símbolo
  desconocido) y se avisa cuántos fueron.

## 8. Árbol, postfija y código de tres direcciones

`python src/parser_v2.py pruebas/promos_v2.txt` imprime el árbol de cada regla (fragmento: la regla `pago = (total_compra - descuento) + envio`;
los paréntesis no son nodo, el operador sí):

```
├─ Regla
│  └─ Asig
│     ├─ ID: pago
│     ├─ ASIGNA: =
│     └─ Valor
│        └─ +
│           ├─ -
│           │  ├─ ID: total_compra
│           │  └─ ID: descuento
│           └─ ID: envio
```

`python src/codigo_intermedio.py pruebas/promos_v2.txt` (completo en `salidas/a3_postfija_y_tres_direcciones.txt`):

**Notación postfija** (postorden: operandos y luego operador, sin paréntesis):

```
  Línea 3: total_compra * 5%   →   Postfija: total_compra 5% *
  Línea 5: km * 2 + $30   →   Postfija: km 2 * $30 +
  Línea 8: precio_unitario * piezas   →   Postfija: precio_unitario piezas *
  Línea 9: total_compra - descuento + envio   →   Postfija: total_compra descuento - envio +
  Línea 11: pago * 15%   →   Postfija: pago 15% *
  Línea 13: puntos - 100   →   Postfija: puntos 100 -
```

**Código de tres direcciones** (un solo generador: los temporales `t1…` y las etiquetas `L1…` no se repiten entre reglas; `SI` y
`MIENTRAS` usan `ifFalse … goto`):

```
Línea 3: SI total_compra > $1000 ENTONCES descuento = total_compra * 5% SINO descuento = $0
    ifFalse total_compra > $1000 goto L1
    t1 = total_compra * 5%
    descuento = t1
    goto L2
L1:
    descuento = $0
L2:
Línea 5: SI total_compra >= $500 ENTONCES envio = $0 SINO envio = km * 2 + $30
    ifFalse total_compra >= $500 goto L3
    envio = $0
    goto L4
L3:
    t2 = km * 2
    t3 = t2 + $30
    envio = t3
L4:
Línea 7: SI piezas > 100 ENTONCES precio_unitario = $8.50 SINO precio_unitario = $10
    ifFalse piezas > 100 goto L5
    precio_unitario = $8.50
    goto L6
L5:
    precio_unitario = $10
L6:
Línea 8: cotizacion = precio_unitario * piezas
    t4 = precio_unitario * piezas
    cotizacion = t4
Línea 9: pago = (total_compra - descuento) + envio
    t5 = total_compra - descuento
    t6 = t5 + envio
    pago = t6
Línea 11: SI edad >= 60 ENTONCES descuento_adulto = pago * 15%
    ifFalse edad >= 60 goto L7
    t7 = pago * 15%
    descuento_adulto = t7
L7:
Línea 13: MIENTRAS puntos > 100 HACER puntos = puntos - 100
L8:
    ifFalse puntos > 100 goto L9
    t8 = puntos - 100
    puntos = t8
    goto L8
L9:
Línea 15: SI descuento > $0 ENTONCES ESCRIBIR "Promoción aplicada"
    ifFalse descuento > $0 goto L10
    escribir "Promoción aplicada"
L10:
```

## 9. Esquema de traducción

`src/esquema_traduccion.py`: la gramática de expresiones con la acción `emitir(...)` colocada **después** del segundo operando. Traduce a
postfija **mientras analiza, en una pasada y sin armar el árbol**. La diferencia con la definición dirigida por sintaxis es *cuándo*:
si `emitir(op)` fuera antes de `Term`, el operador saldría primero (prefija).

```
Expresión: precio * 2 + 10
Acciones, en el orden en que se ejecutan:
  1. emitir(precio) → precio
  2. emitir(2) → precio 2
  3. emitir(*) → precio 2 *
  4. emitir(10) → precio 2 * 10
  5. emitir(+) → precio 2 * 10 +
Postfija: precio 2 * 10 +
…
Expresión: precio * * 2
Error: se esperaba un valor y llegó '*'
```

`python src/esquema_traduccion.py --comparar` confirma que el esquema y la postfija del árbol dan lo mismo:

```
Expresión                                Esquema (en una pasada)                     Postfija del árbol                          ¿Igual?
precio * 2 + 10                          precio 2 * 10 +                             precio 2 * 10 +                             sí
(precio - descuento) * cantidad + envio  precio descuento - cantidad * envio +       precio descuento - cantidad * envio +       sí
total_compra * 5%                        total_compra 5% *                           total_compra 5% *                           sí
km * 2 + $30                             km 2 * $30 +                                km 2 * $30 +                                sí
puntos - 100                             puntos 100 -                                puntos 100 -                                sí
a - b - c                                a b - c -                                   a b - c -                                   sí
a + b * c - (d - e) / f                  a b c * + d e - f / -                       a b c * + d e - f / -                       sí

El esquema y el árbol dan lo mismo en las 7 expresiones.
```

## 10. Atributos `val` y `tipo`, comprobación de tipos

`src/evaluar_atributos.py`: definición dirigida por sintaxis con atributos **sintetizados** (cada nodo calcula `val` y `tipo` con los de sus hijos).

| Regla | `val` | `tipo` |
|---|---|---|
| `Factor → NUM` / `PRECIO` / `PORC` / `CADENA` | el número / la cantidad / `15% → 0.15` / el texto | `num` / `dinero` / `porc` / `cadena` |
| `Factor → ID` | su valor en la venta | su tipo en la venta |
| `E → E1 op T` | `E1.val op T.val` | `combinar(E1.tipo, op, T.tipo)` |

`combinar()` es la comprobación de tipos: `dinero ± dinero → dinero`, `dinero × porc → dinero`, `dinero ÷ dinero → num`, `num ± dinero → dinero`.
No tienen sentido (**error de tipo**, con su línea; es un error *semántico*: la sintaxis está bien): sumar porcentaje con dinero, multiplicar
dinero por dinero, operar con una cadena, dividir un número entre dinero, dividir entre cero, comparar dinero con un porcentaje, o usar un dato que la venta no trae.
Un error de tipo no detiene el programa: se reporta y se sigue con la regla siguiente.

`python src/evaluar_atributos.py pruebas/promos_v2.txt --venta grande --anotado` (aplica las promociones a la venta; `--anotado` muestra el árbol con los atributos):

```
Venta de prueba (grande): total_compra = $1200, km = 4, piezas = 120, edad = 65, puntos = 250

Aplicando las promociones:
  línea 3: descuento = $60 (dinero)
        *   [val = $60, tipo = dinero]
        ├─ total_compra   [val = $1200, tipo = dinero]
        └─ 5%   [val = 5%, tipo = porc]
  línea 5: envio = $0 (dinero)
  línea 7: precio_unitario = $8.5 (dinero)
  línea 8: cotizacion = $1020 (dinero)
        *   [val = $1020, tipo = dinero]
        ├─ precio_unitario   [val = $8.5, tipo = dinero]
        └─ piezas   [val = 120, tipo = num]
  línea 9: pago = $1140 (dinero)
        +   [val = $1140, tipo = dinero]
        ├─ -   [val = $1140, tipo = dinero]
        │  ├─ total_compra   [val = $1200, tipo = dinero]
        │  └─ descuento   [val = $60, tipo = dinero]
        └─ envio   [val = $0, tipo = dinero]
  línea 11: descuento_adulto = $171 (dinero)
        *   [val = $171, tipo = dinero]
        ├─ pago   [val = $1140, tipo = dinero]
        └─ 15%   [val = 15%, tipo = porc]
  línea 13: puntos = 150 (num)
        -   [val = 150, tipo = num]
        ├─ puntos   [val = 250, tipo = num]
        └─ 100   [val = 100, tipo = num]
  línea 13: puntos = 50 (num)
        -   [val = 50, tipo = num]
        ├─ puntos   [val = 150, tipo = num]
        └─ 100   [val = 100, tipo = num]
  línea 15: ESCRIBIR "Promoción aplicada"

Reglas ejecutadas: 8 · errores de tipo: 0
```

Con la venta **chica** (`--venta chica`) las condiciones cambian y salen otros resultados:

```
Venta de prueba (chica): total_compra = $320, km = 4, piezas = 30, edad = 30, puntos = 80

Aplicando las promociones:
  línea 3: descuento = $0 (dinero)
  línea 5: envio = $38 (dinero)
  línea 7: precio_unitario = $10 (dinero)
  línea 8: cotizacion = $300 (dinero)
  línea 9: pago = $358 (dinero)

Reglas ejecutadas: 8 · errores de tipo: 0
```

Errores de tipo (`pruebas/error_de_tipo.txt`):

```
Venta de prueba (grande): total_compra = $1200, km = 4, piezas = 120, edad = 65, puntos = 250

Aplicando las promociones:
  Error de tipo: Línea 2: no se puede sumar un porcentaje con dinero
  Error de tipo: Línea 3: no se puede multiplicar dinero por dinero
  Error de tipo: Línea 4: no se puede sumar con una cadena de texto
  Error de tipo: Línea 5: división entre cero
  Error de tipo: Línea 6: no se puede dividir un número entre dinero
  Error de tipo: Línea 7: no se puede comparar dinero con un porcentaje
  Error de tipo: Línea 8: la venta no trae el dato 'saldo_a_favor'
  línea 9: bien = $180 (dinero)

Reglas ejecutadas: 1 · errores de tipo: 7
```

## 11. Tabla de símbolos

`src/tabla_simbolos.py` (retomado del Avance 2 y adaptado a la versión 2). Recorre el árbol y anota, por variable: **tipo**, **clase**
(*resultado* = la calcula una regla; *dato de la venta* = la manda la caja; *dato y resultado* = viene de la caja y una regla lo cambia),
**líneas donde se define** (recibe un valor) y **líneas donde se usa** (se lee en una condición o dentro de una expresión). Como ahora un valor es una
expresión, el tipo se **infiere** con las reglas de `combinar()` (punto fijo); los datos de la venta toman su tipo de la venta de prueba. Si una variable
cambia de tipo, avisa. `python src/tabla_simbolos.py pruebas/promos_v2.txt`:

```
Nombre             Tipo     Clase             Definida en  Usada en
descuento          dinero   resultado         3            9, 15
total_compra       dinero   dato de la venta  —            3, 5, 9
envio              dinero   resultado         5            9
km                 num      dato de la venta  —            5
precio_unitario    dinero   resultado         7            8
piezas             num      dato de la venta  —            7, 8
cotizacion         dinero   resultado         8            —
pago               dinero   resultado         9            11
descuento_adulto   dinero   resultado         11           —
edad               num      dato de la venta  —            11
puntos             num      dato y resultado  13           13
Total: 11 variables
```

`pruebas/promos_tipos_distintos.txt` (una variable que cambia de tipo):

```
Nombre             Tipo     Clase             Definida en  Usada en
descuento          porc     resultado         2, 3         4
total_compra       dinero   dato de la venta  —            2
edad               num      dato de la venta  —            3
Total: 3 variables
Aviso: Línea 3: 'descuento' era porc y ahora recibe dinero ($100)
```

## 12. Los dos programas con errores

El análisis **no se detiene en el primer error**: lista todos con su línea y sigue. La tabla se arma con las reglas que sí se reconocieron.

### 12.1 Programa 1: errores léxicos (`pruebas/avance3_error_lexico.txt`)

```
// AVANCE 3 · Programa 1: errores LÉXICOS (símbolos que el lenguaje no conoce)
SI total_compra > $1000 ENTONCES descuento = total_compra * 5%
SI edad >= 60 @ ENTONCES descuento_adulto = pago * 15%
SI precio_leche > $ ENTONCES precio_leche = $25.90
SI piezas > 100 ENTONCES precio_unitario = $8.50 SINO precio_unitario = $10
MIENTRAS puntos > 100 HACER puntos = puntos - 100 #
```

Salida de `python src/tabla_simbolos.py pruebas/avance3_error_lexico.txt`:

```
Nombre             Tipo     Clase             Definida en  Usada en
descuento          dinero   resultado         2            —
total_compra       dinero   dato de la venta  —            2
precio_unitario    dinero   resultado         5            —
piezas             num      dato de la venta  —            5
Total: 4 variables

Errores del archivo: 3 (3 léxicos, 0 sintácticos)
  Línea 3: error léxico, símbolo inesperado '@'
  Línea 4: error léxico, precio incompleto '$' (falta un número después de '$')
  Línea 6: error léxico, símbolo inesperado '#'
  (se omitió 1 error de sintaxis en un renglón que ya tiene un error léxico: es consecuencia, un error en cascada)
La tabla solo incluye las reglas sin errores léxicos (reglas reconocidas: 2).
```

Tres símbolos que el lenguaje no conoce (`@`, un `$` sin número, `#`). Las variables `descuento_adulto` (línea 3), `precio_leche` (línea 4) y la
regla de `puntos` (línea 6) **no están en la tabla** porque sus reglas tienen un error léxico y no son confiables. El parser, además, tropezó con uno de esos
símbolos, pero ese **error en cascada** se omite (se avisa en la última línea de la salida): es consecuencia del símbolo desconocido, ya reportado por el escáner.

### 12.2 Programa 2: errores sintácticos (`pruebas/avance3_error_sintactico.txt`)

```
// AVANCE 3 · Programa 2: errores SINTÁCTICOS en renglones distintos
SI total_compra > $1000 ENTONCES descuento = total_compra * 5%
SI total_compra >= $500 envio = $0 SINO envio = km * 2 + $30
SI piezas 100 ENTONCES precio_unitario = $8.50
pago = (total_compra - descuento * 2 + envio
MIENTRAS puntos > 100 HACER puntos = puntos - 100
SINO descuento = 0
SI edad >= 60 ENTONCES descuento_adulto = pago * 15% +
ESCRIBIR "Promoción aplicada"
```

Salida de `python src/tabla_simbolos.py pruebas/avance3_error_sintactico.txt`:

```
Nombre             Tipo     Clase             Definida en  Usada en
descuento          dinero   resultado         2            —
total_compra       dinero   dato de la venta  —            2, 3
envio              dinero   resultado         3            —
km                 num      dato de la venta  —            3
puntos             num      dato y resultado  6            6
Total: 5 variables

Errores del archivo: 5 (0 léxicos, 5 sintácticos)
  Línea 3: se esperaba ENTONCES antes de 'envio' (lo supuse para seguir)
  Línea 4: error de sintaxis, se esperaba un operador de comparación (>, <, >=, <=) y llegó '100' (NUM)
  Línea 5: error de sintaxis, se esperaba «)» y la línea terminó
  Línea 7: error de sintaxis, se esperaba SI, MIENTRAS, ESCRIBIR o una variable al inicio de la regla y llegó 'SINO'
  Línea 8: error de sintaxis, se esperaba un valor (número, precio como $300, porcentaje como 15%, variable o «(») y la línea terminó
La tabla solo incluye las reglas sin errores léxicos (reglas reconocidas: 4).
```

Cinco errores distintos: falta `ENTONCES` (línea 3, el nivel de frase lo **supone** y la regla sí entra a la tabla), falta el operador de comparación (4), falta
`)` (5), un `SINO` suelto (7) y una expresión sin segundo operando (8). Las reglas de las líneas 4, 5 y 8 no se reconocieron, por eso `precio_unitario`, `pago` y
`descuento_adulto` no aparecen en la tabla; las reglas buenas de las líneas 2, 6 y 9 sí se revisaron después de los errores.

## 13. Pruebas cruzadas

`python src/pruebas_cruzadas.py` compara unas piezas contra otras:

```
1. Parser recursivo vs tabla LL(1): 300 programas al azar (+ 300 alterados) → 0 diferencias
2. Esquema de traducción vs postfija del árbol: 7/7 iguales
3. Tres direcciones ejecutado vs evaluador (venta grande): 11/11 variables iguales
3. Tres direcciones ejecutado vs evaluador (venta chica): 10/10 variables iguales

Todo coincide.
```

1. El parser recursivo y un parser dirigido por la tabla LL(1) aceptan/rechazan lo mismo en 300 programas generados al azar con la gramática (y 300 alterados).
2. El esquema de traducción y la postfija del árbol coinciden.
3. El código de tres direcciones, ejecutado con una máquina pequeña, deja las mismas variables que el evaluador de atributos.

## 14. Lista de cotejo del Avance 3

- [x] Tabla de símbolos con nombre, tipo, clase y líneas donde se define y se usa (sección 11).
- [x] Errores léxicos con su línea, sin detener el análisis (sección 12.1).
- [x] Errores sintácticos en una lista, con recuperación de errores (sección 12.2).
- [x] Dos programas con error (léxico y sintáctico) con su salida (sección 12).
- [x] Esquema de traducción con postfija correcta (sección 9).
- [x] Postfija y tres direcciones del árbol (sección 8) y atributos con tipos (sección 10).
- [x] Todo documentado en este README y subido a GitHub.

## 15. Estructura y cómo correr todo

Se necesita Python 3 (sin librerías externas). Todo de una vez, guardando cada salida en `salidas/`: `bash correr_todo.sh`. O por partes:

```
python src/verificar_gramatica.py --tabla                         # gramática v2 y versiones A, B, C
python src/escaner_v2.py pruebas/promos_v2.txt                    # tokens (agrega --traza para ver los AFD)
python src/parser_v2.py pruebas/promos_v2.txt                     # árbol, o lista de errores
python src/codigo_intermedio.py pruebas/promos_v2.txt             # postfija y tres direcciones
python src/esquema_traduccion.py "precio * 2 + 10"                # esquema de traducción (--comparar)
python src/evaluar_atributos.py pruebas/promos_v2.txt --venta grande --anotado
python src/tabla_simbolos.py pruebas/promos_v2.txt
python src/tabla_simbolos.py pruebas/avance3_error_lexico.txt     # programa con errores léxicos
python src/tabla_simbolos.py pruebas/avance3_error_sintactico.txt # programa con errores sintácticos
python src/pruebas_cruzadas.py
```

```
src/
  escaner_Haroldmart.py        escáner del Avance 1 (un AFD por token)
  escaner_v2.py                escáner v2: + PORC, + - * / ( )                                  (Avance 3)
  parser_Haroldmart.py         parser descendente recursivo, una función por no terminal        (Avance 2)
  parser_con_recuperacion.py   modo pánico + nivel de frase + errores léxicos y sintácticos      (Avance 2)
  parser_v2.py                 parser con expresiones, hereda de los dos anteriores              (Avance 3)
  verificar_gramatica.py       recursión izquierda, conflictos LL(1) y SLR, FIRST/FOLLOW, tabla (Avances 2 y 3)
  codigo_intermedio.py         postfija y código de tres direcciones                             (Avance 3)
  esquema_traduccion.py        esquema de traducción en una pasada                               (Avance 3)
  evaluar_atributos.py         atributos val y tipo, errores de tipo, aplica las promociones     (Avance 3)
  tabla_simbolos.py            tabla de símbolos con inferencia de tipos                         (Avance 3)
  pruebas_cruzadas.py          comprobaciones automáticas entre piezas                           (Avance 3)
pruebas/                       archivos de entrada (correctos y con errores)
salidas/                       salida real de cada prueba (a3_* = Avance 3)
correr_todo.sh                 corre todo y guarda las salidas
```
