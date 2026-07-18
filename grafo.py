# -*- coding: utf-8 -*-
"""
grafo.py — El grafo y la lógica de parejas. Núcleo del proyecto.

GRAFO BIPARTITO, NO DIRIGIDO, PONDERADO y DINÁMICO, desde cero:
  - Dos tipos de nodos: "persona" y "skill".
  - Cada arista conecta una persona con una skill, con peso 1-10
    (el nivel de esa persona en esa skill).
  - Las conexiones son referencias directas entre objetos (punteros):
    cada nodo guarda tuplas (nodo_vecino, peso) en su lista 'aristas'.
  - Es dinámico: se insertan y eliminan personas en ejecución.

La lógica de parejas usa UNA sola idea, la COBERTURA: por cada skill,
la pareja vale lo que su mejor integrante; se suman las 5 (máximo 50).
Buena pareja = la que rellena los huecos de la otra persona.
"""

from estructuras import Cola


class Nodo:
    def __init__(self, id, nombre, tipo):
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.aristas = []

    def __repr__(self):
        return "Nodo({}, tipo={})".format(self.id, self.tipo)


class Grafo:
    def __init__(self):
        self.nodos = {}

    def agregar_nodo(self, nodo):
        """O(1). Registra el nodo en el punto de entrada."""
        if nodo.id in self.nodos:
            raise ValueError("Ya existe un nodo con id '{}'".format(nodo.id))
        self.nodos[nodo.id] = nodo

    def conectar(self, id_a, id_b, peso):
        """
        O(1). Arista bidireccional: cada nodo guarda una referencia
        al otro con el mismo peso (el grafo es no dirigido).
        """
        nodo_a = self.nodos[id_a]
        nodo_b = self.nodos[id_b]
        nodo_a.aristas.append((nodo_b, peso))
        nodo_b.aristas.append((nodo_a, peso))

    def eliminar_nodo(self, id_nodo):
        """
        Quita el nodo y TODAS sus aristas: en cada vecino se borra la
        media arista que apuntaba de vuelta (si no, quedarían
        referencias colgantes). Complejidad: O(grado x grado_vecino).
        """
        nodo = self.nodos.pop(id_nodo)
        for vecino, _peso in nodo.aristas:
            vecino.aristas = [(n, p) for (n, p) in vecino.aristas
                              if n is not nodo]
        return nodo

    def personas(self):
        """O(V). Nodos tipo 'persona' en orden de llegada."""
        return [n for n in self.nodos.values() if n.tipo == "persona"]

    def bfs(self, id_inicio):
        """
        Recorrido en anchura (Breadth-First Search): visita TODO el
        grafo por "ondas" de cercanía. La frontera de exploración es
        una COLA (FIFO): el mismo patrón que formar equipos — una fila
        decide el orden. Con una PILA en su lugar sería DFS.

        Devuelve la lista [(nodo, nivel), ...] en orden de visita,
        donde nivel es la distancia en saltos desde el inicio:
        nivel 0 = el inicio, nivel 1 = sus vecinos directos (onda 1),
        nivel 2 = los vecinos de sus vecinos (onda 2), etc.
        Complejidad: O(V + E).
        """
        inicio = self.nodos[id_inicio]
        niveles = {inicio.id: 0}      # también funciona como "visitados"
        cola = Cola()
        cola.encolar(inicio)
        orden = []

        while not cola.esta_vacia():
            actual = cola.desencolar()        # sale el MÁS ANTIGUO
            orden.append((actual, niveles[actual.id]))
            for vecino, _peso in actual.aristas:
                if vecino.id not in niveles:
                    niveles[vecino.id] = niveles[actual.id] + 1
                    cola.encolar(vecino)
        return orden


# ---------------------------------------------------------------------------
# Lógica de parejas: todo se apoya en una sola función, cobertura()
# ---------------------------------------------------------------------------

def perfil_de(nodo_persona):

    vector = {}
    for vecino, peso in nodo_persona.aristas:
        if vecino.tipo == "skill":
            vector[vecino.id] = peso
    return vector


