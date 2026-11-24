# -*- coding: utf-8 -*-
"""
parser_v3.py - Parser de la versión 3 del lenguaje de Haroldmart (con declaraciones)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL, día 1  (PASO 2 y AHORA TÚ 1 de declaraciones_base.py)

Hereda TODO de parser_v2.py (y por él, del Avance 2) y solo agrega la declaración:

     Regla → Decl | Si | Mientras | Asig | Escribir        (NUEVO: Decl)
     Decl  → TIPO ID                                         (TIPO = numero | dinero | porcentaje | texto)

TIPO no está en ningún otro FIRST, así que la gramática sigue siendo LL(1) (se comprueba con verificar_gramatica.py).
Alcance: una declaración vale en TODO el archivo (alcance global), pero hay que declarar antes de usar.
FOLLOW(Sino) ahora incluye TIPO: un SI sin SINO puede ir seguido de una declaración.

Uso:
    python src/parser_v3.py pruebas/promos_v3.txt            (árbol, o lista de errores)
    python src/parser_v3.py pruebas/promos_v3.txt --arbol
"""
import sys

import parser_v2
from parser_Haroldmart import Nodo, NOMBRES
from parser_con_recuperacion import numero_de_linea, lineas_de
from parser_v2 import ParserConExpresiones, imprimir_arbol, leer_archivo, nota_cascada, texto_expr
from escaner_v3 import escanear

NOMBRES["TIPO"] = "un tipo (numero, dinero, porcentaje o texto)"


def leer_tokens(texto):
    """Escáner v3 → [(tipo, lexema, línea), ..., ("$", "$", línea)] y errores léxicos [(línea, mensaje)]."""
    tokens, errores_lexicos = escanear(texto)
    lista = [(tipo, lexema, linea) for linea, tipo, lexema, _ in tokens]
    lista.append(("$", "$", texto.count("\n") + 1))
    return lista, errores_lexicos


class ParserConDeclaraciones(ParserConExpresiones):
    INICIO = ("TIPO", "SI", "MIENTRAS", "ID", "ESCRIBIR")               # FIRST(Regla) ahora incluye TIPO
    TEXTO_INICIO = "un tipo (numero, dinero, porcentaje o texto), SI, MIENTRAS, ESCRIBIR o una variable al inicio de la regla"

    def regla(self):
        # Regla → Decl | Si | Mientras | Asig | Escribir
        if self.tipo() == "TIPO":
            return Nodo("Regla", [self.decl()])
        return super().regla()

    def decl(self):
        # Decl → TIPO ID
        tipo = self.emparejar("TIPO")
        nombre = self.emparejar("ID")
        return Nodo("Decl", [tipo, nombre])


def analizar(texto):
    """parser_v2.analizar con el escáner v3 y el parser con declaraciones."""
    return parser_v2.analizar(texto, leer=leer_tokens, clase_parser=ParserConDeclaraciones)


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/parser_v3.py archivo_de_reglas.txt [--arbol]")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    r = analizar(leer_archivo(sys.argv[1]))
    if not r.errores or "--arbol" in sys.argv:
        imprimir_arbol(r.arbol)
        print()
    print(f"Reglas reconocidas: {r.reconocidas} · errores: {len(r.errores)}"
          + (f" ({r.n_lexicos} léxicos, {r.n_sintacticos} sintácticos)" if r.errores else ""))
    for e in r.errores:
        print("  " + e)
    if r.omitidos:
        print("  " + nota_cascada(r.omitidos))
    return 1 if r.errores else 0


if __name__ == "__main__":
    sys.exit(main())
