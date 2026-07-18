# -*- coding: utf-8 -*-
"""
servidor.py — El puente web: recibe los clics del navegador, llama al
motor del grafo y responde en JSON. Solo librería estándar.

Rutas:
    GET  /               -> index.html
    GET  /api/estado     -> skills + personas (?buscar= y ?orden=)
    GET  /api/grafo      -> nodos y aristas para dibujar el grafo
    GET  /api/bfs?id=    -> orden de visita del recorrido BFS (ondas)
    POST /api/personas   -> registrar persona {nombre, niveles}
    POST /api/eliminar   -> eliminar persona {id}
    POST /api/vaciar     -> eliminar todas las personas
    POST /api/deshacer   -> revierte la última acción (Pila, LIFO)
    POST /api/equipos    -> forma los equipos de la clase {tamano} (Cola)

Ejecutar:  python servidor.py   y abrir  http://localhost:8000

Todo el estado vive en MEMORIA: el grafo arranca vacío y se pierde al
detener el servidor (decisión de diseño: las estructuras en memoria
son el almacenamiento).
"""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from datos import construir_grafo, SKILLS, IDS_SKILLS
from grafo import Nodo, perfil_de, cobertura, formar_equipos
from estructuras import Pila, ordenamiento_insercion, busqueda_lineal

PUERTO = 8000
MAXIMO = 10 * len(IDS_SKILLS)   # cobertura perfecta: 10 x 5 skills = 50

# Estado del servidor (en memoria): grafo, contador de ids e historial.
GRAFO, CONTADOR = construir_grafo()
HISTORIAL = Pila()


# ---------------------------------------------------------------------------
# Operaciones sobre el grafo (cada una apila cómo deshacerse)
# ---------------------------------------------------------------------------

def persona_a_dict(nodo):
    """Serializa un nodo persona para enviarlo como JSON."""
    niveles = perfil_de(nodo)
    promedio = sum(niveles.values()) / len(niveles) if niveles else 0
    return {"id": nodo.id, "nombre": nodo.nombre,
            "niveles": niveles, "promedio": round(promedio, 1)}


def agregar_persona(nombre, niveles):
    """
    Inserta un nodo persona con sus 5 aristas (peso 1-10).
    Para deshacer: bastará eliminar ese nodo, así que se apila su id.
    """
    global CONTADOR
    CONTADOR += 1
    id_persona = "p{}".format(CONTADOR)
    GRAFO.agregar_nodo(Nodo(id_persona, nombre, "persona"))
    for id_skill in IDS_SKILLS:
        nivel = max(1, min(10, int(niveles.get(id_skill, 1))))
        GRAFO.conectar(id_persona, id_skill, nivel)
    HISTORIAL.apilar(("agregar", {"id": id_persona}))
    return id_persona


def eliminar_persona(id_persona):
    """
    Quita el nodo y sus aristas. Para deshacer: se apilan sus datos
    completos, y así se puede volver a insertar idéntica.
    """
    nodo = GRAFO.nodos[id_persona]
    datos = {"id": nodo.id, "nombre": nodo.nombre, "niveles": perfil_de(nodo)}
    GRAFO.eliminar_nodo(id_persona)
    HISTORIAL.apilar(("eliminar", datos))


def vaciar_personas():
    """Elimina todas las personas; apila la lista completa para deshacer."""
    respaldo = []
    for nodo in GRAFO.personas():
        respaldo.append({"id": nodo.id, "nombre": nodo.nombre,
                         "niveles": perfil_de(nodo)})
        GRAFO.eliminar_nodo(nodo.id)
    HISTORIAL.apilar(("vaciar", respaldo))


def _restaurar(datos):
    """Reinserta una persona con su id y niveles originales."""
    GRAFO.agregar_nodo(Nodo(datos["id"], datos["nombre"], "persona"))
    for id_skill, nivel in datos["niveles"].items():
        GRAFO.conectar(datos["id"], id_skill, nivel)


def deshacer():
    """
    Desapila la última acción (LIFO) y aplica su inversa:
        agregar  -> se elimina la persona agregada
        eliminar -> se restaura la persona eliminada
        vaciar   -> se restauran todas
    """
    if HISTORIAL.esta_vacia():
        return None
    tipo, datos = HISTORIAL.desapilar()
    if tipo == "agregar":
        nodo = GRAFO.nodos.get(datos["id"])
        nombre = nodo.nombre if nodo else "?"
        if nodo:
            GRAFO.eliminar_nodo(datos["id"])
        return "Se deshizo: registrar a {}".format(nombre)
    if tipo == "eliminar":
        _restaurar(datos)
        return "Se deshizo: eliminar a {}".format(datos["nombre"])
    if tipo == "vaciar":
        for persona in datos:
            _restaurar(persona)
        return "Se deshizo: vaciar ({} personas restauradas)".format(len(datos))
    return None


# ---------------------------------------------------------------------------
# Armado de respuestas JSON
# ---------------------------------------------------------------------------

def estado(buscar="", orden="llegada"):
    """
    Lista de personas, aplicando la BÚSQUEDA LINEAL (si hay texto) y
    el ORDENAMIENTO POR INSERCIÓN (según el criterio), de estructuras.py.
    """
    personas = [persona_a_dict(n) for n in GRAFO.personas()]

    if buscar:
        personas = busqueda_lineal(personas, buscar, clave=lambda p: p["nombre"])

    if orden == "nombre":
        personas = ordenamiento_insercion(personas, clave=lambda p: p["nombre"].lower())
    elif orden == "promedio":
        personas = ordenamiento_insercion(personas, clave=lambda p: p["promedio"],
                                          descendente=True)
    # "llegada": orden de inserción, sin tocar.

    return {
        "skills": [{"id": s[0], "nombre": s[1], "descripcion": s[2]} for s in SKILLS],
        "personas": personas,
        "acciones_en_historial": HISTORIAL.tamano,
        "maximo": MAXIMO,
    }


