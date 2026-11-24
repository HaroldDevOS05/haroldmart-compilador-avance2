# -*- coding: utf-8 -*-
"""
escaner_v4.py - Escáner FINAL del lenguaje de Haroldmart (versión 4)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL

Reúne todo lo anterior y agrega lo que faltaba para la entrega:
  * (v2) PORC (15%), MAS MENOS POR PARIZQ PARDER, y la «/» como división (ENTRE)
  * (v3) las palabras de tipo numero, dinero, porcentaje, texto se leen como el token TIPO
  * (v4) COMA «,»              para separar los datos de una función:  aplicar_descuento(total_compra, 10%)
         IGUAL «==» y DIFERENTE «!=»   para reglas como «SI tipo_cliente == "frecuente"»

AFD de OPERADORES (v4). Estados: q0 inicio. Todos aceptan salvo q7:
      q0 -- > --> q1 (MAYOR)      q1 -- = --> q2 (MAYORIGUAL)
      q0 -- < --> q3 (MENOR)      q3 -- = --> q4 (MENORIGUAL)
      q0 -- = --> q5 (ASIGNA)     q5 -- = --> q6 (IGUAL)          ← NUEVO
      q0 -- ! --> q7 (error: «!» sola)   q7 -- = --> q8 (DIFERENTE)   ← NUEVO
Como el escáner se queda con el lexema MÁS LARGO, «==» es IGUAL (no dos ASIGNA) y «=» solo es ASIGNA.

Uso:
    python src/escaner_v4.py pruebas/promos_v4.txt            (agrega --traza para ver el recorrido de estados)
"""
import argparse
import copy
import sys

import escaner_Haroldmart as v1
import escaner_v2 as v2
from escaner_Haroldmart import PALABRAS_RESERVADAS, clase, correr_afd, imprimir_resultado

TIPOS = {"numero": "num", "dinero": "dinero", "porcentaje": "porc", "texto": "cadena"}

AFD_ID, AFD_PRECIO, AFD_CADENA, AFD_NUM, AFD_COMENTARIO = v2.AFD_ID, v2.AFD_PRECIO, v2.AFD_CADENA, v2.AFD_NUM, v2.AFD_COMENTARIO

# ---------------- OPERADORES con == y != ----------------
AFD_OPERADORES = copy.deepcopy(v1.AFD_OPERADORES)
AFD_OPERADORES["tabla"]["q0"]["!"] = "q7"
AFD_OPERADORES["tabla"]["q5"] = {"=": "q6"}
AFD_OPERADORES["tabla"]["q6"] = {}
AFD_OPERADORES["tabla"]["q7"] = {"=": "q8"}
AFD_OPERADORES["tabla"]["q8"] = {}
AFD_OPERADORES["acepta"]["q6"] = "IGUAL"
AFD_OPERADORES["acepta"]["q8"] = "DIFERENTE"
AFD_OPERADORES["errores"]["q7"] = "'!' sola (para «distinto» se escribe !=)"

# ---------------- ARITMÉTICOS + la coma ----------------
AFD_ARIT = copy.deepcopy(v2.AFD_ARIT)
AFD_ARIT["nombre"] = "ARITMÉTICOS Y COMA"
AFD_ARIT["tabla"]["q0"][","] = "q6"
AFD_ARIT["tabla"]["q6"] = {}
AFD_ARIT["acepta"]["q6"] = "COMA"


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
    if k in (">", "<", "=", "!"):
        return AFD_OPERADORES
    if k in ("+", "-", "*", "(", ")", ","):
        return AFD_ARIT
    return None


def escanear(texto):
    """Devuelve (tokens, errores); NO se detiene en errores.  tokens: (línea, tipo, lexema, recorrido de estados)."""
    tokens, errores = [], []
    linea, i = 1, 0
    while i < len(texto):
        c = texto[i]
        if c == "\n":
            linea += 1
            i += 1
            continue
        if c in " \t\r":
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
                tipo = lexema
            elif tipo == "ID" and lexema in TIPOS:
                tipo = "TIPO"
            if tipo != "IGNORAR":
                tokens.append((linea, tipo, lexema, camino))
        else:
            errores.append((linea, afd["errores"][estado].format(lex=lexema)))
        i = fin
    return tokens, errores


def main():
    ap = argparse.ArgumentParser(description="Escáner final (v4) del lenguaje de Haroldmart")
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
