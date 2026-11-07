# -*- coding: utf-8 -*-
"""
codigo_intermedio.py - Código intermedio de las reglas de Haroldmart: postfija y tres direcciones
Compiladores (IDS601) - UNEDL 2026B - AVANCE 3  (adaptación de expresiones_base.py del profesor, TODO 4 y 5)

Parte del ÁRBOL que arma parser_v2.py y lo traduce a dos formas de código intermedio:

  * NOTACIÓN POSTFIJA: primero los dos operandos y al final el operador (recorrido en postorden). No usa paréntesis.
        precio * 2 + 10      →   precio 2 * 10 +
  * CÓDIGO DE TRES DIRECCIONES: instrucciones «x = y op z» (un operador y tres nombres por renglón), con
    temporales t1, t2, ... y, para SI y MIENTRAS, saltos (ifFalse ... goto) y etiquetas (L1, L2, ...).
    UN SOLO generador para todo el programa: los temporales y las etiquetas no se repiten entre reglas.

Uso:
    python src/codigo_intermedio.py pruebas/promos_v2.txt
"""
import sys

from parser_v2 import analizar, leer_archivo, texto_expr
from parser_con_recuperacion import lineas_de


def postfija(n):
    """Notación postfija de una expresión del árbol (postorden: hijo izquierdo, hijo derecho, nodo)."""
    if not n.hijos:                       # hoja: el lexema del token
        return n.token[1]
    izq, der = n.hijos
    return f"{postfija(izq)} {postfija(der)} {n.nombre}"


class TresDirecciones:
    def __init__(self):
        self.codigo = []                  # renglones de la regla que se está traduciendo
        self.t = 0                        # contador de temporales (t1, t2, ...) de TODO el programa
        self.l = 0                        # contador de etiquetas (L1, L2, ...) de TODO el programa

    # ---------- utilidades ----------
    def temporal(self):
        self.t += 1
        return f"t{self.t}"

    def etiqueta(self):
        self.l += 1
        return f"L{self.l}"

    def emitir(self, instruccion):
        self.codigo.append("    " + instruccion)

    def poner(self, etiqueta):
        self.codigo.append(f"{etiqueta}:")

    # ---------- expresiones ----------
    def expr(self, n):
        # TODO 5: hoja → su lexema; operación → a = expr(izq), b = expr(der), t = temporal, «t = a op b».
        if not n.hijos:
            return n.token[1]
        a = self.expr(n.hijos[0])
        b = self.expr(n.hijos[1])
        t = self.temporal()
        self.emitir(f"{t} = {a} {n.nombre} {b}")
        return t

    def valor(self, n):
        # Valor → Expr   (n es el nodo Valor; su único hijo es la expresión)
        return self.expr(n.hijos[0])

    def cond(self, n):
        # Cond → ID Oprel Valor: genera el código de la derecha (si es operación) y regresa «a op b»
        ident, oprel, valor = n.hijos
        derecha = self.valor(valor)
        return f"{ident.token[1]} {oprel.hijos[0].token[1]} {derecha}"

    # ---------- sentencias ----------
    def asig(self, n):
        ident, _, valor = n.hijos
        lugar = self.valor(valor)
        self.emitir(f"{ident.token[1]} = {lugar}")

    def escribir(self, n):
        lugar = self.valor(n.hijos[1])
        self.emitir(f"escribir {lugar}")

    def accion(self, n):
        # Accion → Asig | Escribir
        hijo = n.hijos[0]
        self.asig(hijo) if hijo.nombre == "Asig" else self.escribir(hijo)

    def si(self, n):
        # Si → SI Cond ENTONCES Accion Sino
        cond = self.cond(n.hijos[1])
        sino = n.hijos[4] if len(n.hijos) > 4 else None
        if sino is None:
            fin = self.etiqueta()
            self.emitir(f"ifFalse {cond} goto {fin}")
            self.accion(n.hijos[3])
            self.poner(fin)
        else:
            l_sino, l_fin = self.etiqueta(), self.etiqueta()
            self.emitir(f"ifFalse {cond} goto {l_sino}")
            self.accion(n.hijos[3])
            self.emitir(f"goto {l_fin}")
            self.poner(l_sino)
            self.accion(sino.hijos[1])
            self.poner(l_fin)

    def mientras(self, n):
        # Mientras → MIENTRAS Cond HACER Accion
        inicio, fin = self.etiqueta(), self.etiqueta()
        self.poner(inicio)
        cond = self.cond(n.hijos[1])      # la condición se evalúa en cada vuelta: su código va DENTRO del ciclo
        self.emitir(f"ifFalse {cond} goto {fin}")
        self.accion(n.hijos[3])
        self.emitir(f"goto {inicio}")
        self.poner(fin)

    def regla(self, n):
        """Traduce UNA regla y regresa sus renglones."""
        self.codigo = []
        hijo = n.hijos[0]
        if hijo.nombre == "Si":
            self.si(hijo)
        elif hijo.nombre == "Mientras":
            self.mientras(hijo)
        elif hijo.nombre == "Asig":
            self.asig(hijo)
        else:
            self.escribir(hijo)
        return self.codigo


def expresiones_con_operaciones(nodo):
    """Recorre el árbol en orden y regresa (línea, nodo-expresión) de cada Valor que tiene operaciones."""
    encontradas = []
    if nodo.nombre == "Valor" and nodo.hijos[0].hijos:
        e = nodo.hijos[0]
        encontradas.append((min(lineas_de(e)), e))
    for h in nodo.hijos:
        encontradas += expresiones_con_operaciones(h)
    return encontradas


def texto_de_la_regla(regla, fuente):
    """Las líneas originales del archivo que ocupa una regla, en un solo renglón."""
    ls = lineas_de(regla)
    return " ".join(fuente[i - 1].strip() for i in range(min(ls), max(ls) + 1))


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/codigo_intermedio.py archivo_de_reglas.txt")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    texto = leer_archivo(sys.argv[1])
    fuente = texto.split("\n")
    r = analizar(texto)

    print("== Notación postfija (una por cada expresión con operaciones) ==")
    for linea, e in expresiones_con_operaciones(r.arbol):
        print(f"  Línea {linea}: {texto_expr(e)}   →   Postfija: {postfija(e)}")

    print("\n== Código de tres direcciones (un solo generador: t1, t2... y L1, L2... no se repiten) ==")
    g = TresDirecciones()
    for regla in r.arbol.hijos:
        print(f"Línea {min(lineas_de(regla))}: {texto_de_la_regla(regla, fuente)}")
        print("\n".join(g.regla(regla)))
    if r.errores:
        print(f"\nNota: el archivo tiene {len(r.errores)} errores; solo se tradujeron las reglas que sí se reconocieron.")
    return 1 if r.errores else 0


if __name__ == "__main__":
    sys.exit(main())
