# -*- coding: utf-8 -*-
"""
parser_Haroldmart.py - Parser descendente recursivo (LL(1)) del lenguaje de reglas de Haroldmart
Compiladores (IDS601) - UNEDL 2026B - AVANCE 2

Una función por cada no terminal de la gramática (ver README):

     1. Programa  → Regla Programa | ε          (la recursión final se escribe como un ciclo)
     2. Regla     → Si | Mientras | Asig | Escribir
     3. Si        → SI Cond ENTONCES Accion Sino
     4. Sino      → SINO Accion | ε
     5. Mientras  → MIENTRAS Cond HACER Accion
     6. Accion    → Asig | Escribir
     7. Asig      → ID ASIGNA Valor
     8. Escribir  → ESCRIBIR Valor
     9. Cond      → ID Oprel Valor
    10. Oprel     → MAYOR | MENOR | MAYORIGUAL | MENORIGUAL
    11. Valor     → NUM | PRECIO | CADENA

Los terminales son los tipos de token que entrega escaner_Haroldmart.py.

Este parser se detiene en el PRIMER error. La versión que reporta todos los errores y sigue
revisando está en parser_con_recuperacion.py (hereda de la clase Parser de este archivo).

Uso:
    python src/parser_Haroldmart.py pruebas/avance2_tres_reglas.txt
"""
import sys
from escaner_Haroldmart import escanear

# Cómo se le llama a cada terminal en los mensajes de error (pensados para el dueño del negocio)
NOMBRES = {
    "SI": "SI", "ENTONCES": "ENTONCES", "SINO": "SINO", "MIENTRAS": "MIENTRAS",
    "HACER": "HACER", "ESCRIBIR": "ESCRIBIR",
    "ID": "una variable", "ASIGNA": "el signo =",
    "NUM": "un número", "PRECIO": "un precio ($...)", "CADENA": "una cadena entre comillas",
}


class ErrorSintactico(Exception):
    pass


class Nodo:
    """Nodo del árbol sintáctico. Las hojas guardan su token: (tipo, lexema, línea)."""

    def __init__(self, nombre, hijos=None, token=None):
        self.nombre = nombre
        self.hijos = hijos or []
        self.token = token

    def etiqueta(self):
        return f"{self.nombre}: {self.token[1]}" if self.token else self.nombre

    def lineas(self, prefijo="", es_ultimo=True, es_raiz=True):
        """Dibuja el árbol con ├─ └─ │ (una cadena por renglón)."""
        if es_raiz:
            salida, prefijo_hijos = [self.etiqueta()], ""
        else:
            salida = [prefijo + ("└─ " if es_ultimo else "├─ ") + self.etiqueta()]
            prefijo_hijos = prefijo + ("   " if es_ultimo else "│  ")
        for k, h in enumerate(self.hijos):
            salida += h.lineas(prefijo_hijos, k == len(self.hijos) - 1, False)
        return salida


