# -*- coding: utf-8 -*-
"""Verificador de la gramática de Haroldmart · AVANCES 2 y 3 · Compiladores (IDS601) · UNEDL 2026B
Basado en verificar_base.py del profesor (paso 6 del ejemplo de la papelería).

Verifica la gramática: ¿tiene recursión izquierda? ¿conflictos LL(1)? ¿conflictos SLR (LR)?

La gramática FINAL es la versión 2 (con operaciones + - * / y paréntesis, Avance 3). La versión 1
(Avance 2, sin operaciones) se conserva para comparar, y se agregan tres versiones «malas» a propósito
(A, B y C) para ver cuántos conflictos LL(1) y SLR tiene cada una.

Cómo correrlo (desde la carpeta del proyecto):
    python src/verificar_gramatica.py            # veredicto de cada versión de la gramática
    python src/verificar_gramatica.py --tabla    # además: reglas numeradas, FIRST, FOLLOW y tabla LL(1)
"""
import sys

EPS = "ε"

# ---------------- MI GRAMÁTICA v2 (versión final, LL(1)) ----------------
# Una regla por renglón: ("LadoIzquierdo", [símbolos del lado derecho]).  [] = ε (vacío).
# Los terminales se llaman igual que los tipos de token de mi escáner (SI, ID, NUM, PRECIO, PORC, MAS, ...).
TU_GRAMATICA = [
    ("Programa", ["Regla", "Programa"]), ("Programa", []),
    ("Regla", ["Si"]), ("Regla", ["Mientras"]), ("Regla", ["Asig"]), ("Regla", ["Escribir"]),
    ("Si", ["SI", "Cond", "ENTONCES", "Accion", "Sino"]),
    ("Sino", ["SINO", "Accion"]), ("Sino", []),
    ("Mientras", ["MIENTRAS", "Cond", "HACER", "Accion"]),
    ("Accion", ["Asig"]), ("Accion", ["Escribir"]),
    ("Asig", ["ID", "ASIGNA", "Valor"]),
    ("Escribir", ["ESCRIBIR", "Valor"]),
    ("Cond", ["ID", "Oprel", "Valor"]),
    ("Oprel", ["MAYOR"]), ("Oprel", ["MENOR"]), ("Oprel", ["MAYORIGUAL"]), ("Oprel", ["MENORIGUAL"]),
    # --- NUEVO en la versión 2: un valor ahora es una expresión (la precedencia está en la estructura) ---
    ("Valor", ["Expr"]),
    ("Expr", ["Term", "ExprR"]),
    ("ExprR", ["MAS", "Term", "ExprR"]), ("ExprR", ["MENOS", "Term", "ExprR"]), ("ExprR", []),
    ("Term", ["Factor", "TermR"]),
    ("TermR", ["POR", "Factor", "TermR"]), ("TermR", ["ENTRE", "Factor", "TermR"]), ("TermR", []),
    ("Factor", ["NUM"]), ("Factor", ["PRECIO"]), ("Factor", ["PORC"]), ("Factor", ["CADENA"]),
    ("Factor", ["ID"]), ("Factor", ["PARIZQ", "Expr", "PARDER"]),
]

# Versión 1 (Avance 2): un valor es solo NUM, PRECIO o CADENA (sin operaciones)
GRAMATICA_V1 = [r for r in TU_GRAMATICA if r[0] not in ("Valor", "Expr", "ExprR", "Term", "TermR", "Factor")] + [
    ("Valor", ["NUM"]), ("Valor", ["PRECIO"]), ("Valor", ["CADENA"]),
]

# AHORA TÚ 2 (Avance 2): versión A, con recursión izquierda en la lista de reglas (Programa → Programa Regla)
CON_RECURSION_IZQUIERDA = [("Programa", ["Programa", "Regla"]), ("Programa", [])] + TU_GRAMATICA[2:]

# versión B, sin factorizar: las dos formas de SI empiezan igual (SI Cond ENTONCES Accion ...)
SIN_FACTORIZAR = [r for r in TU_GRAMATICA if r[0] not in ("Si", "Sino")] + [
    ("Si", ["SI", "Cond", "ENTONCES", "Accion"]),
    ("Si", ["SI", "Cond", "ENTONCES", "Accion", "SINO", "Accion"]),
]
SIN_FACTORIZAR = [r for r in SIN_FACTORIZAR if r[0] == "Programa"] + [r for r in SIN_FACTORIZAR if r[0] != "Programa"]

