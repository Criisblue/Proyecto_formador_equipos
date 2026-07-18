# -*- coding: utf-8 -*-
"""
estructuras.py — Estructuras de datos LINEALES implementadas desde cero.

Aquí viven la Pila y la Cola (con nodos enlazados, no con listas de
Python), más un ordenamiento por inserción y una búsqueda lineal
escritos a mano. El resto del proyecto las usa con propósito real:

    Pila  -> historial de acciones (botón Deshacer).
    Cola  -> fila de espera al formar parejas y recorrido BFS del grafo.
    Ordenamiento por inserción -> ordenar la lista de personas.
    Búsqueda lineal            -> buscar personas por nombre.
"""


class _NodoEnlazado:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None  # referencia al siguiente eslabón (o None)


class Pila:

    def __init__(self):
        self.tope = None      # referencia al eslabón de arriba
        self.tamano = 0

    def esta_vacia(self):
        """O(1). True si la pila no tiene elementos."""
        return self.tope is None

    def apilar(self, valor):  
        nuevo = _NodoEnlazado(valor)
        nuevo.siguiente = self.tope  # el nuevo apunta al viejo tope
        self.tope = nuevo            # y pasa a ser el tope
        self.tamano += 1

    def desapilar(self):
        if self.esta_vacia():
            raise IndexError("La pila está vacía")
        eslabon = self.tope
        self.tope = eslabon.siguiente  # el de abajo pasa a ser el tope
        self.tamano -= 1
        return eslabon.valor

    def ver_tope(self):
        return None if self.esta_vacia() else self.tope.valor


class Cola:

    def __init__(self):
        self.frente = None
        self.final = None
        self.tamano = 0

    def esta_vacia(self):
        return self.frente is None

    def encolar(self, valor):
        nuevo = _NodoEnlazado(valor)
        if self.esta_vacia():
            self.frente = nuevo   # cola vacía: es a la vez frente y final
        else:
            self.final.siguiente = nuevo  # el viejo final apunta al nuevo
        self.final = nuevo
        self.tamano += 1

    def desencolar(self):
        if self.esta_vacia():
            raise IndexError("La cola está vacía")
        eslabon = self.frente
        self.frente = eslabon.siguiente
        if self.frente is None:   # se vació: 'final' también debe soltarse
            self.final = None
        self.tamano -= 1
        return eslabon.valor


def ordenamiento_insercion(lista, clave, descendente=False):
    resultado = list(lista)  # copia para no tocar la original
    for i in range(1, len(resultado)):
        actual = resultado[i]
        valor_actual = clave(actual)
        j = i - 1
        # Desplaza a la derecha todos los elementos que deban ir después
        # del actual (mayores si es ascendente, menores si descendente).
        while j >= 0:
            valor_j = clave(resultado[j])
            debe_moverse = (valor_j > valor_actual) if not descendente \
                else (valor_j < valor_actual)
            if not debe_moverse:
                break
            resultado[j + 1] = resultado[j]
            j -= 1
        resultado[j + 1] = actual  # inserta en el hueco que quedó
    return resultado


def busqueda_lineal(lista, texto, clave):
    texto = texto.strip().lower()
    encontrados = []
    for elemento in lista:
        if texto in clave(elemento).lower():
            encontrados.append(elemento)
    return encontrados
