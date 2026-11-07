# -*- coding: utf-8 -*-
"""
pruebas_cruzadas.py - Comprobaciones automáticas del Avance 3 (compara unas piezas contra otras)
Compiladores (IDS601) - UNEDL 2026B

  1. PARSER vs TABLA LL(1): genera programas al azar con la gramática v2, los reescribe como texto y comprueba que
     el parser recursivo descendente (parser_v2) y un parser dirigido por la tabla LL(1) (la de verificar_gramatica)
     los aceptan los dos, sin errores.  También con un token cambiado al azar: los dos deben rechazarlo.
  2. ESQUEMA vs ÁRBOL: la postfija del esquema de traducción (una pasada) = la postfija del árbol.
  3. TRES DIRECCIONES vs EVALUADOR: se ejecuta el código de tres direcciones con una máquina pequeña y las
     variables finales deben ser las mismas que las del evaluador de atributos (venta grande y chica).

Uso:  python src/pruebas_cruzadas.py
"""
import random
import sys

from verificar_gramatica import TU_GRAMATICA, first_follow, EPS
from parser_v2 import analizar, leer_archivo
from escaner_v2 import escanear
from codigo_intermedio import TresDirecciones
from evaluar_atributos import aplicar_promociones, VENTAS, OPERACIONES, COMPARACIONES
from esquema_traduccion import Traductor, postfija_del_arbol

LEXEMAS = {"SI": "SI", "ENTONCES": "ENTONCES", "SINO": "SINO", "MIENTRAS": "MIENTRAS", "HACER": "HACER",
           "ESCRIBIR": "ESCRIBIR", "ASIGNA": "=", "MAYOR": ">", "MENOR": "<", "MAYORIGUAL": ">=", "MENORIGUAL": "<=",
           "NUM": "7", "PRECIO": "$30", "PORC": "5%", "CADENA": '"hola"', "ID": "x", "MAS": "+", "MENOS": "-",
           "POR": "*", "ENTRE": "/", "PARIZQ": "(", "PARDER": ")"}


def generar(G, simbolo, rng, prof=0):
    """Deriva al azar una lista de terminales desde 'simbolo' (con tope de profundidad para que termine)."""
    if simbolo not in {A for A, _ in G}:
        return [simbolo]
    reglas = [der for A, der in G if A == simbolo]
    if prof > 6:                                    # ya muy hondo: prefiere la regla más corta
        reglas = [min(reglas, key=len)]
    der = rng.choice(reglas)
    out = []
    for s in der:
        out += generar(G, s, rng, prof + 1)
    return out


def parser_ll1(G, tipos):
    """Parser dirigido por tabla con pila: acepta o rechaza la lista de tipos de token."""
    nts, FI, FO, first_de = first_follow(G)
    tabla = {}
    for k, (A, der) in enumerate(G):
        f = first_de(der)
        for a in (f - {EPS}) | (FO[A] if EPS in f else set()):
            tabla[(A, a)] = k
    entrada, pila, i = tipos + ["$"], ["$", nts[0]], 0
    while pila:
        X = pila.pop()
        a = entrada[i]
        if X in nts:
            k = tabla.get((X, a))
            if k is None:
                return False
            pila += reversed(G[k][1])
        elif X == a:
            i += 1
        else:
            return False
    return i == len(entrada)


def prueba_parsers(n=300):
    rng, malos = random.Random(601), []
    for _ in range(n):
        tipos = generar(TU_GRAMATICA, "Programa", rng)
        texto = "\n".join(" ".join(LEXEMAS[t] for t in tipos[i:i + 1]) for i in range(len(tipos)))   # un token por línea
        r = analizar(texto)
        ok_rec = not r.errores
        ok_tab = parser_ll1(TU_GRAMATICA, tipos)
        if not (ok_rec and ok_tab):
            malos.append(("válido", tipos, ok_rec, ok_tab))
        if len(tipos) > 2:                          # mismo programa con un token cambiado: casi siempre inválido
            k = rng.randrange(len(tipos))
            mal = tipos[:k] + [rng.choice(["SINO", "PARDER", "ASIGNA", "NUM"])] + tipos[k + 1:]
            ok_tab = parser_ll1(TU_GRAMATICA, mal)
            texto = "\n".join(LEXEMAS[t] for t in mal)
            ok_rec = not analizar(texto).errores
            if ok_rec != ok_tab:
                malos.append(("alterado", mal, ok_rec, ok_tab))
    return n, malos


def prueba_esquema():
    from esquema_traduccion import EXPRESIONES
    return [e for e in EXPRESIONES if Traductor(e).traducir() != postfija_del_arbol(e)], len(EXPRESIONES)


def valor_de(x, mem):
    if x in mem:
        return mem[x]
    if x.startswith("$"):
        return float(x[1:])
    if x.endswith("%"):
        return float(x[:-1]) / 100
    return float(x)


def ejecutar_3d(codigo, mem):
    lineas = [l.strip() for l in codigo]
    etiquetas = {l[:-1]: i for i, l in enumerate(lineas) if l.endswith(":")}
    pc, pasos = 0, 0
    while pc < len(lineas) and pasos < 10000:
        l, pc, pasos = lineas[pc], pc + 1, pasos + 1
        p = l.split()
        if l.endswith(":") or p[0] == "escribir":
            continue
        if p[0] == "goto":
            pc = etiquetas[p[1]]
        elif p[0] == "ifFalse":
            a, op, b = p[1:4]
            ops = {">": COMPARACIONES["MAYOR"], "<": COMPARACIONES["MENOR"],
                   ">=": COMPARACIONES["MAYORIGUAL"], "<=": COMPARACIONES["MENORIGUAL"]}
            if not ops[op](valor_de(a, mem), valor_de(b, mem)):
                pc = etiquetas[p[5]]
        elif len(p) == 5:
            mem[p[0]] = OPERACIONES[p[3]](valor_de(p[2], mem), valor_de(p[4], mem))
        else:
            mem[p[0]] = valor_de(p[2], mem)
    return mem


def prueba_tres_direcciones(ruta="pruebas/promos_v2.txt"):
    r = analizar(leer_archivo(ruta))
    g = TresDirecciones()
    codigo = []
    for regla in r.arbol.hijos:
        codigo += g.regla(regla)
    resultados = []
    for nombre, venta in VENTAS.items():
        mem = ejecutar_3d(codigo, {k: float(v) for k, (v, _) in venta.items()})
        _, _, final = aplicar_promociones(r.arbol, {k: (float(v), t) for k, (v, t) in venta.items()}, salida=lambda *_: None)
        difs = [k for k, (v, _) in final.items() if abs(mem.get(k, float("nan")) - v) > 1e-9]
        resultados.append((nombre, difs, len(final)))
    return resultados


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    fallos = 0
    n, malos = prueba_parsers()
    print(f"1. Parser recursivo vs tabla LL(1): {n} programas al azar (+ {n} alterados) → {len(malos)} diferencias")
    fallos += len(malos)
    difs, total = prueba_esquema()
    print(f"2. Esquema de traducción vs postfija del árbol: {total - len(difs)}/{total} iguales")
    fallos += len(difs)
    for nombre, d, total in prueba_tres_direcciones():
        print(f"3. Tres direcciones ejecutado vs evaluador (venta {nombre}): {total - len(d)}/{total} variables iguales" + (f"  ¡difieren: {d}!" if d else ""))
        fallos += len(d)
    print("\nTodo coincide." if not fallos else f"\n¡Hay {fallos} diferencias!")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
