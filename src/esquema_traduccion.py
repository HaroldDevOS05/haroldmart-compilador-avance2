# -*- coding: utf-8 -*-
"""
esquema_traduccion.py - Esquema de traducción de las expresiones de Haroldmart a postfija
Compiladores (IDS601) - UNEDL 2026B - AVANCE 3  (adaptación de esquema_base.py del profesor, TODO 1-3)

Traduce una expresión a notación postfija MIENTRAS la analiza, sin armar el árbol (traducción en una pasada).
Es la gramática de expresiones con ACCIONES { emitir(...) } puestas en el lugar exacto:

    Expr   → Term ExprR
    ExprR  → + Term { emitir("+") } ExprR  |  - Term { emitir("-") } ExprR  |  ε
    Term   → Factor TermR
    TermR  → * Factor { emitir("*") } TermR  |  / Factor { emitir("/") } TermR  |  ε
    Factor → ( Expr )  |  num { emitir(num) }  |  precio { emitir(precio) }  |  porc { emitir(porc) }
             |  id { emitir(id) }  |  cadena { emitir(cadena) }

* La definición dirigida por sintaxis (miércoles) DICE qué calcular; el esquema de traducción (hoy) dice
  también CUÁNDO hacerlo: la acción emitir(op) va DESPUÉS de reconocer el segundo operando. Si fuera antes
  de Term, el operador saldría primero (prefija).
* Las hojas emiten su lexema en cuanto se reconocen.

Uso:
    python src/esquema_traduccion.py "precio * 2 + 10"
    python src/esquema_traduccion.py "(precio - descuento) * cantidad + envio"
    python src/esquema_traduccion.py "precio * * 2"          (con error)
    python src/esquema_traduccion.py --comparar               (compara el esquema con la postfija del árbol)
"""
import sys

from escaner_v2 import escanear

HOJAS = ("NUM", "PRECIO", "PORC", "CADENA", "ID")


class ErrorDeTraduccion(Exception):
    pass


class Traductor:
    def __init__(self, texto):
        tokens, errores_lexicos = escanear(texto)
        if errores_lexicos:                                   # el esquema trabaja con tokens válidos
            _, mensaje = errores_lexicos[0]
            raise ErrorDeTraduccion(f"{mensaje} (error léxico)")
        self.tokens = [(tipo, lexema, linea) for linea, tipo, lexema, _ in tokens] + [("$", "el fin de la expresión", 0)]
        self.pos = 0
        self.salida = []                                      # la postfija que se va armando
        self.acciones = []                                    # bitácora: (lo que se emitió, cómo va la salida)

    def actual(self):
        return self.tokens[self.pos][0]

    def lexema(self):
        return self.tokens[self.pos][1]

    def llego(self):
        return self.lexema() if self.actual() == "$" else f"'{self.lexema()}'"

    def emparejar(self, tipo, nombre):
        if self.actual() != tipo:
            raise ErrorDeTraduccion(f"se esperaba {nombre} y llegó {self.llego()}")
        lex = self.lexema()
        self.pos += 1
        return lex

    def emitir(self, x):                 # la ACCIÓN semántica
        self.salida.append(x)
        self.acciones.append((x, " ".join(self.salida)))

    def traducir(self):
        self.expr()
        if self.actual() != "$":         # sobró algo después de la expresión
            raise ErrorDeTraduccion(f"se esperaba el fin de la expresión y llegó {self.llego()}")
        return " ".join(self.salida)

    def expr(self):
        self.term()
        self.expr_r()

    def expr_r(self):
        if self.actual() in ("MAS", "MENOS"):
            op = self.emparejar(self.actual(), "un operador")
            self.term()                  # TODO 1: primero el segundo operando...
            self.emitir(op)              # ...y DESPUÉS la acción: el operador va al final (postfija)
            self.expr_r()

    def term(self):
        self.factor()
        self.term_r()

    def term_r(self):
        if self.actual() in ("POR", "ENTRE"):
            op = self.emparejar(self.actual(), "un operador")
            self.factor()                # TODO 2: igual que expr_r pero con factor() y term_r()
            self.emitir(op)
            self.term_r()

    def factor(self):
        if self.actual() == "PARIZQ":
            self.emparejar("PARIZQ", "«(»")
            self.expr()
            self.emparejar("PARDER", "«)»")
        elif self.actual() in HOJAS:
            self.emitir(self.emparejar(self.actual(), "un valor"))     # TODO 3: la hoja emite su lexema
        else:
            raise ErrorDeTraduccion(f"se esperaba un valor y llegó {self.llego()}")


def postfija_del_arbol(expresion):
    """La postfija que sale del ÁRBOL (parser_v2 + codigo_intermedio): la «x = » solo sirve para que sea una regla."""
    from parser_v2 import analizar
    from codigo_intermedio import postfija
    r = analizar("x = " + expresion)
    if r.errores:
        raise ErrorDeTraduccion(r.errores[0])
    return postfija(r.arbol.hijos[0].hijos[0].hijos[2].hijos[0])      # Programa → Regla → Asig → Valor → Expr


EXPRESIONES = [
    "precio * 2 + 10",
    "(precio - descuento) * cantidad + envio",
    "total_compra * 5%",
    "km * 2 + $30",
    "puntos - 100",
    "a - b - c",
    "a + b * c - (d - e) / f",
]


def comparar():
    ancho = max(len(e) for e in EXPRESIONES) + 2
    print(f"{'Expresión':<{ancho}}{'Esquema (en una pasada)':<44}{'Postfija del árbol':<44}¿Igual?")
    todas = True
    for e in EXPRESIONES:
        a = Traductor(e).traducir()
        b = postfija_del_arbol(e)
        todas = todas and a == b
        print(f"{e:<{ancho}}{a:<44}{b:<44}{'sí' if a == b else 'NO'}")
    print("\n" + ("El esquema y el árbol dan lo mismo en las %d expresiones." % len(EXPRESIONES) if todas else "¡HAY DIFERENCIAS!"))
    return 0 if todas else 1


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    if "--comparar" in sys.argv:
        return comparar()
    texto = sys.argv[1] if len(sys.argv) > 1 else "precio * 2 + 10"      # prueba también con paréntesis
    print("Expresión:", texto)
    try:
        t = Traductor(texto)
        postfija = t.traducir()
    except ErrorDeTraduccion as e:
        print("Error:", e)
        return 1
    print("Acciones, en el orden en que se ejecutan:")
    for k, (x, parcial) in enumerate(t.acciones, 1):
        print(f"  {k}. emitir({x}) → {parcial}")
    print("Postfija:", postfija)
    return 0


if __name__ == "__main__":
    sys.exit(main())
