#!/bin/bash
# Corre todas las pruebas del Avance 3 y guarda cada salida en salidas/  (desde la carpeta del proyecto: bash correr_todo.sh)
cd "$(dirname "$0")"
mkdir -p salidas
PY=python3; command -v python3 >/dev/null || PY=python
S=salidas
$PY src/verificar_gramatica.py --tabla            > $S/a3_verificar_gramatica_v2.txt
$PY src/escaner_v2.py pruebas/promos_v2.txt       > $S/a3_escaner_promos_v2.txt
$PY src/parser_v2.py pruebas/promos_v2.txt        > $S/a3_arbol_promos_v2.txt
$PY src/codigo_intermedio.py pruebas/promos_v2.txt > $S/a3_postfija_y_tres_direcciones.txt
$PY src/esquema_traduccion.py "precio * 2 + 10"   > $S/a3_esquema_traduccion.txt
$PY src/esquema_traduccion.py "(precio - descuento) * cantidad + envio" >> $S/a3_esquema_traduccion.txt
$PY src/esquema_traduccion.py "precio * * 2"      >> $S/a3_esquema_traduccion.txt
$PY src/esquema_traduccion.py --comparar          > $S/a3_esquema_vs_arbol.txt
$PY src/evaluar_atributos.py pruebas/promos_v2.txt --venta grande --anotado > $S/a3_atributos_venta_grande.txt
$PY src/evaluar_atributos.py pruebas/promos_v2.txt --venta chica  > $S/a3_atributos_venta_chica.txt
$PY src/evaluar_atributos.py pruebas/error_de_tipo.txt            > $S/a3_errores_de_tipo.txt
$PY src/tabla_simbolos.py pruebas/promos_v2.txt                   > $S/a3_tabla_simbolos_promos_v2.txt
$PY src/tabla_simbolos.py pruebas/promos_tipos_distintos.txt      > $S/a3_tabla_simbolos_tipos_distintos.txt
$PY src/tabla_simbolos.py pruebas/avance3_error_lexico.txt        > $S/a3_programa1_error_lexico.txt
$PY src/tabla_simbolos.py pruebas/avance3_error_sintactico.txt    > $S/a3_programa2_error_sintactico.txt
$PY src/pruebas_cruzadas.py                                       > $S/a3_pruebas_cruzadas.txt
echo "Listo: salidas guardadas en la carpeta salidas/ (archivos a3_*.txt)"
