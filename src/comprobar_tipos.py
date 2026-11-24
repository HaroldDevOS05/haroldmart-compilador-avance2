# -*- coding: utf-8 -*-
"""
comprobar_tipos.py - Comprobación de tipos de Haroldmart (fase 4 del front-end)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL  (adaptación de tipos_base.py del profesor)

Revisa, SIN ejecutar nada, que cada operación tenga sentido para el negocio:
    descuento = total_compra + 15%     → error: no se puede sumar dinero con porcentaje
    envio = tipo_cliente               → error: 'envio' es dinero y le quieres guardar texto
    redondear(tasa)                    → error: el dato 1 de 'redondear' debe ser dinero y es porcentaje
El tipo de una expresión se calcula de las hojas hacia arriba (como el atributo «tipo» de la clase 23):
  * hoja: un literal tiene su tipo (5 numero, $5 dinero, 5% porcentaje, "x" texto); una variable, su tipo DECLARADO (tabla de símbolos)
  * operación: SISTEMA DE TIPOS = tabla (tipo izq, operador, tipo der) → tipo; lo que NO está en la tabla es un error
  * llamada: el tipo que regresa la función (su firma, funciones.py); cada dato debe ser del tipo que la firma pide
  * asignación: el tipo declarado de la variable debe ser IGUAL al tipo de lo que recibe (equivalencia de tipos)
  * comparación: se comparan tipos iguales (un numero con dinero también); el texto solo con == y !=
Si algo no está declarado el tipo es «?»: ya se avisó en la fase 3 y aquí no se repite el error.
La tabla de operaciones sale de combinar() de evaluar_atributos.py (la misma que usa el intérprete): una sola fuente de verdad.

Uso:
    python src/comprobar_tipos.py pruebas/promos_v4.txt
    python src/comprobar_tipos.py pruebas/promos_v4_tipos.txt
    python src/comprobar_tipos.py --tabla                      (imprime la tabla del sistema de tipos)
"""
import re
import sys

from parser_v4 import analizar, leer_archivo
from parser_con_recuperacion import lineas_de
from tabla_simbolos_v4 import construir
from escaner_v4 import TIPOS
from funciones import FUNCIONES
from evaluar_atributos import combinar, comparar_tipos, ErrorDeTipo, primera_linea

PALABRA = {interno: palabra for palabra, interno in TIPOS.items()}          # num → numero, porc → porcentaje ...
LITERAL = {"NUM": "num", "PRECIO": "dinero", "PORC": "porc", "CADENA": "cadena"}
VERBOS = ("+", "-", "*", "/")


def como_error_de_tipo(e):
    """«Línea 7: no se puede sumar…» → «Línea 7: error de tipo, no se puede sumar…» y con los nombres de tipo del lenguaje."""
    texto = re.sub(r"^Línea (\d+): ", r"Línea \1: error de tipo, ", str(e))
    for viejo, nuevo in (("un número", "numero"), ("un porcentaje", "porcentaje"), ("una cadena de texto", "texto")):
        texto = texto.replace(viejo, nuevo)
    return texto


