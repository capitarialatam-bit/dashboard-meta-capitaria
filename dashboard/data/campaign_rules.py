"""
Reglas para clasificar campañas por el código que llevan en el nombre
(ej. "P001E-WE001" → país Perú, código de tipo "WE").
Punto único de verdad: cualquier exclusión por tipo de campaña (eventos
presenciales, webinars, etc.) debe usar estas funciones en vez de
redefinir el criterio en cada módulo.
"""
import re

_WEBINAR_RE = re.compile(r"-WE\d+")


def es_evento_presencial(nombre: str) -> bool:
    return "-EP" in str(nombre).upper()


def es_webinar(nombre: str) -> bool:
    return bool(_WEBINAR_RE.search(str(nombre).upper()))


def excluir_de_gasto_total(nombre: str) -> bool:
    """Campañas que no deben sumarse al KPI de Importe gastado (pero sí seguir
    apareciendo en la tabla de detalle)."""
    return es_evento_presencial(nombre) or es_webinar(nombre)
