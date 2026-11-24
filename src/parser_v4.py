# -*- coding: utf-8 -*-
"""
parser_v4.py - Parser FINAL del lenguaje de Haroldmart (versión 4)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL  (adaptación de llamadas_base.py del profesor)

Hereda TODO de parser_v3.py (declaraciones) → parser_v2.py (expresiones) → Avance 2 (recuperación de errores) y agrega:

     Factor  → NUM | PRECIO | PORC | CADENA | ID Llamada | ( Expr )        (antes: ... | ID | ...)
     Llamada → ( Args ) | ε                                            «ID» sola es una variable; «ID ( ... )» es una llamada
     Args    → Expr ArgsR | ε          ArgsR → , Expr ArgsR | ε
     Oprel   → MAYOR | MENOR | MAYORIGUAL | MENORIGUAL | IGUAL | DIFERENTE      (== y !=)

* FACTORIZAR: «variable» y «llamada» empiezan igual (ID). Con Factor → ID | ID ( Args ) la tabla LL(1) tendría DOS reglas en la
  celda [Factor, ID] (conflicto FIRST/FIRST; es la versión D de verificar_gramatica.py). Se saca lo común (ID) y se decide después con Llamada.
* En el parser esa decisión se toma MIRANDO UN TOKEN MÁS ADELANTE: si después del ID viene «(», es una llamada.
* En el árbol una llamada es un nodo «Llamada» con el nombre de la función en su token y un hijo por cada dato (argumento).
  Una llamada SIN datos, redondear(), no tiene hijos: por eso el código pregunta primero si el nodo es «Llamada» y no solo si tiene hijos.

Uso:
    python src/parser_v4.py pruebas/promos_v4.txt            (árbol, o lista de errores)
    python src/parser_v4.py pruebas/promos_v4.txt --arbol
"""
import sys

import parser_v2
from parser_Haroldmart import Nodo, NOMBRES
from parser_v2 import imprimir_arbol, leer_archivo, nota_cascada
from parser_v3 import ParserConDeclaraciones
from escaner_v4 import escanear

NOMBRES.update({"COMA": "«,»", "IGUAL": "«==»", "DIFERENTE": "«!=»"})


def leer_tokens(texto):
    """Escáner v4 → [(tipo, lexema, línea), ..., ("$", "$", línea)] y errores léxicos [(línea, mensaje)]."""
    tokens, errores_lexicos = escanear(texto)
    lista = [(tipo, lexema, linea) for linea, tipo, lexema, _ in tokens]
    lista.append(("$", "$", texto.count("\n") + 1))
    return lista, errores_lexicos


class ParserConLlamadas(ParserConDeclaraciones):
    OPERADORES = ("MAYOR", "MENOR", "MAYORIGUAL", "MENORIGUAL", "IGUAL", "DIFERENTE")

    def oprel(self):
        # Oprel → MAYOR | MENOR | MAYORIGUAL | MENORIGUAL | IGUAL | DIFERENTE
        if self.tipo() in self.OPERADORES:
            return Nodo("Oprel", [self.emparejar(self.tipo())])
        self.error("un operador de comparación (>, <, >=, <=, ==, !=)")

    def factor(self):
        # Factor → ID Llamada | ...   Si después del ID viene «(» es una llamada: se mira UN TOKEN MÁS ADELANTE.
        if self.tipo() == "ID" and self.tokens[self.pos + 1][0] == "PARIZQ":      # siempre hay un «$» al final
            nombre = self.emparejar("ID")
            self.emparejar("PARIZQ")
            args = self.args()
            self.emparejar("PARDER")
            return Nodo("Llamada", args, token=nombre.token)
        return super().factor()                                                  # variable, número, precio... o ( Expr )

    def args(self):
        # Args → Expr ArgsR | ε       ArgsR → , Expr ArgsR | ε      (ArgsR es el ciclo while)
        if self.tipo() == "PARDER":
            return []                                                            # ningún dato
        lista = [self.expr()]
        while self.tipo() == "COMA":
            self.emparejar("COMA")
            lista.append(self.expr())
        return lista


def analizar(texto):
    """parser_v2.analizar con el escáner v4 y el parser con llamadas."""
    return parser_v2.analizar(texto, leer=leer_tokens, clase_parser=ParserConLlamadas)


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/parser_v4.py archivo_de_reglas.txt [--arbol]")
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
