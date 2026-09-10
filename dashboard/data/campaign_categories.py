"""
Diccionario centralizado código de campaña → categoría de contenido, y
utilidades para extraer ese código desde el nombre real de la campaña en
Meta Ads (que puede traer texto adicional, ej. "C029L-MC005 | Bonifaz | Leads").
"""
import re

CAMPAIGN_CATEGORIES = {
    # CHILE
    "C004L-MC001": "Aprende a desafiar los mercados",
    "C029L-MC005": "MasterClass Cap1 Bonifaz",
    "C059L-MC006": "Repetición - Mercados en momentos de crisis",
    "C008L-WK001": "Weekly",
    "C007L-EB001": "Ebook ABC Trading",
    "C057L-EX007": "Cupon Reembolso 30%",
    "C022L-EB003": "Ebook primeros pasos en las inversiones",
    "C034L-IN004": "Informe El Mundial Se Opera",
    "C036L-IN005": "Informe SpaceX",
    "C040L-IN006": "Proyecciones 2026 2°",
    "C045L-IN007": "Informe ETF",
    "C056L-IN009": "Proyecciones Dólar - Bonifaz",
    "C048L-IN008": "Informe Anthropic",
    "C010L-TF001": "Miedo a invertir",
    "C013L-MF002": "Invertir acompañado",
    "C038L-BD004": "Branding - 3 Ventajas de Capitaria",
    "C055L-BD007": "Nota Forbes Chile",
    "C054L-BD006": "Brand - 20 años Capitaria Latam",
    "C058L-EX008": "F1 Segunda etapa",
    "C043L-EP007": "Evento presencial con Roberto Bonifaz",

    # MÉXICO
    "M028X-MC002": "MasterClass Cap1 Bonifaz",
    "M012X-EB002": "Ebook ABC Trading",
    "M029X-MC003": "Aprende a desafiar los mercados Masterclass Bonifaz",
    "M027X-BD001": "Branding",
    "M031X-IN005": "Informe El Mundial Se Opera",
    "M009X-EB001": "Ebook Primeros Pasos",
    "M013X-WK001": "Weekly",
    "M032X-IN006": "Informe SpaceX",
    "M008X-WE003": "Webinar Mercados y Mundiales",
    "M036X-IN008": "Informe ETF Semiconductores e IA",
    "M041X-MC005": "Repetición - Mercados en momentos de crisis",
    "M038X-IN009": "Informe dolar peso mexico",
    "M040X-EX003": "Cupon Reembolso 30%",
    "M042X-WE006": "Webinar de Roberto Bonifaz",

    # PERÚ
    "P022E-MC003": "Aprende a desafiar los mercados",
    "P002E-EB001": "Ebook ABC Trading",
    "P004E-EB002": "Ebook Primeros Pasos",
    "P003E-WK001": "Weekly",
    "P001E-WE001": "Webinar (Bau Display)",
    "P026E-IN004": "Proyecciones S2 2026",
    "P019E-MC002": "MasterClass Cap1 Bonifaz",
    "P028E-TF003": "Gratificaciones PE",
    "P029E-IN005": "Informe ETF",
    "P030E-IN006": "Informe Anthropic",
    "P033E-MC005": "Repetición - Mercados en momentos de crisis",

    # URUGUAY
    "U020Y-MC003": "MasterClass Cap1 Bonifaz",
    "U001Y-EP001": "Evento Presencial",
    "U002Y-WK001": "Weekly",
    "U007Y-EB002": "Ebook ABC Trading",
    "U003Y-EB001": "Ebook Primeros Pasos",
    "U022Y-IN002": "Informe El Mundial Se Opera",
    "U024Y-BD001": "Branding - 3 Ventajas de Capitaria",
    "U025Y-IN004": "Proyecciones S2 2026",
    "U026Y-IN005": "Informe ETF Semiconductores e IA",
    "U028Y-EX003": "Cupon Reembolso 30%",
    "U029Y-MC005": "Repetición - Mercados en momentos de crisis",
}

SIN_CATEGORIZAR = "Sin categorizar"

# Código de campaña: [Letra][dígitos][Letra país]-[2 letras][dígitos], ej. "C029L-MC005".
# No se ancla al inicio del string ni depende de la cantidad exacta de dígitos,
# porque el nombre real en Meta suele traer texto adicional alrededor del código
# (ej. "C029L-MC005 | Bonifaz | Leads | Meta").
_CODIGO_RE = re.compile(r'([A-Z]\d+[A-Z]-[A-Z]{2}\d+)')


def extraer_codigo_campania(nombre: str) -> str:
    """Extrae el código de campaña (ej. 'C029L-MC005') desde el nombre completo."""
    m = _CODIGO_RE.search(str(nombre).upper())
    return m.group(1) if m else ""


def categoria_de_campania(nombre: str) -> str:
    """Categoría por código exacto. Si el código no está en el diccionario
    (campaña nueva/todavía no mapeada), devuelve 'Sin categorizar' — nunca
    se oculta la campaña ni se inventa una categoría por coincidencia parcial."""
    codigo = extraer_codigo_campania(nombre)
    return CAMPAIGN_CATEGORIES.get(codigo, SIN_CATEGORIZAR)