# AVANCE 3, versión C: la expresión «de libro de texto» con recursión izquierda (Expr → Expr + Term)
EXPR_RECURSIVA = [r for r in TU_GRAMATICA if r[0] not in ("Expr", "ExprR", "Term", "TermR")]
EXPR_RECURSIVA = EXPR_RECURSIVA[:EXPR_RECURSIVA.index(("Factor", ["NUM"]))] + [
    ("Expr", ["Expr", "MAS", "Term"]), ("Expr", ["Expr", "MENOS", "Term"]), ("Expr", ["Term"]),
    ("Term", ["Term", "POR", "Factor"]), ("Term", ["Term", "ENTRE", "Factor"]), ("Term", ["Factor"]),
] + EXPR_RECURSIVA[EXPR_RECURSIVA.index(("Factor", ["NUM"])):]

GRAMATICAS = [
    ("MI GRAMÁTICA v2 (final, con operaciones)", TU_GRAMATICA),
    ("Versión 1 (Avance 2, sin operaciones)", GRAMATICA_V1),
    ("VERSIÓN A: con recursión izquierda en la lista de reglas (Programa → Programa Regla)", CON_RECURSION_IZQUIERDA),
    ("VERSIÓN B: sin factorizar el SINO (dos reglas Si que empiezan igual)", SIN_FACTORIZAR),
    ("VERSIÓN C: Expr con recursión izquierda (Expr → Expr + Term, Term → Term * Factor)", EXPR_RECURSIVA),
]


# ---------------- FIRST y FOLLOW ----------------
def first_follow(G):
    nts = list(dict.fromkeys(A for A, _ in G))
    FI = {A: set() for A in nts}

    def first_de(seq):
        out = set()
        for X in seq:
            f = FI[X] if X in FI else {X}
            out |= f - {EPS}
            if EPS not in f:
                return out
        return out | {EPS}

    cambio = True
    while cambio:
        cambio = False
        for A, der in G:
            n = first_de(der)
            if not n <= FI[A]:
                FI[A] |= n; cambio = True
    FO = {A: set() for A in nts}; FO[nts[0]].add("$")
    cambio = True
    while cambio:
        cambio = False
        for B, der in G:
            for i, A in enumerate(der):
                if A in FO:
                    r = first_de(der[i + 1:])
                    n = (r - {EPS}) | (FO[B] if EPS in r else set())
                    if not n <= FO[A]:
                        FO[A] |= n; cambio = True
    return nts, FI, FO, first_de


# ---------------- Prueba 1: recursión izquierda ----------------
def recursion_izquierda(G):
    """A es recursiva por la izquierda si A ⇒+ A … (directa o pasando por otros no terminales que pueden ser ε)."""
    nts, FI, FO, first_de = first_follow(G)
    empieza = {A: set() for A in nts}          # A → B …  (B puede ir al inicio)
    for A, der in G:
        for X in der:
            if X in empieza:
                empieza[A].add(X)
            if X not in FI or EPS not in FI[X]:
                break
    malos = []
    for A in nts:
        visto, pila = set(), list(empieza[A])
        while pila:
            B = pila.pop()
            if B == A:
                malos.append(A); break
            if B not in visto:
                visto.add(B); pila.extend(empieza[B])
    return malos


# ---------------- Prueba 2: conflictos LL(1) ----------------
def conflictos_ll1(G):
    nts, FI, FO, first_de = first_follow(G)
    tabla = {}
    for k, (A, der) in enumerate(G):
        f = first_de(der)
        columnas = (f - {EPS}) | (FO[A] if EPS in f else set())
        for a in columnas:
            tabla.setdefault((A, a), []).append(k)
    return {celda: ks for celda, ks in tabla.items() if len(ks) > 1}


