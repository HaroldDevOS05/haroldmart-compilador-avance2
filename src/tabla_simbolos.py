# -*- coding: utf-8 -*-
"""
tabla_simbolos.py - Tabla de símbolos de Haroldmart (versión 2, con expresiones)
Compiladores (IDS601) - UNEDL 2026B - AVANCE 3  (adaptación de tabla_simbolos_base.py del profesor)

Recorre el ÁRBOL y anota cada variable: nombre, tipo, clase y las líneas donde se DEFINE y donde se USA.

  * DEFINIR = que reciba un valor:  descuento = ...     (Asig → ID = Valor)
  * USAR    = que se lea su valor:  en una condición (SI total_compra > $1000) o dentro de una expresión
              (pago = (total_compra - descuento) + envio  usa total_compra, descuento y envio).
  * TIPO    = num | dinero | porc | cadena. Ahora un valor puede ser una expresión, así que el tipo se INFIERE
              con las mismas reglas de combinar() de evaluar_atributos.py (dinero × porc → dinero, etc.).
              Una variable que no se define en el archivo es un dato de la venta: su tipo sale de la venta
              de prueba o, si no está ahí, de lo que se compara con ella.
  * CLASE   = resultado (la calcula una regla) | dato de la venta (la manda la caja) | dato y resultado.

El análisis léxico y sintáctico NO se detiene en el primer error: se listan todos (con su línea) y la tabla
se arma con las reglas que sí se reconocieron.

Uso:
    python src/tabla_simbolos.py pruebas/promos_v2.txt
"""
import sys

from parser_v2 import analizar, leer_archivo, nota_cascada, texto_expr
from parser_con_recuperacion import lineas_de
from evaluar_atributos import combinar, ErrorDeTipo, TIPOS_DE_LA_VENTA, primera_linea

TIPO_DE_HOJA = {"NUM": "num", "PRECIO": "dinero", "PORC": "porc", "CADENA": "cadena"}


class TablaDeSimbolos:
    def __init__(self):
        self.simbolos = {}          # nombre → {"tipo", "definida": [líneas], "usos": [líneas], "valores": [textos]}
        self.avisos = []

    def entrada(self, nombre):
        return self.simbolos.setdefault(nombre, {"tipo": None, "definida": [], "usos": [], "valores": []})

    def definir(self, nombre, tipo, valor, linea):
        # guarda el tipo (si aún no tiene), la línea en "definida", y avisa si cambia de tipo
        s = self.entrada(nombre)
        if tipo is None:
            self.avisos.append(f"Línea {linea}: no se pudo determinar el tipo de '{nombre}' ({valor}): su expresión tiene un error de tipo o usa una variable sin tipo")
        elif s["tipo"] and s["tipo"] != tipo:
            self.avisos.append(f"Línea {linea}: '{nombre}' era {s['tipo']} y ahora recibe {tipo} ({valor})")
        s["tipo"] = s["tipo"] or tipo
        s["definida"].append(linea)
        s["valores"].append(valor)

    def usar(self, nombre, linea):
        # agrega la línea a "usos" (el tipo se resuelve después, con inferir_tipos)
        self.entrada(nombre)["usos"].append(linea)


# ---------------- Paso 1: recorrer el árbol y juntar los hechos ----------------
def es_id(n):
    return not n.hijos and n.token and n.token[0] == "ID"


def usos_en(n, hechos):
    """Cada ID que aparece dentro de una expresión es un USO."""
    if es_id(n):
        hechos["usos"].append((n.token[1], n.token[2]))
    for h in n.hijos:
        usos_en(h, hechos)


def recorrer(nodo, hechos):
    """Asig → ID = Valor (definición) · Cond → ID Oprel Valor (uso) · ESCRIBIR Valor · ids dentro de expresiones (usos)."""
    if nodo.nombre == "Asig":
        ident, _, valor = nodo.hijos
        hechos["defs"].append((ident.token[1], valor.hijos[0], ident.token[2]))
        usos_en(valor, hechos)
        return
    if nodo.nombre == "Cond":
        ident, _, valor = nodo.hijos
        hechos["usos"].append((ident.token[1], ident.token[2]))
        hechos["conds"].append((ident.token[1], valor.hijos[0]))
        usos_en(valor, hechos)
        return
    for h in nodo.hijos:
        recorrer(h, hechos)


