# -*- coding: utf-8 -*-
"""
funciones.py - Las funciones PREDEFINIDAS de Haroldmart (las «teclas de la caja registradora»)
Compiladores (IDS601) - UNEDL 2026B - ENTREGA FINAL

El administrador las USA en sus reglas pero no las escribe. Cada una tiene su FIRMA: qué datos recibe, de qué tipo, y qué regresa.
Esta tabla la usan tres piezas: la tabla de símbolos (¿existe? ¿cuántos datos?), la comprobación de tipos (¿de qué tipo es cada dato?)
y el evaluador (¿cuánto da?).

    redondear(dinero) → dinero                   redondear($127.40) = $127        (al peso más cercano)
    aplicar_descuento(dinero, porcentaje) → dinero   aplicar_descuento($200, 10%) = $180   (precio con descuento)
    minimo(dinero, dinero) → dinero              minimo($180, $150) = $150        (el menor de dos: sirve de TOPE)
"""
import math

# nombre → (tipos de los datos, tipo que regresa, ejemplo)   Los tipos se escriben con las palabras del lenguaje.
FUNCIONES = {
    "redondear": (["dinero"], "dinero", "redondea al peso: redondear($127.40) = $127"),
    "aplicar_descuento": (["dinero", "porcentaje"], "dinero", "precio con descuento: aplicar_descuento($200, 10%) = $180"),
    "minimo": (["dinero", "dinero"], "dinero", "el menor de dos (un tope): minimo($180, $150) = $150"),
}

# Lo que calcula cada una (los datos llegan como números: el porcentaje como fracción, 10% → 0.10)
CALCULO = {
    "redondear": lambda a: math.floor(a + 0.5),
    "aplicar_descuento": lambda precio, pct: precio * (1 - pct),
    "minimo": lambda a, b: min(a, b),
}

NOMBRES_DISPONIBLES = ", ".join(FUNCIONES)
