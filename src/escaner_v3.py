# -*- coding: utf-8 -*-
"""
escaner_v3.py - Escáner de la versión 3 del lenguaje de Haroldmart (con declaraciones)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL, día 1  (PASO 1 de declaraciones_base.py)

Las declaraciones presentan un dato y su tipo ANTES de usarlo:      dinero total_compra
                                                                     porcentaje descuento
Las palabras de tipo (numero, dinero, porcentaje, texto) se leen como ID con el AFD de siempre y aquí se
convierten en el token TIPO. No hace falta otro AFD: son identificadores con un significado especial.

   «dinero» (la palabra) es TIPO ;  «$300» es el token PRECIO.   No se confunden.

Tipos de Haroldmart y cómo se llaman por dentro (lo que usan evaluar_atributos.py y la tabla):
   numero → num      dinero → dinero      porcentaje → porc      texto → cadena

Uso:
    python src/escaner_v3.py pruebas/promos_v3.txt
"""
import argparse
import sys

import escaner_v2
from escaner_Haroldmart import imprimir_resultado

TIPOS = {"numero": "num", "dinero": "dinero", "porcentaje": "porc", "texto": "cadena"}


def escanear(texto):
    """Escáner v2 + palabras de tipo. Devuelve (tokens, errores) igual que el v2: tokens = (línea, tipo, lexema, camino)."""
    tokens, errores = escaner_v2.escanear(texto)
    tokens = [(ln, "TIPO" if tipo == "ID" and lex in TIPOS else tipo, lex, camino) for ln, tipo, lex, camino in tokens]
    return tokens, errores


def main():
    ap = argparse.ArgumentParser(description="Escáner v3 (con declaraciones) del lenguaje de Haroldmart")
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
