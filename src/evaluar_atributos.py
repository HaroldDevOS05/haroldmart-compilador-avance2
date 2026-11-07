# -*- coding: utf-8 -*-
"""
evaluar_atributos.py - Atributos val y tipo en las expresiones de Haroldmart, y aplicación de las promociones
Compiladores (IDS601) - UNEDL 2026B - AVANCE 3  (adaptación de atributos_base.py del profesor)

TRADUCCIÓN DIRIGIDA POR SINTAXIS: cada nodo del árbol calcula DOS atributos a partir de sus hijos:
    val   = su valor            tipo = num | dinero | porc | cadena

    Regla de la gramática          Regla semántica (val)                      tipo
    Factor → NUM                   el número                                   num
    Factor → PRECIO                la cantidad ($50 → 50)                      dinero
    Factor → PORC                  número / 100 (15% → 0.15)                   porc
    Factor → CADENA                el texto sin comillas                       cadena
    Factor → ID                    valor en la venta                           el de la venta
    E → E1 op T                    E.val = E1.val op T.val                     combinar(E1.tipo, op, T.tipo)

Son atributos SINTETIZADOS: se calculan con los atributos de los HIJOS (primero los dos hijos, luego el nodo).
combinar() es la COMPROBACIÓN DE TIPOS: un error de tipo es un error SEMÁNTICO (la regla está bien escrita,
la sintaxis es correcta, pero no tiene sentido: no se suma 15% con $50).

La «venta de prueba» (VENTAS) es lo que mandaría la caja de Haroldmart: nombre → (valor, tipo).
Este programa funciona como un INTÉRPRETE: recorre el árbol y aplica las promociones a esa venta.

Uso:
    python src/evaluar_atributos.py pruebas/promos_v2.txt                       (venta grande, la de por omisión)
    python src/evaluar_atributos.py pruebas/promos_v2.txt --venta chica
    python src/evaluar_atributos.py pruebas/promos_v2.txt --anotado             (muestra el árbol anotado de cada operación)
    python src/evaluar_atributos.py pruebas/error_de_tipo.txt
"""
import operator
import sys

from parser_v2 import analizar, leer_archivo, nota_cascada
from parser_con_recuperacion import lineas_de

# ---------------- La venta de prueba: nombre → (valor, tipo).  Datos inventados de Haroldmart ----------------
VENTAS = {
    "grande": {"total_compra": (1200, "dinero"), "km": (4, "num"), "piezas": (120, "num"),
               "edad": (65, "num"), "puntos": (250, "num")},
    "chica": {"total_compra": (320, "dinero"), "km": (4, "num"), "piezas": (30, "num"),
              "edad": (30, "num"), "puntos": (80, "num")},
}
VENTA = VENTAS["grande"]
TIPOS_DE_LA_VENTA = {nombre: tipo for nombre, (_, tipo) in VENTA.items()}    # lo usa la tabla de símbolos

LIMITE_DE_VUELTAS = 1000          # un MIENTRAS que no termina se corta con un error

OPERACIONES = {"+": operator.add, "-": operator.sub, "*": operator.mul, "/": operator.truediv}
COMPARACIONES = {"MAYOR": operator.gt, "MENOR": operator.lt, "MAYORIGUAL": operator.ge, "MENORIGUAL": operator.le}
VERBO = {"+": "sumar", "-": "restar", "*": "multiplicar", "/": "dividir"}
NOMBRE_DE_TIPO = {"num": "un número", "dinero": "dinero", "porc": "un porcentaje", "cadena": "una cadena de texto"}


class ErrorDeTipo(Exception):
    pass


