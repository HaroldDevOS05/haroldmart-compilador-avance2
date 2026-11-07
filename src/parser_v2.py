# -*- coding: utf-8 -*-
"""
parser_v2.py - Parser de la versión 2 del lenguaje de Haroldmart (con operaciones)
Compiladores (IDS601) - UNEDL 2026B - AVANCE 3  (adaptación de expresiones_base.py del profesor)

Hereda TODO del parser con recuperación del Avance 2 (parser_con_recuperacion.py, que a su vez hereda de
parser_Haroldmart.py) y solo cambia lo nuevo: un VALOR ahora es una EXPRESIÓN.

     Valor   → Expr
     Expr    → Term ExprR          ExprR → + Term ExprR | - Term ExprR | ε      (suma y resta)
     Term    → Factor TermR        TermR → * Factor TermR | / Factor TermR | ε   (multiplicación y división)
     Factor  → NUM | PRECIO | PORC | CADENA | ID | ( Expr )

* PRECEDENCIA: * y / están en Term (más abajo en la gramática), así que se agrupan antes que + y -.
* ASOCIATIVIDAD IZQUIERDA: ExprR y TermR se escriben como un ciclo while; a - b - c se agrupa (a - b) - c.
* El árbol es de SINTAXIS ABSTRACTA: cada operación es un nodo con sus dos operandos; los paréntesis y
  los no terminales Expr/Term/ExprR/TermR no aparecen.  Las hojas son tokens (NUM, PRECIO, PORC, CADENA, ID).

Uso:
    python src/parser_v2.py pruebas/promos_v2.txt              (árbol de cada regla, o la lista de errores)
    python src/parser_v2.py pruebas/promos_v2.txt --arbol      (fuerza imprimir el árbol aunque haya errores)
"""
import sys
from types import SimpleNamespace

from escaner_v2 import escanear
from parser_Haroldmart import Nodo, ErrorSintactico, NOMBRES
from parser_con_recuperacion import ParserConRecuperacion, lineas_de, numero_de_linea

# Nombres de los terminales nuevos para los mensajes de error (se suman a los del Avance 2)
NOMBRES.update({
    "PORC": "un porcentaje (15%)",
    "MAS": "«+»", "MENOS": "«-»", "POR": "«*»", "ENTRE": "«/»", "PARIZQ": "«(»", "PARDER": "«)»",
})

PRECEDENCIA = {"+": 1, "-": 1, "*": 2, "/": 2}


def leer_tokens(texto):
    """Escáner v2 → tokens como los usa el parser: [(tipo, lexema, línea), ..., ("$", "$", línea)]
    más la lista de errores léxicos [(línea, mensaje)]."""
    tokens, errores_lexicos = escanear(texto)
    lista = [(tipo, lexema, linea) for linea, tipo, lexema, _camino in tokens]
    lista.append(("$", "$", texto.count("\n") + 1))          # marca de fin de entrada
    return lista, errores_lexicos


class ParserConExpresiones(ParserConRecuperacion):
    """Parser de la versión 2: operaciones + - * / y paréntesis, con recuperación de errores."""

    def valor(self):
        # Valor → Expr
        return Nodo("Valor", [self.expr()])

    def expr(self):
        # Expr → Term ExprR      (ExprR es el ciclo)
        izq = self.term()
        while self.tipo() in ("MAS", "MENOS"):
            op = self.emparejar(self.tipo())                  # hoja del operador: su lexema es + o -
            izq = Nodo(op.token[1], [izq, self.term()])       # el operador es el nodo; los operandos, sus hijos
        return izq

    def term(self):
        # Term → Factor TermR    (TermR es el ciclo)
        izq = self.factor()
        while self.tipo() in ("POR", "ENTRE"):
            op = self.emparejar(self.tipo())
            izq = Nodo(op.token[1], [izq, self.factor()])
        return izq

    def factor(self):
        # Factor → NUM | PRECIO | PORC | CADENA | ID | ( Expr )
        t = self.tipo()
        if t in ("NUM", "PRECIO", "PORC", "CADENA", "ID"):
            return self.emparejar(t)
        if t == "PARIZQ":
            self.emparejar("PARIZQ")
            dentro = self.expr()
            self.emparejar("PARDER")
            return dentro                                     # los paréntesis solo agrupan: no son nodo
        self.error("un valor (número, precio como $300, porcentaje como 15%, variable o «(»)")


def imprimir_arbol(nodo):
    print("\n".join(nodo.lineas()))


def texto_expr(n, padre=0, es_derecho=False):
    """Escribe una expresión del árbol otra vez en forma normal (infija), con los paréntesis mínimos."""
    if not n.hijos:
        return n.token[1]
    p = PRECEDENCIA[n.nombre]
    s = f"{texto_expr(n.hijos[0], p, False)} {n.nombre} {texto_expr(n.hijos[1], p, True)}"
    return f"({s})" if (p < padre or (p == padre and es_derecho)) else s


def analizar(texto):
    """Escáner v2 + parser con recuperación. Junta los errores léxicos y sintácticos (ordenados por línea).
    Regresa un objeto con: arbol, errores, n_lexicos, n_sintacticos, omitidos, reconocidas, errores_lexicos."""
    tokens, errores_lexicos = leer_tokens(texto)
    parser = ParserConExpresiones(tokens)
    arbol = parser.programa()
    lineas_lexicas = {linea for linea, _ in errores_lexicos}
    # una regla cuenta como reconocida si no tiene ningún símbolo con error léxico en sus renglones
    reconocidas = sum(1 for regla in arbol.hijos if not (lineas_de(regla) & lineas_lexicas))
    lexicos = [(linea, f"Línea {linea}: error léxico, {m}") for linea, m in errores_lexicos]
    sintacticos, omitidos = [], 0
    for e in parser.errores:
        linea = numero_de_linea(e)
        if linea in lineas_lexicas:          # ERROR EN CASCADA: consecuencia de un símbolo ya reportado por el escáner
            omitidos += 1
        else:
            sintacticos.append((linea, e))
    todos = sorted(lexicos + sintacticos, key=lambda par: par[0])
    return SimpleNamespace(arbol=arbol, errores=[m for _, m in todos], n_lexicos=len(lexicos),
                           n_sintacticos=len(sintacticos), omitidos=omitidos, reconocidas=reconocidas,
                           errores_lexicos=errores_lexicos)


def leer_archivo(ruta):
    with open(ruta, encoding="utf-8-sig") as f:
        return f.read()


def nota_cascada(omitidos):
    """Texto que avisa cuántos errores de sintaxis se omitieron por ser errores en cascada (o vacío)."""
    if not omitidos:
        return ""
    if omitidos == 1:
        return "(se omitió 1 error de sintaxis en un renglón que ya tiene un error léxico: es consecuencia, un error en cascada)"
    return (f"(se omitieron {omitidos} errores de sintaxis en renglones que ya tienen un error léxico: "
            "son consecuencia, errores en cascada)")


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/parser_v2.py archivo_de_reglas.txt [--arbol]")
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
