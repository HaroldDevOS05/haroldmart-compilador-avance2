# -*- coding: utf-8 -*-
"""
consultar_tabla.py - ¿Qué regla elige mi parser con un token y por qué?  (para explicarlo en la defensa)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL

Mira la celda [No terminal, token] de la tabla LL(1) de MI gramática y dice qué regla se usa y la razón (FIRST o FOLLOW):
  * si el token está en FIRST del lado derecho de una regla → se elige esa regla;
  * si el lado derecho puede ser vacío (ε) y el token está en FOLLOW del no terminal → se elige la regla de ε;
  * si ninguna → celda vacía = error de sintaxis (y qué tokens se esperaban).

Uso:
    python src/consultar_tabla.py Sino SINO        (celda [Sino, SINO])
    python src/consultar_tabla.py Sino '$'         (celda [Sino, $]: regla de ε porque $ está en FOLLOW(Sino))
    python src/consultar_tabla.py Factor ID        (variable o llamada: se decide con Llamada, mirando un token más)
    python src/consultar_tabla.py Si ENTONCES      (celda vacía: error)
"""
import sys

from verificar_gramatica import TU_GRAMATICA, first_follow, EPS


def lado(der):
    return " ".join(der) if der else EPS


def consultar(no_terminal, token, G=TU_GRAMATICA):
    nts, FI, FO, first_de = first_follow(G)
    if no_terminal not in nts:
        return f"'{no_terminal}' no es un no terminal. Los hay: {', '.join(nts)}"
    lineas = []
    elegidas = []
    for k, (A, der) in enumerate(G, 1):
        if A != no_terminal:
            continue
        f = first_de(der)
        if token in f:
            elegidas.append(k)
            lineas.append(f"Regla {k}: {A} → {lado(der)}  porque «{token}» está en FIRST({lado(der)}) = {{ {', '.join(sorted(f - {EPS}))} }}")
        elif EPS in f and token in FO[A]:
            elegidas.append(k)
            lineas.append(f"Regla {k}: {A} → ε  porque el lado derecho puede ser vacío y «{token}» está en FOLLOW({A}) = {{ {', '.join(sorted(FO[A]))} }}")
    if not elegidas:
        esperados = sorted(set().union(*[(first_de(d) - {EPS}) | (FO[A] if EPS in first_de(d) else set()) for A, d in G if A == no_terminal]))
        return f"Celda [{no_terminal}, {token}] VACÍA → error de sintaxis. Con {no_terminal} se esperaba: {', '.join(esperados)}"
    return f"Celda [{no_terminal}, {token}] = " + ("regla " + str(elegidas[0]) if len(elegidas) == 1 else f"CONFLICTO (reglas {elegidas})") + "\n  " + "\n  ".join(lineas)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    print(consultar(sys.argv[1], sys.argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
