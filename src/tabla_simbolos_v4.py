# -*- coding: utf-8 -*-
"""
tabla_simbolos_v4.py - Tabla de símbolos FINAL de Haroldmart: variables con tipo declarado + tabla de FUNCIONES
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL  (PASO 3 y AHORA TÚ 2 de llamadas_base.py)

Hereda la tabla de declaraciones (tabla_simbolos_v3.py) y agrega las llamadas a las funciones predefinidas (funciones.py):
  * «no existe la función 'x'»                     (el nombre no está en FUNCIONES)
  * «'f' recibe N dato(s) y le diste M»            (número de datos equivocado)
  * lista de las funciones usadas y en qué línea.
Los TIPOS de los datos (¿es dinero lo que le pasas a redondear?) y de las asignaciones los revisa comprobar_tipos.py (fase 4).

Uso:
    python src/tabla_simbolos_v4.py pruebas/promos_v4.txt
    python src/tabla_simbolos_v4.py pruebas/promos_v4_errores.txt
"""
import sys

from parser_v4 import analizar, leer_archivo, nota_cascada
from tabla_simbolos_v3 import TablaDeclaraciones, armar_tabla, imprimir_tabla
from funciones import FUNCIONES, NOMBRES_DISPONIBLES


class TablaConFunciones(TablaDeclaraciones):
    def __init__(self, declaradas_con_error=()):
        super().__init__(declaradas_con_error)
        self.llamadas = {}                       # función → líneas donde se usa
        self.comprueba_asignacion = False        # el tipo de lo que se asigna lo revisa comprobar_tipos.py

    def llamar(self, nombre, n_args, linea):
        if nombre not in FUNCIONES:
            self.errores.append((linea, f"Línea {linea}: no existe la función '{nombre}' (hay: {NOMBRES_DISPONIBLES})"))
            return
        pedidos = len(FUNCIONES[nombre][0])
        if n_args != pedidos:
            self.errores.append((linea, f"Línea {linea}: '{nombre}' recibe {pedidos} dato(s) y le diste {n_args}"))
            return
        self.llamadas.setdefault(nombre, []).append(linea)


def construir(r):
    """Tabla (variables + funciones) de un resultado de analizar()."""
    return armar_tabla(r.arbol, {l for l, _ in r.errores_lexicos}, TablaConFunciones)


def imprimir_funciones(tabla):
    for f, lineas in tabla.llamadas.items():
        tipos = ", ".join(FUNCIONES[f][0])
        print(f"Función {f}({tipos}) → {FUNCIONES[f][1]}: usada en la(s) línea(s) {', '.join(str(n) for n in sorted(set(lineas)))}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/tabla_simbolos_v4.py archivo_de_reglas.txt")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    r = analizar(leer_archivo(sys.argv[1]))
    tabla = construir(r)
    if r.errores:
        print(f"Errores léxicos y sintácticos: {len(r.errores)} ({r.n_lexicos} léxicos, {r.n_sintacticos} sintácticos)")
        for e in r.errores:
            print("  " + e)
        if r.omitidos:
            print("  " + nota_cascada(r.omitidos))
        print()
    imprimir_tabla(tabla)
    imprimir_funciones(tabla)
    return 1 if (r.errores or tabla.errores) else 0


if __name__ == "__main__":
    sys.exit(main())