def leer_tokens(texto):
    """Llama al escáner del Avance 1 y deja los tokens en la forma que usa el parser:
    [(tipo, lexema, línea), ..., ("$", "$", línea)]  más la lista de errores léxicos [(línea, mensaje)]."""
    tokens, errores_lexicos = escanear(texto)
    lista = [(tipo, lexema, linea) for linea, tipo, lexema, _camino in tokens]
    lista.append(("$", "$", texto.count("\n") + 1))          # marca de fin de entrada
    return lista, errores_lexicos


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- utilidades ----------
    def actual(self):
        return self.tokens[self.pos]

    def tipo(self):
        return self.tokens[self.pos][0]

    def linea(self):
        return self.tokens[self.pos][2]

    def error(self, esperado, en_regla=True):
        """Lanza el error con su línea. Si la regla se cortó al final del renglón (el token que
        llegó está en un renglón posterior), el error se reporta en el renglón donde quedó incompleta."""
        tipo, lexema, linea = self.actual()
        if tipo == "$":
            llego = "llegó el fin del archivo"
        else:                                  # en las palabras reservadas el tipo es igual al lexema
            llego = f"llegó '{lexema}'" + (f" ({tipo})" if tipo != lexema else "")
        if en_regla and self.pos > 0 and self.tokens[self.pos - 1][2] < linea:
            linea = self.tokens[self.pos - 1][2]
            llego = "la línea terminó"
        raise ErrorSintactico(f"Línea {linea}: error de sintaxis, se esperaba {esperado} y {llego}")

    def emparejar(self, tipo):
        """Consume el token si es del tipo esperado y regresa su hoja; si no, error."""
        if self.tipo() != tipo:
            self.error(NOMBRES.get(tipo, tipo))
        hoja = Nodo(tipo, token=self.actual())
        self.pos += 1
        return hoja

    # ---------- una función por no terminal ----------
    def programa(self):
        # Programa → Regla Programa | ε    (ε cuando llega "$")
        reglas = []
        while self.tipo() != "$":
            reglas.append(self.regla())
        return Nodo("Programa", reglas)

    def regla(self):
        # Regla → Si | Mientras | Asig | Escribir
        t = self.tipo()
        if t == "SI":
            hijo = self.si()
        elif t == "MIENTRAS":
            hijo = self.mientras()
        elif t == "ID":
            hijo = self.asig()
        elif t == "ESCRIBIR":
            hijo = self.escribir()
        else:
            self.error("SI, MIENTRAS, ESCRIBIR o una variable al inicio de la regla", en_regla=False)
        return Nodo("Regla", [hijo])

    def si(self):
        # Si → SI Cond ENTONCES Accion Sino
        hijos = [self.emparejar("SI"), self.cond(), self.emparejar("ENTONCES"), self.accion()]
        resto = self.sino()
        if resto:
            hijos.append(resto)
        return Nodo("Si", hijos)

    def sino(self):
        # Sino → SINO Accion | ε     (ε cuando no viene SINO: la regla ya terminó)
        if self.tipo() == "SINO":
            return Nodo("Sino", [self.emparejar("SINO"), self.accion()])
        return None

    def mientras(self):
        # Mientras → MIENTRAS Cond HACER Accion
        return Nodo("Mientras", [self.emparejar("MIENTRAS"), self.cond(), self.emparejar("HACER"), self.accion()])

    def accion(self):
        # Accion → Asig | Escribir
        t = self.tipo()
        if t == "ID":
            return Nodo("Accion", [self.asig()])
        if t == "ESCRIBIR":
            return Nodo("Accion", [self.escribir()])
        self.error("una acción (variable = valor, o ESCRIBIR valor)")

    def asig(self):
        # Asig → ID ASIGNA Valor
        return Nodo("Asig", [self.emparejar("ID"), self.emparejar("ASIGNA"), self.valor()])

    def escribir(self):
        # Escribir → ESCRIBIR Valor
        return Nodo("Escribir", [self.emparejar("ESCRIBIR"), self.valor()])

    def cond(self):
        # Cond → ID Oprel Valor
        return Nodo("Cond", [self.emparejar("ID"), self.oprel(), self.valor()])

    def oprel(self):
        # Oprel → MAYOR | MENOR | MAYORIGUAL | MENORIGUAL
        if self.tipo() in ("MAYOR", "MENOR", "MAYORIGUAL", "MENORIGUAL"):
            return Nodo("Oprel", [self.emparejar(self.tipo())])
        self.error("un operador de comparación (>, <, >=, <=)")

    def valor(self):
        # Valor → NUM | PRECIO | CADENA
        if self.tipo() in ("NUM", "PRECIO", "CADENA"):
            return Nodo("Valor", [self.emparejar(self.tipo())])
        self.error("un valor (número, precio con $ o cadena entre comillas)")


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/parser_Haroldmart.py archivo_de_reglas.txt")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    with open(sys.argv[1], encoding="utf-8-sig") as f:
        texto = f.read()

    tokens, errores_lexicos = leer_tokens(texto)
    if errores_lexicos:
        print("El escáner encontró errores léxicos (el parser no corre hasta corregirlos):")
        for linea, mensaje in errores_lexicos:
            print(f"  Línea {linea}: error léxico, {mensaje}")
        return 1
    try:
        arbol = Parser(tokens).programa()
    except ErrorSintactico as e:
        print(e)
        print("El análisis se detiene en el primer error; parser_con_recuperacion.py muestra todos.")
        return 1
    print("\n".join(arbol.lineas()))
    print(f"\nReglas reconocidas: {len(arbol.hijos)} · errores: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
