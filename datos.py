# -*- coding: utf-8 -*-
"""
datos.py — Solo datos: las 5 skills del proyecto.

El grafo arranca VACÍO de personas: el usuario las registra desde la
interfaz. Todo vive en memoria — al reiniciar el servidor, se parte
de cero otra vez (no hay base de datos, y es a propósito: las
estructuras de datos en memoria SON el almacenamiento del proyecto).
"""

from grafo import Grafo, Nodo


# (id, nombre, descripcion corta)
SKILLS = [
    ("programacion", "Programación",
     "Escribir código: lógica, algoritmos, depuración."),
    ("matematica", "Matemática",
     "Álgebra, cálculo y razonamiento formal."),
    ("analisis_datos", "Análisis de datos",
     "Interpretar datos, estadística y hojas de cálculo."),
    ("comunicacion", "Comunicación",
     "Exponer, redactar y explicar ideas con claridad."),
    ("liderazgo", "Liderazgo",
     "Organizar al equipo, repartir tareas y dar seguimiento."),
]

IDS_SKILLS = [s[0] for s in SKILLS]


def construir_grafo():
    """
    Arma el grafo inicial: SOLO los 5 nodos skill, sin personas.
    Devuelve (grafo, contador_de_personas) — el contador genera los
    ids únicos p1, p2, ... conforme el usuario registra gente.
    """
    g = Grafo()
    for id_skill, nombre, _descripcion in SKILLS:
        g.agregar_nodo(Nodo(id_skill, nombre, "skill"))
    return g, 0
