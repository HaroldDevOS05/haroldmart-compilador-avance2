# -*- coding: utf-8 -*-
"""
parser_con_recuperacion.py - Recuperación de errores para el parser de Haroldmart
Compiladores (IDS601) - UNEDL 2026B - AVANCE 2 (basado en recuperacion_base.py del profesor)

parser_Haroldmart.py se detiene en el PRIMER error. Aquí se extiende para que:
  - modo pánico: reporte el error con su línea, salte tokens hasta el inicio de la siguiente regla
    (en otro renglón) o hasta el fin, y SIGA revisando;
  - nivel de frase: si falta ENTONCES/HACER y ya viene la acción, lo avise y lo «suponga».

También junta los errores léxicos del escáner con los sintácticos y los muestra ordenados por línea.

Uso (desde la carpeta del proyecto):
    python src/parser_con_recuperacion.py pruebas/errores_sintacticos.txt
    python src/parser_con_recuperacion.py pruebas/avance2_tres_reglas.txt       (sin errores: imprime el árbol)
    python src/parser_con_recuperacion.py pruebas/avance2_tres_reglas.txt --arbol   (fuerza imprimir el árbol)
"""
import re
import sys
from parser_Haroldmart import Parser, Nodo, ErrorSintactico, leer_tokens

INICIO_DE_REGLA = ("SI", "MIENTRAS", "ID", "ESCRIBIR")      # TODO 0: FIRST(Regla) con las palabras de MI lenguaje


class ParserConRecuperacion(Parser):
    def __init__(self, tokens):
        super().__init__(tokens)
        self.errores = []

    def programa(self):
        # TODO 1: cada regla dentro de try; si falla, se guarda el error y se salta con modo pánico.
        reglas = []
        while self.tipo() != "$":
            inicio = self.linea()                      # línea donde EMPIEZA la regla
            try:
                if self.tipo() not in INICIO_DE_REGLA:
                    self.error("SI, MIENTRAS, ESCRIBIR o una variable al inicio de la regla", en_regla=False)
                reglas.append(self.regla())
            except ErrorSintactico as e:
                self.errores.append(str(e))
                self.modo_panico(inicio)
        return Nodo("Programa", reglas)

    def modo_panico(self, inicio):
        # TODO 2: avanza mientras NO sea "$" y NO (la línea sea mayor que «inicio» y el token inicie una regla).
        # Siempre avanza al menos hasta salir del renglón donde empezó la regla, así que nunca se cicla.
        while self.tipo() != "$" and not (self.linea() > inicio and self.tipo() in INICIO_DE_REGLA):
            self.pos += 1

    def emparejar(self, tipo):
        # TODO 3 (nivel de frase): si falta ENTONCES/HACER y ya viene la acción, lo avisa y lo supone.
        if tipo in ("ENTONCES", "HACER") and self.tipo() in ("ID", "ESCRIBIR"):
            _, lexema, linea = self.actual()
            self.errores.append(f"Línea {linea}: se esperaba {tipo} antes de '{lexema}' (lo supuse para seguir)")
            return Nodo(tipo, token=(tipo, "(supuesto)", linea))     # sin avanzar
        return super().emparejar(tipo)


def numero_de_linea(mensaje):
    return int(re.match(r"Línea (\d+)", mensaje).group(1))


def lineas_de(nodo):
    """Números de línea de todos los tokens de un subárbol."""
    if nodo.token:
        return {nodo.token[2]}
    lineas = set()
    for h in nodo.hijos:
        lineas |= lineas_de(h)
    return lineas


def analizar(texto):
    """Escáner + parser con recuperación.
    Devuelve (árbol, errores_ordenados, n_léxicos, n_sintácticos, omitidos, reglas_reconocidas)."""
    tokens, errores_lexicos = leer_tokens(texto)
    parser = ParserConRecuperacion(tokens)
    arbol = parser.programa()
    lineas_lexicas = {linea for linea, _ in errores_lexicos}
    # una regla cuenta como reconocida si no tiene ningún símbolo con error léxico en sus renglones
    reconocidas = sum(1 for regla in arbol.hijos if not (lineas_de(regla) & lineas_lexicas))
    lexicos = [(linea, f"Línea {linea}: error léxico, {m}") for linea, m in errores_lexicos]
    sintacticos, omitidos = [], 0
    for e in parser.errores:
        linea = numero_de_linea(e)
        if linea in lineas_lexicas:          # consecuencia de un símbolo ya reportado por el escáner
            omitidos += 1
        else:
            sintacticos.append((linea, e))
    todos = sorted(lexicos + sintacticos, key=lambda par: par[0])
    return arbol, [m for _, m in todos], len(lexicos), len(sintacticos), omitidos, reconocidas


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/parser_con_recuperacion.py archivo_de_reglas.txt [--arbol]")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    with open(sys.argv[1], encoding="utf-8-sig") as f:
        texto = f.read()
    arbol, errores, n_lex, n_sint, omitidos, reconocidas = analizar(texto)

    if not errores or "--arbol" in sys.argv:
        print("\n".join(arbol.lineas()))
        print()
    print(f"Reglas reconocidas: {reconocidas} · errores: {len(errores)}"
          + (f" ({n_lex} léxicos, {n_sint} sintácticos)" if errores else ""))
    for e in errores:
        print("  " + e)
    if omitidos:
        print(f"  (se omitieron {omitidos} errores de sintaxis en renglones que ya tienen un error léxico: son consecuencia)")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
