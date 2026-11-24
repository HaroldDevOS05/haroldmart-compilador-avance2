# -*- coding: utf-8 -*-
"""
analizar_todo.py - El ANALIZADOR COMPLETO de Haroldmart (frente del compilador: léxico → sintaxis → declaraciones → tipos)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL

Corre las cuatro fases sobre un archivo de promociones y resume cada una. Revisa, no ejecuta (ejecutar es evaluar_atributos.py).

    Fase 1 · Léxico:        el escáner (un AFD por token) lista los tokens con su línea; no se detiene en un error.
    Fase 2 · Sintaxis:      parser LL(1) descendente recursivo con recuperación de errores (modo pánico y nivel de frase).
    Fase 3 · Declaraciones: tabla de símbolos: ¿está declarada cada variable? ¿repetida? ¿la función existe y recibe sus datos?
    Fase 4 · Tipos:         comprobación de tipos: ¿tiene sentido cada operación, asignación y comparación?

Uso:
    python src/analizar_todo.py pruebas/promos_v4.txt             (programa correcto)
    python src/analizar_todo.py pruebas/promos_v4_tipos.txt       (con errores: cada uno con su línea)
    python src/analizar_todo.py pruebas/promos_v4.txt --tabla     (además imprime la tabla de símbolos y de funciones)
"""
import sys

from escaner_v4 import escanear
from parser_v4 import analizar, leer_archivo, nota_cascada
from tabla_simbolos_v4 import construir, imprimir_funciones
from tabla_simbolos_v3 import imprimir_tabla
from comprobar_tipos import comprobar


def analizar_archivo(texto):
    """Corre las cuatro fases. Regresa un diccionario con los números y los mensajes de cada una."""
    tokens, _ = escanear(texto)
    r = analizar(texto)
    tabla = construir(r)
    tipos = comprobar(r, tabla)
    lexicos = [e for e in r.errores if "error léxico" in e]
    sintacticos = [e for e in r.errores if "error léxico" not in e]
    declaraciones = [m for _, m in tabla.errores]
    return {"tokens": len(tokens), "r": r, "tabla": tabla, "lexicos": lexicos, "sintacticos": sintacticos,
            "declaraciones": declaraciones, "tipos": tipos,
            "total": len(r.errores) + len(declaraciones) + len(tipos)}


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/analizar_todo.py archivo_de_reglas.txt [--tabla]")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    a = analizar_archivo(leer_archivo(sys.argv[1]))
    r, t = a["r"], a["tabla"]
    print(f"Fase 1 · Léxico:        {a['tokens']} tokens, {len(a['lexicos'])} error(es)")
    print(f"Fase 2 · Sintaxis:      {len(r.arbol.hijos)} reglas, {len(a['sintacticos'])} error(es)")
    print(f"Fase 3 · Declaraciones: {len(t.simbolos)} variables, {len(t.llamadas)} funciones, {len(a['declaraciones'])} error(es)")
    print(f"Fase 4 · Tipos:         {len(a['tipos'])} error(es)")
    detalle = [("léxico", a["lexicos"]), ("sintaxis", a["sintacticos"]), ("declaración", a["declaraciones"]), ("tipos", a["tipos"])]
    for fase, mensajes in detalle:
        for m in mensajes:
            print(f"  [{fase}] {m}")
    if r.omitidos:
        print("  " + nota_cascada(r.omitidos))
    print("RESULTADO: " + ("programa correcto ✓" if not a["total"] else f"{a['total']} error(es) en total"))
    if "--tabla" in sys.argv:
        print()
        imprimir_tabla(t)
        imprimir_funciones(t)
    return 1 if a["total"] else 0


if __name__ == "__main__":
    sys.exit(main())