def cobertura(nodos_personas, ids_skills):
    """
    LA función del proyecto. Por cada skill, el grupo vale lo que su
    MEJOR integrante; se suman las skills. Máximo: 10 x 5 = 50.

    Devuelve (puntaje, detalle) con detalle[id_skill] =
    (mejor_nivel, id_de_quien_lo_aporta).
    Complejidad: O(personas x skills).
    """
    puntaje = 0
    detalle = {}
    for id_skill in ids_skills:
        mejor_nivel = 0
        mejor_persona = None
        for persona in nodos_personas:
            nivel = perfil_de(persona).get(id_skill, 0)
            if nivel > mejor_nivel:
                mejor_nivel = nivel
                mejor_persona = persona.id
        puntaje += mejor_nivel
        detalle[id_skill] = (mejor_nivel, mejor_persona)
    return puntaje, detalle


def formar_equipos(grafo, ids_skills, tamano=2):
    """
    Reparte a TODA la clase en equipos complementarios de 'tamano'
    integrantes (2 a 5).

    Usa una COLA (FIFO) como fila de espera, en orden de llegada:
      1. Todas las personas entran a la fila.
      2. Sale el primero: es la semilla (fundador) del equipo.
      3. De los que siguen libres, se recluta de forma VORAZ al que
         logra la mayor cobertura junto al equipo actual; se repite
         hasta completar el tamaño.
      4. Se vuelve al paso 2 hasta vaciar la fila. El último equipo
         puede quedar incompleto si las cuentas no dan exactas.

    La cola da justicia (turno de fundar por orden de llegada);
    el criterio voraz da mérito (entra quien mejor complementa).
    El voraz no garantiza el óptimo global: es un trade-off elegido
    porque probar todas las particiones posibles es combinatorio.
    Complejidad: O(P² x S).

    Además de decidir, el algoritmo ANOTA cada decisión en una
    "traza" (bitácora): quién fundó, qué candidatos se evaluaron y
    con qué puntaje, y quién entró. La interfaz reproduce esa traza
    paso a paso — así lo que se ve en pantalla es literalmente lo
    que el algoritmo hizo, no una animación aparte.

    Devuelve (equipos, traza) donde:
        equipos = [(miembros, puntaje, detalle), ...]
        traza   = lista de pasos: {"tipo": "funda"|"ronda"|"cierra"|
                  "salta", ...datos de esa decisión...}
    """
    fila = Cola()
    for persona in grafo.personas():
        fila.encolar(persona)

    libres = {p.id for p in grafo.personas()}
    equipos = []
    traza = []

    while not fila.esta_vacia():
        semilla = fila.desencolar()
        if semilla.id not in libres:
            # Salió de la fila pero ya fue reclutado antes: se salta.
            traza.append({"tipo": "salta", "id": semilla.id})
            continue
        libres.discard(semilla.id)
        miembros = [semilla]
        num_equipo = len(equipos) + 1
        traza.append({"tipo": "funda", "id": semilla.id,
                      "equipo": num_equipo})

        # Reclutamiento voraz: entra quien más sube la cobertura.
        while len(miembros) < tamano and libres:
            candidatos = []
            mejor = None
            mejor_puntaje = -1
            for id_libre in libres:
                candidato = grafo.nodos[id_libre]
                puntaje, _ = cobertura(miembros + [candidato], ids_skills)
                candidatos.append({"id": id_libre, "puntaje": puntaje})
                if puntaje > mejor_puntaje:
                    mejor_puntaje = puntaje
                    mejor = candidato
            candidatos.sort(key=lambda c: -c["puntaje"])
            traza.append({"tipo": "ronda", "equipo": num_equipo,
                          "candidatos": candidatos, "gana": mejor.id,
                          "puntaje": mejor_puntaje})
            miembros.append(mejor)
            libres.discard(mejor.id)

        puntaje, detalle = cobertura(miembros, ids_skills)
        traza.append({"tipo": "cierra", "equipo": num_equipo,
                      "miembros": [m.id for m in miembros],
                      "puntaje": puntaje})
        equipos.append((miembros, puntaje, detalle))

    return equipos, traza
