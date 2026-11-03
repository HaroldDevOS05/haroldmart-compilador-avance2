# -*- coding: utf-8 -*-
"""Tabla de símbolos de Haroldmart · Compiladores (IDS601) · UNEDL 2026B
(basado en tabla_simbolos_base.py del profesor; pieza que se entrega en el AVANCE 3)

Recorre el ÁRBOL que arma el parser y anota cada variable: nombre, tipo, si es resultado (se asigna)
o dato de la venta (solo se usa en condiciones) y las líneas donde aparece. Avisa si una variable
cambia de tipo (por ejemplo descuento = 5 y luego descuento = $100).

Cómo correrlo (desde la carpeta del proyecto):
    python src/tabla_simbolos.py pruebas/reglas_ok.txt
"""
import sys
from parser_Haroldmart import leer_tokens
from parser_con_recuperacion import ParserConRecuperacion

# Tipo de cada variable según la hoja del nodo Valor con la que se asigna o se compara
TIPOS = {"NUM": "num", "PRECIO": "dinero", "CADENA": "cadena"}


class TablaDeSimbolos:
    def __init__(self):
        self.simbolos = {}          # nombre → {"tipo": ..., "definida": [líneas], "usos": [líneas], "valores": [...]}
        self.avisos = []

    def entrada(self, nombre):
        return self.simbolos.setdefault(nombre, {"tipo": None, "definida": [], "usos": [], "valores": []})

    def definir(self, nombre, tipo, valor, linea):
        # TODO 1: guarda el tipo (si aún no tiene), la línea en "definida", y avisa si cambia de tipo
        s = self.entrada(nombre)
        if s["tipo"] and s["tipo"] != tipo:
            self.avisos.append(f"Línea {linea}: '{nombre}' era {s['tipo']} y ahora recibe {tipo} ({valor})")
        s["tipo"] = s["tipo"] or tipo
        s["definida"].append(linea)
        s["valores"].append(valor)

    def usar(self, nombre, tipo, linea):
        # TODO 2: agrega la línea a "usos"; si la variable no tiene tipo, toma el del valor con el que se compara
        s = self.entrada(nombre)
        s["tipo"] = s["tipo"] or tipo
        s["usos"].append(linea)


def recorrer(nodo, tabla):
    # TODO 3: Asig → ID ASIGNA Valor (definición) · Cond → ID Oprel Valor (uso); luego recorre los hijos.
    if nodo.nombre in ("Asig", "Cond"):
        ident, _, valor = nodo.hijos
        hoja = valor.hijos[0]                      # Valor → NUM | PRECIO | CADENA
        nombre, linea = ident.token[1], ident.token[2]
        tipo = TIPOS[hoja.nombre]
        if nodo.nombre == "Asig":
            tabla.definir(nombre, tipo, hoja.token[1], linea)
        else:
            tabla.usar(nombre, tipo, linea)
    for h in nodo.hijos:
        recorrer(h, tabla)


def lineas_sin_repetir(lista):
    return ", ".join(str(n) for n in sorted(set(lista))) or "—"


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/tabla_simbolos.py archivo_de_reglas.txt")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    with open(sys.argv[1], encoding="utf-8-sig") as f:
        texto = f.read()
    tokens, errores_lexicos = leer_tokens(texto)
    parser = ParserConRecuperacion(tokens)
    arbol = parser.programa()
    tabla = TablaDeSimbolos()
    recorrer(arbol, tabla)

    print(f"{'Nombre':<18} {'Tipo':<8} {'Clase':<17} {'Definida en':<12} Usada en")
    for nombre, s in tabla.simbolos.items():
        clase = "resultado" if s["definida"] else "dato de la venta"
        print(f"{nombre:<18} {str(s['tipo'] or '—'):<8} {clase:<17} {lineas_sin_repetir(s['definida']):<12} {lineas_sin_repetir(s['usos'])}")
    print(f"Total: {len(tabla.simbolos)} variables")
    for aviso in tabla.avisos:
        print("Aviso:", aviso)
    if errores_lexicos or parser.errores:
        print(f"Nota: el archivo tiene {len(errores_lexicos) + len(parser.errores)} errores; "
              f"la tabla solo incluye las reglas que sí se reconocieron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