# ---------------- Prueba 3: conflictos SLR (análisis ascendente) ----------------
def conflictos_slr(G):
    P = [("Inicio'", [G[0][0]])] + G
    nts = {A for A, _ in P}
    _, _, FO, _ = first_follow(P)

    def cerradura(I):
        I = list(I)
        for k, p in I:
            der = P[k][1]
            if p < len(der) and der[p] in nts:
                for j, (A, _) in enumerate(P):
                    if A == der[p] and (j, 0) not in I:
                        I.append((j, 0))
        return tuple(sorted(I))

    simbolos = list(dict.fromkeys(X for _, der in P for X in der))
    estados, flechas, i = [cerradura([(0, 0)])], {}, 0
    while i < len(estados):
        for X in simbolos:
            mov = [(k, p + 1) for k, p in estados[i] if p < len(P[k][1]) and P[k][1][p] == X]
            if mov:
                J = cerradura(mov)
                if J not in estados:
                    estados.append(J)
                flechas[(i, X)] = estados.index(J)
        i += 1
    accion = {}
    for i, I in enumerate(estados):
        for k, p in I:
            A, der = P[k]
            if p < len(der) and der[p] not in nts:
                accion.setdefault((i, der[p]), set()).add(f"s{flechas[(i, der[p])]}")
            elif p == len(der):
                for b in (["$"] if k == 0 else FO[A]):
                    accion.setdefault((i, b), set()).add("acc" if k == 0 else f"r{k}")
    return len(estados), {c: sorted(v) for c, v in accion.items() if len(v) > 1}


# ---------------- Documentación: reglas numeradas, FIRST, FOLLOW y tabla LL(1) ----------------
def mostrar_tabla(G):
    nts, FI, FO, first_de = first_follow(G)
    terminales = list(dict.fromkeys(X for _, der in G for X in der if X not in nts)) + ["$"]
    orden = {t: i for i, t in enumerate(terminales)}
    ordenar = lambda conjunto: sorted(conjunto, key=lambda s: (s == EPS, orden.get(s, 0)))

    print("Reglas numeradas:")
    for k, (A, der) in enumerate(G, 1):
        print(f"  {k:>2}. {A} → {' '.join(der) if der else EPS}")
    print("\nFIRST:")
    for A in nts:
        print(f"  FIRST({A}) = {{ {', '.join(ordenar(FI[A]))} }}")
    print("\nFOLLOW:")
    for A in nts:
        print(f"  FOLLOW({A}) = {{ {', '.join(ordenar(FO[A]))} }}")

    celdas = {}
    for k, (A, der) in enumerate(G, 1):
        f = first_de(der)
        for a in (f - {EPS}) | (FO[A] if EPS in f else set()):
            celdas.setdefault((A, a), []).append(k)
    print("\nTabla LL(1) (cada celda es el número de la regla a usar; vacío = error):\n")
    print("| |" + "|".join(f" {t} " for t in terminales) + "|")
    print("|---|" + "|".join(":-:" for _ in terminales) + "|")
    for A in nts:
        fila = "|".join(f" {','.join(map(str, celdas.get((A, t), []))) or ' '} " for t in terminales)
        print(f"| **{A}** |{fila}|")


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    for nombre, G in GRAMATICAS:
        rec = recursion_izquierda(G)
        ll = conflictos_ll1(G)
        n, slr = conflictos_slr(G)
        print(f"== {nombre} ({len(G)} reglas)")
        print(f"   Recursión izquierda: {', '.join(rec) if rec else 'no'}")
        print(f"   Conflictos LL(1):    {len(ll)}" + ("".join(f"\n      celda [{A}, {a}]: reglas {', '.join(str(k + 1) for k in ks)}" for (A, a), ks in sorted(ll.items())[:3])))
        print(f"   Conflictos SLR:      {len(slr)} (en {n} estados)" + ("".join(f"\n      estado {i}, token {a}: {' / '.join(v)}" for (i, a), v in sorted(slr.items())[:2])))
        ok_ll = not rec and not ll
        print(f"   → {'SIRVE para nuestro parser LL(1)' if ok_ll else 'NO sirve para LL(1)'} · {'SIRVE para SLR' if not slr else 'NO es SLR'}")
    if "--tabla" in sys.argv:
        print("\n" + "=" * 70 + "\nDOCUMENTACIÓN DE MI GRAMÁTICA FINAL\n" + "=" * 70)
        mostrar_tabla(TU_GRAMATICA)
