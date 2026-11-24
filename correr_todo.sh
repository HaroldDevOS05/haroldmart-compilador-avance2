#!/bin/bash
# Corre todas las pruebas del Avance 3 y guarda cada salida en salidas/  (desde la carpeta del proyecto: bash correr_todo.sh)
cd "$(dirname "$0")"
mkdir -p salidas
PY=python3; command -v python3 >/dev/null || PY=python
S=salidas
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
# --- Entrega final, día 1: declaraciones con tipo (Clase 25) ---
$PY src/escaner_v3.py pruebas/promos_v3.txt                   > $S/a4_escaner_promos_v3.txt
$PY src/parser_v3.py pruebas/promos_v3.txt --arbol            > $S/a4_arbol_promos_v3.txt
$PY src/tabla_simbolos_v3.py pruebas/promos_v3.txt            > $S/a4_tabla_declaraciones.txt
$PY src/tabla_simbolos_v3.py pruebas/promos_v3_errores.txt    > $S/a4_errores_de_declaracion.txt
$PY src/tabla_simbolos_v3.py pruebas/promos_v3_si_sin_sino.txt > $S/a4_si_sin_sino_y_declaracion.txt
# --- ENTREGA FINAL: llamadas a funciones, igualdad, comprobación de tipos y el analizador completo (a5_*) ---
$PY src/verificar_gramatica.py --tabla                         > $S/a5_verificar_gramatica_v4.txt
$PY src/escaner_v4.py pruebas/promos_v4.txt                    > $S/a5_escaner_promos_v4.txt
$PY src/escaner_v4.py pruebas/defensa_afd.txt --traza          > $S/a5_escaner_traza_afd.txt
$PY src/parser_v4.py pruebas/promos_v4.txt --arbol             > $S/a5_arbol_promos_v4.txt
$PY src/codigo_intermedio.py pruebas/promos_v4.txt             > $S/a5_postfija_y_tres_direcciones_v4.txt
$PY src/evaluar_atributos.py pruebas/promos_v4.txt --venta grande --anotado > $S/a5_atributos_v4_venta_grande.txt
$PY src/evaluar_atributos.py pruebas/promos_v4.txt --venta chica           > $S/a5_atributos_v4_venta_chica.txt
$PY src/analizar_todo.py pruebas/promos_v4.txt --tabla         > $S/a5_analizar_todo_promos_v4.txt
$PY src/analizar_todo.py pruebas/promos_v4_errores.txt         > $S/a5_errores_declaracion_y_funciones.txt
$PY src/analizar_todo.py pruebas/promos_v4_tipos.txt           > $S/a5_errores_de_tipo_v4.txt
$PY src/comprobar_tipos.py --tabla                             > $S/a5_sistema_de_tipos.txt
$PY src/analizar_todo.py pruebas/final_error_lexico.txt --tabla    > $S/a5_programa1_error_lexico.txt
$PY src/analizar_todo.py pruebas/final_error_sintactico.txt --tabla > $S/a5_programa2_error_sintactico.txt
{ $PY src/consultar_tabla.py Sino '$'; $PY src/consultar_tabla.py Sino SINO; $PY src/consultar_tabla.py Factor ID; \
  $PY src/consultar_tabla.py Si ENTONCES; $PY src/consultar_tabla.py Programa SINO; } > $S/a5_consultar_tabla.txt
$PY src/pruebas_cruzadas.py                                    > $S/a5_pruebas_cruzadas.txt
echo "Listo: salidas guardadas en la carpeta salidas/ (a3_*, a4_* y a5_*)"