class Comprobador:
    def __init__(self, tabla):
        self.tabla = tabla
        self.errores = []                                  # (línea, mensaje)

    def error(self, linea, mensaje):
        self.errores.append((linea, f"Línea {linea}: error de tipo, {mensaje}"))

    def declarado(self, nombre):
        palabra = self.tabla.simbolos.get(nombre, {}).get("tipo", "?")
        return TIPOS.get(palabra, "?")

    def tipo_de(self, n):
        """Tipo (num | dinero | porc | cadena | «?») de la expresión n."""
        if n.nombre == "Llamada":
            nombre = n.token[1]
            tipos = [self.tipo_de(h) for h in n.hijos]                 # también revisa lo de adentro
            if nombre not in FUNCIONES:
                return "?"                                             # ya se avisó en la fase 3
            parametros, regresa, _ = FUNCIONES[nombre]
            if len(parametros) == len(tipos):
                for k, (pedido, dado) in enumerate(zip(parametros, tipos), 1):
                    if dado != "?" and dado != TIPOS[pedido]:
                        self.error(n.token[2], f"el dato {k} de '{nombre}' debe ser {pedido} y es {PALABRA[dado]}")
            return TIPOS[regresa]
        if not n.hijos:
            if n.token[0] == "ID":
                return self.declarado(n.token[1])
            return LITERAL[n.token[0]]
        a, b = self.tipo_de(n.hijos[0]), self.tipo_de(n.hijos[1])
        if "?" in (a, b):
            return "?"
        try:
            return combinar(a, n.nombre, b, primera_linea(n))
        except ErrorDeTipo as e:
            self.errores.append((primera_linea(n), como_error_de_tipo(e)))
            return a                                                   # como tipos_base.py: se sigue con el tipo de la izquierda

    def condicion(self, n):
        ident, oprel, valor = n.hijos
        linea = ident.token[2]
        a, b = self.declarado(ident.token[1]), self.tipo_de(valor.hijos[0])
        if "?" in (a, b):
            return
        op = oprel.hijos[0].token[1]
        try:
            comparar_tipos(a, b, linea)
            if "cadena" in (a, b) and op not in ("==", "!="):
                raise ErrorDeTipo(f"Línea {linea}: el texto solo se compara con == o !=, no con {op}")
        except ErrorDeTipo as e:
            self.errores.append((linea, como_error_de_tipo(e)))

    def revisar(self, n):
        if n.nombre == "Decl":
            return
        if n.nombre == "Asig":
            ident, _, expr = n.hijos
            declarado, t = self.declarado(ident.token[1]), self.tipo_de(expr.hijos[0])
            if "?" not in (declarado, t) and declarado != t:
                self.error(ident.token[2], f"'{ident.token[1]}' es {PALABRA[declarado]} y le quieres guardar {PALABRA[t]}")
            return
        if n.nombre == "Cond":
            self.condicion(n)
            return
        if n.nombre == "Escribir":
            self.tipo_de(n.hijos[1].hijos[0])
            return
        for h in n.hijos:
            self.revisar(h)


def comprobar(r, tabla):
    """Revisa las reglas sin error léxico de un resultado de analizar(). Regresa la lista de mensajes ordenada por línea."""
    c = Comprobador(tabla)
    lineas_lexicas = {l for l, _ in r.errores_lexicos}
    for regla in r.arbol.hijos:
        if not (lineas_de(regla) & lineas_lexicas):
            c.revisar(regla)
    return [m for _, m in sorted(dict.fromkeys(c.errores), key=lambda par: par[0])]


def imprimir_sistema_de_tipos():
    """La tabla (tipo izq, operador, tipo der) → tipo, generada con combinar(): lo que no aparece es un error."""
    tipos = ["num", "dinero", "porc"]
    filas = []
    for op in VERBOS:
        for a in tipos:
            for b in tipos:
                try:
                    filas.append((PALABRA[a], op, PALABRA[b], PALABRA[combinar(a, op, b, 0)]))
                except ErrorDeTipo:
                    pass
    for op in VERBOS:
        validas = [f"{a} {op} {b} → {c}" for a, o, b, c in filas if o == op]
        print(f"  {op}   " + "  ·  ".join(validas))
    print("  (el texto no se opera con nada; cualquier combinación que no está en la lista es un error de tipo)")


def main():
    if "--tabla" in sys.argv:
        imprimir_sistema_de_tipos()
        return 0
    if len(sys.argv) < 2:
        print("Uso: python src/comprobar_tipos.py archivo_de_reglas.txt")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    r = analizar(leer_archivo(sys.argv[1]))
    errores = comprobar(r, construir(r))
    print(f"Comprobación de tipos: {len(errores)} error(es)")
    for e in errores:
        print("  " + e)
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