def grafo_para_dibujar():
    """Nodos y aristas en crudo, para que el navegador dibuje el 3D."""
    return {
        "skills": [{"id": s[0], "nombre": s[1]} for s in SKILLS],
        "personas": [{"id": n.id, "nombre": n.nombre} for n in GRAFO.personas()],
        "aristas": [{"persona": n.id, "skill": v.id, "peso": p}
                    for n in GRAFO.personas() for v, p in n.aristas],
    }


def _detalle_json(detalle):
    return {s: {"nivel": d[0], "aporta": d[1]} for s, d in detalle.items()}


def equipos_json(tamano):
    """
    Forma los equipos (Cola FIFO + voraz) y devuelve también la traza
    de decisiones, con los nombres ya resueltos para mostrar en vivo.
    """
    equipos, traza = formar_equipos(GRAFO, IDS_SKILLS, tamano)

    # La traza trae ids; se agregan nombres para pintarla en pantalla.
    for paso in traza:
        if "id" in paso:
            paso["nombre"] = GRAFO.nodos[paso["id"]].nombre
        if "gana" in paso:
            paso["nombre_gana"] = GRAFO.nodos[paso["gana"]].nombre
        for candidato in paso.get("candidatos", []):
            candidato["nombre"] = GRAFO.nodos[candidato["id"]].nombre
        if "miembros" in paso:
            paso["nombres"] = [GRAFO.nodos[m].nombre for m in paso["miembros"]]

    return {"maximo": MAXIMO, "traza": traza, "equipos": [{
        "miembros": [persona_a_dict(m) for m in miembros],
        "cobertura": puntaje,
        "cobertura_pct": round(puntaje * 100 / MAXIMO, 1),
        "detalle": _detalle_json(detalle),
    } for miembros, puntaje, detalle in equipos]}


def bfs_json(id_inicio):
    """Orden de visita del BFS con su nivel (onda), listo para animar."""
    return {"orden": [{
        "id": nodo.id, "nombre": nodo.nombre, "tipo": nodo.tipo,
        "nivel": nivel, "orden": indice + 1,
    } for indice, (nodo, nivel) in enumerate(GRAFO.bfs(id_inicio))]}


# ---------------------------------------------------------------------------
# Servidor HTTP
# ---------------------------------------------------------------------------

class Manejador(BaseHTTPRequestHandler):

    def _json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def _leer_cuerpo(self):
        longitud = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(longitud).decode("utf-8")) if longitud else {}

    def do_GET(self):
        url = urlparse(self.path)
        parametros = parse_qs(url.query)

        if url.path in ("/", "/index.html"):
            ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "index.html")
            try:
                with open(ruta, "rb") as archivo:
                    cuerpo = archivo.read()
            except FileNotFoundError:
                self.send_error(404, "No se encontró index.html")
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        elif url.path == "/api/estado":
            self._json(estado(
                buscar=parametros.get("buscar", [""])[0],
                orden=parametros.get("orden", ["llegada"])[0]))

        elif url.path == "/api/grafo":
            self._json(grafo_para_dibujar())

        elif url.path == "/api/bfs":
            id_inicio = parametros.get("id", [""])[0]
            if id_inicio not in GRAFO.nodos:
                self._json({"error": "Nodo no encontrado."}, 404)
            else:
                self._json(bfs_json(id_inicio))

        else:
            self.send_error(404, "Ruta no encontrada")

    def do_POST(self):
        try:
            if self.path == "/api/personas":
                datos = self._leer_cuerpo()
                nombre = str(datos.get("nombre", "")).strip()
                if not nombre:
                    self._json({"error": "El nombre no puede estar vacío."}, 400)
                    return
                id_nuevo = agregar_persona(nombre, datos.get("niveles", {}))
                self._json({"ok": True, "id": id_nuevo})

            elif self.path == "/api/eliminar":
                id_persona = self._leer_cuerpo().get("id", "")
                if id_persona not in GRAFO.nodos:
                    self._json({"error": "Persona no encontrada."}, 404)
                    return
                eliminar_persona(id_persona)
                self._json({"ok": True})

            elif self.path == "/api/vaciar":
                vaciar_personas()
                self._json({"ok": True})

            elif self.path == "/api/deshacer":
                mensaje = deshacer()
                if mensaje is None:
                    self._json({"error": "No hay acciones para deshacer."}, 400)
                    return
                self._json({"ok": True, "mensaje": mensaje})

            elif self.path == "/api/equipos":
                if len(GRAFO.personas()) < 2:
                    self._json({"error": "Registra al menos 2 personas."}, 400)
                    return
                tamano = max(2, min(5, int(self._leer_cuerpo().get("tamano", 2))))
                self._json(equipos_json(tamano))

            else:
                self.send_error(404, "Ruta no encontrada")
        except (ValueError, json.JSONDecodeError):
            self._json({"error": "JSON inválido."}, 400)

    def log_message(self, formato, *args):
        print("[peticion] " + formato % args)


def main():
    servidor = HTTPServer(("localhost", PUERTO), Manejador)
    print("Formador de Equipos Complementarios")
    print("Grafo inicial: {} skills, 0 personas (se registran en vivo).".format(
        len(SKILLS)))
    print("Servidor listo en http://localhost:{}  (Ctrl+C para detener)".format(PUERTO))
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        servidor.server_close()


if __name__ == "__main__":
    main()
