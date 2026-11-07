# -*- coding: utf-8 -*-
"""
escaner_v2.py - Escáner de la versión 2 del lenguaje de Haroldmart (con operaciones)
Compiladores (IDS601) - UNEDL 2026B - AVANCE 3

El escáner del Avance 1 (escaner_Haroldmart.py) se queda IGUAL. Este archivo lo reutiliza
(AFD de ID, PRECIO, CADENA y operadores de comparación) y le agrega lo nuevo:

  * MAS, MENOS, POR, PARIZQ, PARDER   →  + - * ( )       (AFD_ARIT, de un solo carácter)
  * ENTRE                              →  /               (comparte AFD con el comentario //)
  * PORC                               →  15%  12.5%      (el AFD de NUM ahora acepta un % al final)

Lo que cambia respecto al Avance 1:
  * La «/» sola ya NO es error: es la división. Dos «//» siguen siendo comentario (gana el lexema más largo).
  * «%» después de un número es un porcentaje (PORC); un «%» suelto sigue siendo símbolo inesperado.

Uso (muestra los tokens, igual que el escáner del Avance 1):
    python src/escaner_v2.py pruebas/promos_v2.txt
    python src/escaner_v2.py pruebas/promos_v2.txt --traza
"""
import argparse
import copy
import sys

import escaner_Haroldmart as v1
from escaner_Haroldmart import PALABRAS_RESERVADAS, clase, correr_afd, imprimir_resultado

# ---------------- AFD que NO cambian (se reutilizan tal cual) ----------------
AFD_ID = v1.AFD_ID
AFD_PRECIO = v1.AFD_PRECIO
AFD_CADENA = v1.AFD_CADENA
AFD_OPERADORES = v1.AFD_OPERADORES

# ---------------- NUM con porcentaje:  dígito+ ( . dígito+ )? %? ----------------
#   q1 (entero)  -- % --> q5        q3 (decimal) -- % --> q5        q5 acepta PORC
AFD_NUM = copy.deepcopy(v1.AFD_NUM)
AFD_NUM["tabla"]["q1"]["%"] = "q5"
AFD_NUM["tabla"]["q3"]["%"] = "q5"
AFD_NUM["tabla"]["q5"] = {}
AFD_NUM["acepta"]["q5"] = "PORC"

# ---------------- «/» ahora es división; «//» sigue siendo comentario ----------------
#   q0 -- / --> q1 (acepta ENTRE)      q1 -- / --> q2 (acepta IGNORAR: el comentario llega al fin de línea)
AFD_COMENTARIO = copy.deepcopy(v1.AFD_COMENTARIO)
AFD_COMENTARIO["nombre"] = "COMENTARIO / ENTRE"
AFD_COMENTARIO["acepta"] = {"q1": "ENTRE", "q2": "IGNORAR"}
AFD_COMENTARIO["errores"] = {}

# ---------------- NUEVO: + - * ( )  (un carácter cada uno) ----------------
AFD_ARIT = {
    "nombre": "ARITMÉTICOS",
    "tabla": {
        "q0": {"+": "q1", "-": "q2", "*": "q3", "(": "q4", ")": "q5"},
        "q1": {}, "q2": {}, "q3": {}, "q4": {}, "q5": {},
    },
    "acepta": {"q1": "MAS", "q2": "MENOS", "q3": "POR", "q4": "PARIZQ", "q5": "PARDER"},
    "errores": {},
}


def elegir_afd(c):
    """El primer carácter decide el AFD. Devuelve None si no empieza ningún token."""
    k = clase(c)
    if k == "letra":
        return AFD_ID
    if k == "digito":
        return AFD_NUM
    if k == "$":
        return AFD_PRECIO
    if k == '"':
        return AFD_CADENA
    if k == "/":
        return AFD_COMENTARIO
    if k in (">", "<", "="):
        return AFD_OPERADORES
    if k in ("+", "-", "*", "(", ")"):
        return AFD_ARIT
    return None


def escanear(texto):
    """Igual que el escáner del Avance 1, pero con los AFD de la versión 2.
    Devuelve (tokens, errores); NO se detiene en errores.  tokens: (línea, tipo, lexema, recorrido)."""
    tokens, errores = [], []
    linea, i = 1, 0
    while i < len(texto):
        c = texto[i]
        if c == "\n":                     # el salto de línea cuenta una línea más
            linea += 1
            i += 1
            continue
        if c in " \t\r":                  # separadores: se ignoran
            i += 1
            continue
        afd = elegir_afd(c)
        if afd is None:
            errores.append((linea, f"símbolo inesperado '{c}'"))
            i += 1
            continue
        estado, fin, camino = correr_afd(afd, texto, i)
        lexema = texto[i:fin]
        if estado in afd["acepta"]:
            tipo = afd["acepta"][estado]
            if tipo == "ID" and lexema in PALABRAS_RESERVADAS:
                tipo = lexema             # la reservada toma su propio tipo
            if tipo != "IGNORAR":         # los comentarios no generan token
                tokens.append((linea, tipo, lexema, camino))
        else:
            errores.append((linea, afd["errores"][estado].format(lex=lexema)))
        i = fin                           # sigue leyendo después del lexema (o del error)
    return tokens, errores


def main():
    ap = argparse.ArgumentParser(description="Escáner v2 (con operaciones) del lenguaje de Haroldmart")
    ap.add_argument("archivo", help="archivo con las reglas a analizar")
    ap.add_argument("--traza", action="store_true", help="muestra el recorrido de estados del AFD")
    args = ap.parse_args()
    try:
        with open(args.archivo, encoding="utf-8-sig") as f:
            texto = f.read()
    except FileNotFoundError:
        print(f"No se encontró el archivo: {args.archivo}")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    tokens, errores = escanear(texto)
    imprimir_resultado(tokens, errores, args.traza)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