# ---------------- Comprobación de tipos: ¿qué tipos se pueden operar? ----------------
def combinar(t1, op, t2, linea):
    """Tipo que resulta de «t1 op t2». Si la operación no tiene sentido, lanza ErrorDeTipo con la línea.

        +  -    num±num → num      dinero±dinero → dinero      porc±porc → porc
                dinero±num → dinero (un número suelto se toma como pesos)      porc con otro tipo → ERROR
        *       num×num → num      dinero×num | dinero×porc → dinero      num×porc → num      porc×porc → porc
                dinero×dinero → ERROR
        /       num÷num → num      dinero÷num | dinero÷porc → dinero      dinero÷dinero → num (cuántas veces cabe)
                num÷porc → num     porc÷num → porc      porc÷porc → num      lo demás con dinero en el divisor → ERROR
        cadena  no se puede operar con nada → ERROR
    """
    verbo = VERBO[op]
    if "cadena" in (t1, t2):
        raise ErrorDeTipo(f"Línea {linea}: no se puede {verbo} con una cadena de texto")
    par = {t1, t2}
    if op in ("+", "-"):
        if t1 == t2:
            return t1
        if par == {"num", "dinero"}:
            return "dinero"
        otro = t2 if t1 == "porc" else t1                      # lo que queda siempre mezcla un porcentaje
        raise ErrorDeTipo(f"Línea {linea}: no se puede {verbo} un porcentaje con {NOMBRE_DE_TIPO[otro]}")
    if op == "*":
        if t1 == t2 == "dinero":
            raise ErrorDeTipo(f"Línea {linea}: no se puede multiplicar dinero por dinero")
        if "dinero" in par:
            return "dinero"
        return t1 if t1 == t2 else "num"                       # num×num → num, porc×porc → porc, num×porc → num
    # op == "/"
    if t1 == "dinero":
        return "num" if t2 == "dinero" else "dinero"
    if t2 == "dinero":
        raise ErrorDeTipo(f"Línea {linea}: no se puede dividir {NOMBRE_DE_TIPO[t1]} entre dinero")
    return "porc" if (t1 == "porc" and t2 == "num") else "num"


def comparar_tipos(t1, t2, linea):
    """Solo se comparan cosas del mismo tipo (un número suelto se puede comparar con dinero)."""
    if t1 == t2 or {t1, t2} == {"num", "dinero"}:
        return
    raise ErrorDeTipo(f"Línea {linea}: no se puede comparar {NOMBRE_DE_TIPO[t1]} con {NOMBRE_DE_TIPO[t2]}")


