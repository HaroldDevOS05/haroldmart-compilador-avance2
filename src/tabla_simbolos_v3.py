# -*- coding: utf-8 -*-
"""
tabla_simbolos_v3.py - Tabla de símbolos con tipo DECLARADO (versión 3 del lenguaje de Haroldmart)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL, día 1  (PASOS 3-4 y AHORA TÚ 2 de declaraciones_base.py)

Antes (Avance 3) el tipo de cada variable se INFERÍA de lo que se le asignaba. Ahora el dueño de las promociones lo
DECLARA («dinero total_compra») y la tabla guarda ese tipo. Una entrada de la tabla tiene:
      tipo (el declarado) · línea donde se declara · líneas donde se asigna · líneas donde se usa

  * ASIGNAR = que reciba un valor (descuento = ...).     USAR = que se lea su valor (en una condición, en una expresión, en ESCRIBIR).
  * Dato de la venta = declarada y nunca asignada (la trae la caja).    Resultado = la calcula una regla.
    Dato y resultado = viene de la caja y una regla lo cambia (se usa antes de asignarse: puntos = puntos - 100).

ERRORES DE DECLARACIÓN (están bien escritos pero no tienen sentido: son errores SEMÁNTICOS, cada uno con su línea):
  1. «'x' se usa sin declarar»              (se usa o se asigna una variable que ninguna declaración presentó antes)
  2. «'x' ya estaba declarada en la línea N» (se declara dos veces; se queda con la primera declaración)
  3. «'x' se declaró como T1 pero recibe T2» (la asignación no respeta el tipo declarado)   [extra mío]
Alcance: una declaración vale en TODO el archivo (alcance global), pero hay que declarar ANTES de usar.

Uso:
    python src/tabla_simbolos_v3.py pruebas/promos_v3.txt
    python src/tabla_simbolos_v3.py pruebas/promos_v3_errores.txt
"""
import sys

from parser_v3 import analizar, leer_archivo, nota_cascada, texto_expr
from parser_con_recuperacion import lineas_de
from escaner_v3 import TIPOS
from tabla_simbolos import tipo_de, lineas_sin_repetir

NOMBRE_DE_TIPO = {interno: palabra for palabra, interno in TIPOS.items()}      # num → numero, porc → porcentaje ...


class TablaDeclaraciones:
    def __init__(self, declaradas_con_error=()):
        self.simbolos = {}                       # nombre → {"tipo", "declarada", "asignada": [], "usos": []}
        self.errores = []                        # (línea, mensaje)
        self.avisos = []
        self.pendientes = set(declaradas_con_error)   # declaradas en una regla con error léxico (no se pudo leer su tipo)
        self.comprueba_asignacion = True              # (v4: la comprobación de tipos la hace comprobar_tipos.py)

    def entrada(self, nombre, tipo="?", declarada=None):
        return self.simbolos.setdefault(nombre, {"tipo": tipo, "declarada": declarada, "asignada": [], "usos": []})

    def declarar(self, nombre, tipo, linea):
        s = self.simbolos.get(nombre)
        if s and s["declarada"] is not None:
            self.errores.append((linea, f"Línea {linea}: '{nombre}' ya estaba declarada en la línea {s['declarada']}"))
            return                                # se queda con la primera declaración
        if s:                                     # ya se había usado antes de declararla: ese uso ya quedó como error
            s["tipo"], s["declarada"] = tipo, linea
            return
        self.entrada(nombre, tipo, linea)

    def buscar(self, nombre, linea, sugerencia="dinero"):
        """Regresa la entrada de la variable o anota el error «sin declarar» (una sola vez por variable)."""
        if nombre not in self.simbolos:
            if nombre in self.pendientes:         # su declaración tiene un error léxico: no es culpa de esta línea
                self.avisos.append(f"'{nombre}' se declara en una línea con error léxico; su tipo no se pudo leer")
            else:
                self.errores.append((linea, f"Línea {linea}: '{nombre}' se usa sin declarar (¿falta «{sugerencia} {nombre}»?)"))
            self.entrada(nombre)
        return self.simbolos[nombre]

    def usar(self, nombre, linea):
        self.buscar(nombre, linea)["usos"].append(linea)

    def asignar(self, nombre, linea, tipo_recibido, valor_texto, sugerencia):
        s = self.buscar(nombre, linea, sugerencia)
        s["asignada"].append(linea)
        declarado = TIPOS.get(s["tipo"])
        if self.comprueba_asignacion and declarado and tipo_recibido and declarado != tipo_recibido:
            self.errores.append((linea, f"Línea {linea}: '{nombre}' se declaró como {s['tipo']} pero recibe "
                                        f"{NOMBRE_DE_TIPO[tipo_recibido]} ({valor_texto})"))