# ---------------- Paso 2: inferir el tipo de cada variable ----------------
def tipo_de(n, tipos):
    """Tipo de una expresión con lo que se sabe hasta ahora. None = todavía no se sabe (o es un error de tipo)."""
    if not n.hijos:
        if n.token[0] == "ID":
            return tipos.get(n.token[1])
        return TIPO_DE_HOJA[n.token[0]]
    a, b = tipo_de(n.hijos[0], tipos), tipo_de(n.hijos[1], tipos)
    if a is None or b is None:
        return None
    try:
        return combinar(a, n.nombre, b, primera_linea(n))
    except ErrorDeTipo:
        return None


def inferir_tipos(hechos):
    """Punto fijo: se repite hasta que ya no se aprende nada nuevo.
    1) lo que la caja manda (la venta de prueba)  2) el primer valor que se asigna  3) con qué se compara."""
    definidas = {nombre for nombre, _, _ in hechos["defs"]}
    tipos = {n: t for n, t in TIPOS_DE_LA_VENTA.items() if n in {u for u, _ in hechos["usos"]} | definidas}
    cambio = True
    while cambio:
        cambio = False
        for nombre, expr, _ in hechos["defs"]:
            if nombre not in tipos and (t := tipo_de(expr, tipos)):
                tipos[nombre], cambio = t, True
        for nombre, expr in hechos["conds"]:
            if nombre not in tipos and (t := tipo_de(expr, tipos)):
                tipos[nombre], cambio = t, True
    return tipos


def armar_tabla(arbol, lineas_con_error=()):
    """Arma la tabla con las reglas que no tocan una línea con error léxico (esas reglas no son confiables)."""
    hechos = {"defs": [], "conds": [], "usos": []}
    for regla in arbol.hijos:
        if not (lineas_de(regla) & set(lineas_con_error)):
            recorrer(regla, hechos)
    tipos = inferir_tipos(hechos)
    tabla = TablaDeSimbolos()
    for nombre, expr, linea in sorted(hechos["defs"], key=lambda d: d[2]):
        s = tabla.entrada(nombre)
        if s["tipo"] is None and nombre in tipos:
            s["tipo"] = tipos[nombre]                          # tipo inicial: el de la venta o el del primer valor
        tabla.definir(nombre, tipo_de(expr, {**tipos, **{k: v["tipo"] for k, v in tabla.simbolos.items() if v["tipo"]}}),
                      texto_expr(expr), linea)
    for nombre, linea in hechos["usos"]:
        tabla.usar(nombre, linea)
    for nombre, s in tabla.simbolos.items():
        s["tipo"] = s["tipo"] or tipos.get(nombre)
    return tabla


def lineas_sin_repetir(lista):
    return ", ".join(str(n) for n in sorted(set(lista))) or "—"


def clase_de(nombre, s):
    if not s["definida"]:
        return "dato de la venta"
    return "dato y resultado" if nombre in TIPOS_DE_LA_VENTA else "resultado"


def imprimir_tabla(tabla):
    print(f"{'Nombre':<18} {'Tipo':<8} {'Clase':<17} {'Definida en':<12} Usada en")
    for nombre, s in sorted(tabla.simbolos.items(), key=lambda kv: min(kv[1]["definida"] + kv[1]["usos"] or [0])):
        print(f"{nombre:<18} {str(s['tipo'] or '—'):<8} {clase_de(nombre, s):<17} "
              f"{lineas_sin_repetir(s['definida']):<12} {lineas_sin_repetir(s['usos'])}")
    print(f"Total: {len(tabla.simbolos)} variables")
    for aviso in tabla.avisos:
        print("Aviso:", aviso)


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/tabla_simbolos.py archivo_de_reglas.txt")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    r = analizar(leer_archivo(sys.argv[1]))
    imprimir_tabla(armar_tabla(r.arbol, {l for l, _ in r.errores_lexicos}))
    if r.errores:
        print(f"\nErrores del archivo: {len(r.errores)} ({r.n_lexicos} léxicos, {r.n_sintacticos} sintácticos)")
        for e in r.errores:
            print("  " + e)
        if r.omitidos:
            print("  " + nota_cascada(r.omitidos))
        print(f"La tabla solo incluye las reglas sin errores léxicos (reglas reconocidas: {r.reconocidas}).")
    return 1 if r.errores else 0


if __name__ == "__main__":
    sys.exit(main())