# ---------------- Cómo se escribe un valor ----------------
def fmt_num(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def mostrar(val, tipo):
    if tipo == "dinero":
        return "$" + fmt_num(val)
    if tipo == "porc":
        return fmt_num(val * 100) + "%"
    if tipo == "cadena":
        return f'"{val}"'
    return fmt_num(val)


# ---------------- Los atributos: evaluar() ----------------
def primera_linea(n):
    return min(lineas_de(n))


def evaluar(n, venta, notas):
    """Regresa (val, tipo) del nodo n, y anota el resultado de cada nodo en notas[id(n)]."""
    if not n.hijos:
        # TODO 1: hoja (Factor). n.token = (tipo, lexema, línea)
        tipo, lex, linea = n.token
        if tipo == "NUM":
            val, t = float(lex), "num"
        elif tipo == "PRECIO":
            val, t = float(lex[1:]), "dinero"
        elif tipo == "PORC":
            val, t = float(lex[:-1]) / 100, "porc"
        elif tipo == "CADENA":
            val, t = lex[1:-1], "cadena"
        else:                                                   # ID: el valor sale de la venta
            if lex not in venta:
                raise ErrorDeTipo(f"Línea {linea}: la venta no trae el dato '{lex}'")
            val, t = venta[lex]
        notas[id(n)] = (val, t)
        return val, t
    # TODO 2: operación. Primero los hijos (atributos sintetizados), luego el nodo.
    a, ta = evaluar(n.hijos[0], venta, notas)
    b, tb = evaluar(n.hijos[1], venta, notas)
    linea = primera_linea(n)
    tipo = combinar(ta, n.nombre, tb, linea)
    if n.nombre == "/" and b == 0:
        raise ErrorDeTipo(f"Línea {linea}: división entre cero")
    val = OPERACIONES[n.nombre](a, b)
    notas[id(n)] = (val, tipo)
    return val, tipo


def arbol_anotado(n, notas, prefijo="", es_ultimo=True, es_raiz=True):
    """Dibuja el árbol con el valor de cada atributo en cada nodo."""
    val, tipo = notas[id(n)]
    nombre = n.token[1] if not n.hijos else n.nombre
    etiqueta = f"{nombre}   [val = {mostrar(val, tipo)}, tipo = {tipo}]"
    if es_raiz:
        salida, prefijo_hijos = [etiqueta], ""
    else:
        salida = [prefijo + ("└─ " if es_ultimo else "├─ ") + etiqueta]
        prefijo_hijos = prefijo + ("   " if es_ultimo else "│  ")
    for k, h in enumerate(n.hijos):
        salida += arbol_anotado(h, notas, prefijo_hijos, k == len(n.hijos) - 1, False)
    return salida


# ---------------- El intérprete: aplicar las promociones a una venta ----------------
def evaluar_cond(n, venta, notas):
    # Cond → ID Oprel Valor
    ident, oprel, valor = n.hijos
    nombre, linea = ident.token[1], ident.token[2]
    if nombre not in venta:
        raise ErrorDeTipo(f"Línea {linea}: la venta no trae el dato '{nombre}'")
    a, ta = venta[nombre]
    b, tb = evaluar(valor.hijos[0], venta, notas)
    comparar_tipos(ta, tb, linea)
    return COMPARACIONES[oprel.hijos[0].token[0]](a, b)


def ejecutar_asig(n, venta, salida, anotar):
    ident, _, valor = n.hijos
    notas = {}
    val, tipo = evaluar(valor.hijos[0], venta, notas)
    venta[ident.token[1]] = (val, tipo)                       # el resultado queda disponible para las reglas que siguen
    salida(f"  línea {ident.token[2]}: {ident.token[1]} = {mostrar(val, tipo)} ({tipo})")
    if anotar and valor.hijos[0].hijos:
        for renglon in arbol_anotado(valor.hijos[0], notas):
            salida("        " + renglon)


def ejecutar_escribir(n, venta, salida, anotar):
    notas = {}
    val, tipo = evaluar(n.hijos[1].hijos[0], venta, notas)
    salida(f"  línea {n.hijos[0].token[2]}: ESCRIBIR {mostrar(val, tipo)}")


def ejecutar_accion(n, venta, salida, anotar):
    hijo = n.hijos[0]                                          # Accion → Asig | Escribir
    (ejecutar_asig if hijo.nombre == "Asig" else ejecutar_escribir)(hijo, venta, salida, anotar)


def ejecutar_regla(n, venta, salida, anotar):
    hijo = n.hijos[0]
    if hijo.nombre == "Si":
        if evaluar_cond(hijo.hijos[1], venta, {}):
            ejecutar_accion(hijo.hijos[3], venta, salida, anotar)
        elif len(hijo.hijos) > 4:                              # hay SINO
            ejecutar_accion(hijo.hijos[4].hijos[1], venta, salida, anotar)
    elif hijo.nombre == "Mientras":
        vueltas = 0
        while evaluar_cond(hijo.hijos[1], venta, {}):
            ejecutar_accion(hijo.hijos[3], venta, salida, anotar)
            vueltas += 1
            if vueltas >= LIMITE_DE_VUELTAS:
                raise ErrorDeTipo(f"Línea {primera_linea(hijo)}: el ciclo MIENTRAS no termina (más de {LIMITE_DE_VUELTAS} vueltas)")
    elif hijo.nombre == "Asig":
        ejecutar_asig(hijo, venta, salida, anotar)
    else:
        ejecutar_escribir(hijo, venta, salida, anotar)


def aplicar_promociones(arbol, venta, salida=print, anotar=False):
    """Ejecuta cada regla del árbol sobre una COPIA de la venta. Un error de tipo se reporta con su línea
    y se sigue con la regla siguiente. Regresa (reglas_ejecutadas, errores_de_tipo, venta_final)."""
    venta = dict(venta)
    errores, ejecutadas = [], 0
    for regla in arbol.hijos:
        try:
            ejecutar_regla(regla, venta, salida, anotar)
            ejecutadas += 1
        except ErrorDeTipo as e:
            errores.append(str(e))
            salida(f"  Error de tipo: {e}")
    return ejecutadas, errores, venta


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("Uso: python src/evaluar_atributos.py archivo_de_reglas.txt [--venta grande|chica] [--anotado]")
        return 2
    nombre_venta = "grande"
    if "--venta" in sys.argv:
        nombre_venta = sys.argv[sys.argv.index("--venta") + 1]
        args = [a for a in args if a != nombre_venta]
        if nombre_venta not in VENTAS:
            print(f"No existe la venta '{nombre_venta}'. Hay: {', '.join(VENTAS)}")
            return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    venta = {k: (float(v), t) for k, (v, t) in VENTAS[nombre_venta].items()}
    r = analizar(leer_archivo(args[0]))

    print(f"Venta de prueba ({nombre_venta}): " + ", ".join(f"{k} = {mostrar(v, t)}" for k, (v, t) in venta.items()))
    print("\nAplicando las promociones:")
    ejecutadas, errores_tipo, _ = aplicar_promociones(r.arbol, venta, anotar="--anotado" in sys.argv)
    print(f"\nReglas ejecutadas: {ejecutadas} · errores de tipo: {len(errores_tipo)}")
    if r.errores:
        print(f"Nota: el archivo tiene {len(r.errores)} errores léxicos o sintácticos; solo se ejecutaron las reglas que se reconocieron.")
    return 1 if errores_tipo or r.errores else 0


if __name__ == "__main__":
    sys.exit(main())
