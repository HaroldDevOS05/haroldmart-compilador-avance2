#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
escaner.py - Analizador léxico del lenguaje de reglas de Haroldmart
Compiladores (IDS601) - UNEDL 2026B

Uso:
    python escaner.py reglas_ok.txt
    python escaner.py reglas_con_errores.txt
    python escaner.py reglas_ok.txt --traza     (muestra el recorrido de cada AFD)

Cómo funciona:
  * Cada token compuesto tiene su AFD, escrito como TABLA de transiciones
    (igual que las tablas del documento): ID, NUM, PRECIO, CADENA, COMENTARIO
    y OPERADORES.
  * El primer carácter del lexema decide a qué AFD entrar (no se repiten).
  * El AFD avanza mientras exista transición; cuando se atora:
        - si está en un estado de aceptación -> corta el lexema ahí (acepta)
        - si no -> error léxico (se reporta y el escáner SIGUE leyendo)
  * Si un ID es palabra reservada, el token toma el tipo de la reservada.
"""

import argparse
import sys

# ----------------------------------------------------------------------
# Palabras reservadas (en mayúsculas; el lenguaje distingue mayúsculas)
# ----------------------------------------------------------------------
PALABRAS_RESERVADAS = {
    "SI", "ENTONCES", "SINO", "MIENTRAS", "HACER", "PARA", "SEGUN", "CASO",
    "FUNCION", "RETORNAR", "PROCEDIMIENTO", "FIN", "ROMPER", "CONTINUAR",
    "LEER", "ESCRIBIR",
}

# ----------------------------------------------------------------------
# Los AFD como tablas de transiciones
#   tabla[estado][clase] = estado destino
#   clase: 'letra', 'digito' o el carácter mismo ('_', '.', '$', '"', ...)
#   '*'  = cualquier otro carácter (solo si no está listado en la fila)
#   None = se prohíbe ese carácter (el AFD se atora)
#   Si una clase no aparece en la fila -> no hay transición (el AFD se atora)
# ----------------------------------------------------------------------

# letra (letra | dígito | _)*
AFD_ID = {
    "nombre": "ID",
    "tabla": {
        "q0": {"letra": "q1"},
        "q1": {"letra": "q1", "digito": "q1", "_": "q1"},
    },
    "acepta": {"q1": "ID"},
    "errores": {},
}

# dígito dígito* ( . dígito dígito* )?
AFD_NUM = {
    "nombre": "NUM",
    "tabla": {
        "q0": {"digito": "q1"},
        "q1": {"digito": "q1", ".": "q2"},
        "q2": {"digito": "q3"},
        "q3": {"digito": "q3"},
    },
    "acepta": {"q1": "NUM", "q3": "NUM"},
    "errores": {
        "q2": "número decimal incompleto '{lex}' (falta un dígito después del punto)",
    },
}

# $ dígito dígito* ( . dígito dígito* )?
AFD_PRECIO = {
    "nombre": "PRECIO",
    "tabla": {
        "q0": {"$": "q1"},
        "q1": {"digito": "q2"},
        "q2": {"digito": "q2", ".": "q3"},
        "q3": {"digito": "q4"},
        "q4": {"digito": "q4"},
    },
    "acepta": {"q2": "PRECIO", "q4": "PRECIO"},
    "errores": {
        "q1": "precio incompleto '{lex}' (falta un número después de '$')",
        "q3": "precio decimal incompleto '{lex}' (falta un dígito después del punto)",
    },
}

# " (cualquier carácter excepto " y salto de línea)* "
AFD_CADENA = {
    "nombre": "CADENA",
    "tabla": {
        "q0": {'"': "q1"},
        "q1": {'"': "q2", "\n": None, "\r": None, "*": "q1"},
        "q2": {},
    },
    "acepta": {"q2": "CADENA"},
    "errores": {
        "q1": "cadena sin cerrar {lex} (falta la comilla de cierre)",
    },
}

# // (cualquier carácter excepto salto de línea)*      -> se ignora
AFD_COMENTARIO = {
    "nombre": "COMENTARIO",
    "tabla": {
        "q0": {"/": "q1"},
        "q1": {"/": "q2"},
        "q2": {"\n": None, "\r": None, "*": "q2"},
    },
    "acepta": {"q2": "IGNORAR"},
    "errores": {
        "q1": "'/' sola (los comentarios empiezan con //)",
    },
}

# >   <   =   >=   <=
AFD_OPERADORES = {
    "nombre": "OPERADORES",
    "tabla": {
        "q0": {">": "q1", "<": "q3", "=": "q5"},
        "q1": {"=": "q2"},
        "q2": {},
        "q3": {"=": "q4"},
        "q4": {},
        "q5": {},
    },
    "acepta": {
        "q1": "MAYOR", "q2": "MAYORIGUAL",
        "q3": "MENOR", "q4": "MENORIGUAL",
        "q5": "ASIGNA",
    },
    "errores": {},
}


# ----------------------------------------------------------------------
# Funciones del escáner
# ----------------------------------------------------------------------
def clase(c):
    """Clase de un carácter: 'letra' [A-Za-z], 'digito' [0-9] o el mismo carácter."""
    if "a" <= c <= "z" or "A" <= c <= "Z":
        return "letra"
    if "0" <= c <= "9":
        return "digito"
    return c


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
    return None


def correr_afd(afd, texto, i):
    """
    Ejecuta el AFD desde la posición i. Avanza mientras haya transición.
    Devuelve (estado_final, posición_donde_se_atoró, recorrido_de_estados).
    """
    estado = "q0"
    j = i
    camino = [estado]
    while j < len(texto):
        fila = afd["tabla"][estado]
        k = clase(texto[j])
        destino = fila[k] if k in fila else fila.get("*")
        if destino is None:          # sin transición (o carácter prohibido)
            break
        estado = destino
        camino.append(estado)
        j += 1
    return estado, j, camino


def escanear(texto):
    """Recorre todo el texto. Devuelve (tokens, errores); NO se detiene en errores."""
    tokens = []     # (línea, tipo, lexema, recorrido)
    errores = []    # (línea, mensaje)
    linea = 1
    i = 0
    while i < len(texto):
        c = texto[i]

        # Separadores: se ignoran; el salto de línea aumenta el número de línea
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
                tipo = lexema        # la reservada toma su propio tipo
            if tipo != "IGNORAR":    # los comentarios no generan token
                tokens.append((linea, tipo, lexema, camino))
        else:
            mensaje = afd["errores"][estado].format(lex=lexema)
            errores.append((linea, mensaje))

        i = fin                      # sigue leyendo después del lexema (o del error)
    return tokens, errores


def imprimir_resultado(tokens, errores, traza=False):
    encabezado = f"{'LÍNEA':<6}{'TOKEN':<14}{'LEXEMA':<28}"
    print(encabezado + ("RECORRIDO DEL AFD" if traza else ""))
    for linea, tipo, lexema, camino in tokens:
        fila = f"{linea:<6}{tipo:<14}{lexema:<28}"
        if traza:
            fila += "→".join(camino)
        print(fila.rstrip())
    print()
    print(f"Total de tokens: {len(tokens)}")
    if not errores:
        print("Sin errores léxicos.")
    else:
        print(f"Errores léxicos: {len(errores)}")
        for linea, mensaje in errores:
            print(f"  Línea {linea}: error léxico, {mensaje}")


def main():
    ap = argparse.ArgumentParser(description="Escáner del lenguaje de reglas de Haroldmart")
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
