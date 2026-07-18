# 🤝 Formador de Equipos Complementarios

Proyecto de estructuras de datos: cada **persona es un nodo de un grafo
bipartito** conectado a 5 skills (programación, matemática, análisis de
datos, comunicación, liderazgo) con aristas ponderadas **1–10**. El
sistema reparte a toda la clase en **equipos de 2 a 5 personas que se
complementan**. Solo librería estándar de Python; interfaz sin
frameworks ni CDNs.

## Cómo ejecutar

```bash
python servidor.py
```

Abrir **http://localhost:8000**. El grafo arranca **vacío**: las
personas se registran en vivo. Todo vive en memoria — al reiniciar el
servidor se parte de cero (decisión de diseño: las estructuras en
memoria son el almacenamiento; una base de datos ocultaría justo lo que
el proyecto demuestra).

## Interfaz: 3 pestañas

1. **Registrar** — alta de personas (nombre + 5 niveles 1–10), lista
   con búsqueda y ordenamiento, eliminar, vaciar y **deshacer**.
2. **Formar equipos** — eliges el tamaño (2 a 5) y el sistema reparte a
   toda la clase (cola FIFO + voraz). Las parejas se muestran con la
   tarjeta de "colapso" (los dos nombres unidos por una línea con su
   puntaje); los equipos grandes, con su desglose de quién aporta qué.
3. **Grafo 3D** — el grafo girando en vivo; los integrantes de cada
   equipo formado se unen con líneas directas de color.

## Estructuras usadas (todas desde cero) y su propósito

| Estructura | Dónde | Para qué |
|---|---|---|
| Grafo bipartito dinámico | `grafo.py` | La libreta de registro: guarda personas, skills y niveles. Insertar/eliminar personas modifica nodos y aristas en ejecución. |
| Pila (LIFO) | `estructuras.py` | El botón Deshacer: cada acción se apila como platos; deshacer levanta el de arriba. |
| Cola (FIFO) | `estructuras.py` | La fila para formar equipos (nadie se salta el turno de fundar) y el recorrido BFS. |
| Ordenamiento por inserción | `estructuras.py` | Ordenar la lista de personas (como ordenar cartas en la mano), O(n²). |
| Búsqueda lineal | `estructuras.py` | El buscador por nombre, O(n). |

## Cómo decide (una sola idea: cobertura)

Por cada skill, el equipo vale lo que su **mejor** integrante; se suman
las 5 skills (máximo 50). Un buen equipo no es el de gente parecida: es
el que entre todos rellena los huecos.

**Repartir la clase**: una **cola FIFO** da el turno de fundar equipo
(justicia por orden de llegada) y un criterio **voraz** recluta, uno a
uno, al que más cobertura aporta al equipo (mérito), hasta llenar el
tamaño elegido. Si las cuentas no dan exactas, el último equipo queda
incompleto. El voraz no garantiza el óptimo global — trade-off elegido
conscientemente: probar todas las particiones posibles es combinatorio.

## El grafo persona–persona (la vista)

Las personas nunca se conectan directamente en el grafo: se relacionan
a través de las skills. Al dibujar los resultados, esos caminos
compartidos se **colapsan** en líneas directas entre compañeros con la
cobertura encima (proyección del bipartito). El bipartito es donde se
*escribe*; esta vista es donde se *ve*.

## BFS (y por qué no hay DFS)

`Grafo.bfs()` recorre todo el grafo por niveles usando la Cola — el
mismo patrón que formar equipos: una fila decide el orden. Cambiando la
cola por una pila se obtiene DFS; se omitió el código porque es
simétrico y la pila ya se demuestra en Deshacer.

## El 3D es solo dibujo

El bloque marcado `SOLO DIBUJO 3D` en `index.html` no toma decisiones:
recibe nodos y aristas ya calculados por Python y los pinta. Cada nodo
tiene coordenadas (x, y, z); rotar es seno y coseno; proyectar a
pantalla es una división por la profundidad.

## Archivos

- `estructuras.py` — Pila, Cola (nodos enlazados), ordenamiento por inserción, búsqueda lineal.
- `grafo.py` — Nodo, Grafo dinámico, BFS, cobertura y formación de equipos.
- `datos.py` — las 5 skills (el grafo arranca sin personas).
- `servidor.py` — API con `http.server` + la pila de deshacer.
- `index.html` — las 3 pestañas (HTML/CSS/JS vanilla).