def es_id(n):
    return not n.hijos and n.nombre == "ID" and bool(n.token)


def usos_en(n, tabla):
    if n.nombre == "Llamada":                  # (v4) una llamada: se revisa la función y sus datos son usos
        tabla.llamar(n.token[1], len(n.hijos), n.token[2])
    elif es_id(n):
        tabla.usar(n.token[1], n.token[2])
    for h in n.hijos:
        usos_en(h, tabla)


def tipos_declarados(tabla):
    """nombre → tipo interno (num, dinero, porc, cadena) de lo ya declarado, para calcular el tipo de una expresión."""
    return {n: TIPOS[s["tipo"]] for n, s in tabla.simbolos.items() if s["tipo"] in TIPOS}


def recorrer(nodo, tabla):
    """Recorre el árbol EN EL ORDEN DEL ARCHIVO: Decl = declaración; Asig = usos de la derecha y luego asignación;
    Cond y ESCRIBIR = usos."""
    if nodo.nombre == "Decl":
        tipo, ident = nodo.hijos
        tabla.declarar(ident.token[1], tipo.token[1], ident.token[2])
        return
    if nodo.nombre == "Asig":
        ident, _, valor = nodo.hijos
        usos_en(valor, tabla)
        recibido = tipo_de(valor.hijos[0], tipos_declarados(tabla)) if tabla.comprueba_asignacion else None
        sugerencia = NOMBRE_DE_TIPO.get(recibido, "dinero")
        tabla.asignar(ident.token[1], ident.token[2], recibido, texto_expr(valor.hijos[0]), sugerencia)
        return
    if nodo.nombre == "Cond":
        ident, _, valor = nodo.hijos
        tabla.usar(ident.token[1], ident.token[2])
        usos_en(valor, tabla)
        return
    if nodo.nombre == "Escribir":
        usos_en(nodo.hijos[1], tabla)
        return
    for h in nodo.hijos:
        recorrer(h, tabla)


def armar_tabla(arbol, lineas_con_error=(), clase_tabla=None):
    """Arma la tabla con las reglas que no tocan una línea con error léxico (esas reglas no son confiables)."""
    buenas, malas = [], []
    for regla in arbol.hijos:
        (malas if lineas_de(regla) & set(lineas_con_error) else buenas).append(regla)
    pendientes = set()
    for regla in malas:                                    # nombres que esas reglas intentaban declarar
        def buscar_decl(n):
            if n.nombre == "Decl":
                pendientes.add(n.hijos[1].token[1])
            for h in n.hijos:
                buscar_decl(h)
        buscar_decl(regla)
    tabla = (clase_tabla or TablaDeclaraciones)(pendientes)
    for regla in buenas:
        recorrer(regla, tabla)
    for nombre, s in tabla.simbolos.items():
        if s["declarada"] is not None and not s["asignada"] and not s["usos"]:
            tabla.avisos.append(f"'{nombre}' se declaró en la línea {s['declarada']} pero nunca se usa")
    tabla.errores.sort(key=lambda par: par[0])
    return tabla


def clase_de(s):
    if not s["asignada"]:
        return "dato de la venta"
    if s["usos"] and min(s["usos"]) <= min(s["asignada"]):
        return "dato y resultado"
    return "resultado"


def imprimir_tabla(tabla):
    print(f"{'Nombre':<18} {'Tipo':<11} {'Clase':<17} {'Declarada':<10} {'Asignada en':<12} Usada en")
    for nombre, s in tabla.simbolos.items():
        print(f"{nombre:<18} {s['tipo']:<11} {clase_de(s):<17} {str(s['declarada'] or '—'):<10} "
              f"{lineas_sin_repetir(s['asignada']):<12} {lineas_sin_repetir(s['usos'])}")
    print(f"Total: {len(tabla.simbolos)} variables")
    for aviso in dict.fromkeys(tabla.avisos):
        print("Aviso:", aviso)
    for _, mensaje in tabla.errores:
        print("Error:", mensaje)


def main():
    if len(sys.argv) < 2:
        print("Uso: python src/tabla_simbolos_v3.py archivo_de_reglas.txt")
        return 2
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    r = analizar(leer_archivo(sys.argv[1]))
    tabla = armar_tabla(r.arbol, {l for l, _ in r.errores_lexicos})
    if r.errores:
        print(f"Errores léxicos y sintácticos: {len(r.errores)} ({r.n_lexicos} léxicos, {r.n_sintacticos} sintácticos)")
        for e in r.errores:
            print("  " + e)
        if r.omitidos:
            print("  " + nota_cascada(r.omitidos))
        print()
    imprimir_tabla(tabla)
    return 1 if (r.errores or tabla.errores) else 0


if __name__ == "__main__":
    sys.exit(main())
