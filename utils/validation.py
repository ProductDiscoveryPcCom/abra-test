"""
Validation & Sanitization Module
Funciones para validar y sanitizar datos de entrada
Previene XSS, inyección, y maneja valores nulos/cero
"""

import re
import html
from typing import Any, List, Dict, Optional, Union
from numbers import Number


# ============================================================================
# SANITIZACIÓN DE STRINGS (Prevención XSS)
# ============================================================================

def sanitize_html(text: Any) -> str:
    """
    Sanitiza texto para uso seguro en HTML
    Escapa caracteres especiales que podrían ser usados para XSS
    
    Args:
        text: Cualquier valor a sanitizar
        
    Returns:
        String sanitizado seguro para HTML
    """
    if text is None:
        return ""
    
    # Convertir a string si no lo es
    text_str = str(text)
    
    # Escapar caracteres HTML
    return html.escape(text_str, quote=True)


def sanitize_for_query(text: Any) -> str:
    """
    Sanitiza texto para uso en queries de API
    Remueve caracteres potencialmente peligrosos
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        String seguro para queries
    """
    if text is None:
        return ""
    
    text_str = str(text).strip()
    
    # Remover caracteres de control y no imprimibles
    text_str = ''.join(char for char in text_str if char.isprintable())
    
    # Limitar longitud
    text_str = text_str[:500]
    
    # Remover caracteres que podrían causar problemas en URLs
    # Mantener letras, números, espacios, guiones y algunos caracteres comunes
    text_str = re.sub(r'[^\w\s\-.,áéíóúñüÁÉÍÓÚÑÜ]', '', text_str, flags=re.UNICODE)
    
    return text_str.strip()


def sanitize_filename(filename: Any) -> str:
    """
    Sanitiza un nombre de archivo
    
    Args:
        filename: Nombre de archivo a sanitizar
        
    Returns:
        Nombre de archivo seguro
    """
    if filename is None:
        return "export"
    
    filename_str = str(filename).strip()
    
    # Remover caracteres peligrosos para nombres de archivo
    filename_str = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename_str)
    
    # Limitar longitud
    filename_str = filename_str[:100]
    
    # Asegurar que no está vacío
    if not filename_str:
        filename_str = "export"
    
    return filename_str


# ============================================================================
# VALIDACIÓN Y COERCIÓN DE NÚMEROS
# ============================================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Convierte valor a float de forma segura
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla
        
    Returns:
        Float válido
    """
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        # Manejar NaN e infinito
        if isinstance(value, float) and (value != value or value == float('inf') or value == float('-inf')):
            return default
        return float(value)
    
    if isinstance(value, str):
        # Manejar "Breakout" y otros strings especiales
        value_lower = value.lower().strip()
        if value_lower == "breakout":
            return 5000.0
        
        # Intentar extraer número
        try:
            # Remover caracteres no numéricos excepto punto y signo
            cleaned = re.sub(r'[^\d.\-+]', '', value)
            if cleaned:
                return float(cleaned)
        except (ValueError, TypeError):
            pass
    
    return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    Convierte valor a int de forma segura
    
    Args:
        value: Valor a convertir
        default: Valor por defecto si la conversión falla
        
    Returns:
        Int válido
    """
    float_val = safe_float(value, float(default))
    return int(float_val)


def safe_percentage(value: Any, default: float = 0.0) -> float:
    """
    Convierte valor a porcentaje de forma segura
    Maneja strings como "+500%", "Breakout", etc.
    
    Returns:
        Float representando porcentaje
    """
    if value is None:
        return default
    
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower == "breakout":
            return 5000.0
        
        # Extraer número de strings como "+500%"
        match = re.search(r'([+-]?\d+(?:\.\d+)?)', value)
        if match:
            return float(match.group(1))
    
    return safe_float(value, default)


# ============================================================================
# OPERACIONES MATEMÁTICAS SEGURAS (División por cero)
# ============================================================================

def safe_divide(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    """
    División segura que evita división por cero
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor por defecto si división es imposible
        
    Returns:
        Resultado de la división o valor por defecto
    """
    num = safe_float(numerator, 0.0)
    den = safe_float(denominator, 0.0)
    
    if den == 0:
        return default
    
    result = num / den
    
    # Verificar que el resultado es un número válido
    if result != result or result == float('inf') or result == float('-inf'):
        return default
    
    return result


def safe_percentage_change(current: Any, previous: Any, default: float = 0.0) -> float:
    """
    Calcula cambio porcentual de forma segura
    
    Returns:
        Cambio porcentual o valor por defecto
    """
    curr = safe_float(current, 0.0)
    prev = safe_float(previous, 0.0)
    
    if prev == 0:
        if curr > 0:
            return 100.0  # Crecimiento desde 0
        return default
    
    return ((curr - prev) / prev) * 100


def safe_average(values: List[Any], default: float = 0.0) -> float:
    """
    Calcula promedio de forma segura
    
    Args:
        values: Lista de valores
        default: Valor por defecto si no hay valores válidos
        
    Returns:
        Promedio o valor por defecto
    """
    if not values:
        return default
    
    valid_values = [safe_float(v, None) for v in values]
    valid_values = [v for v in valid_values if v is not None]
    
    if not valid_values:
        return default
    
    return sum(valid_values) / len(valid_values)


def clamp(value: Any, min_val: float, max_val: float, default: float = 0.0) -> float:
    """
    Limita un valor a un rango
    
    Args:
        value: Valor a limitar
        min_val: Valor mínimo
        max_val: Valor máximo
        default: Valor por defecto
        
    Returns:
        Valor limitado al rango
    """
    val = safe_float(value, default)
    return max(min_val, min(max_val, val))


# ============================================================================
# VALIDACIÓN DE LISTAS Y DICCIONARIOS
# ============================================================================

def safe_list(value: Any, default: List = None) -> List:
    """
    Asegura que el valor es una lista
    
    Args:
        value: Valor a validar
        default: Lista por defecto
        
    Returns:
        Lista válida
    """
    if default is None:
        default = []
    
    if value is None:
        return default
    
    if isinstance(value, list):
        return value
    
    if isinstance(value, (tuple, set)):
        return list(value)
    
    return default


def safe_dict(value: Any, default: Dict = None) -> Dict:
    """
    Asegura que el valor es un diccionario
    
    Args:
        value: Valor a validar
        default: Diccionario por defecto
        
    Returns:
        Diccionario válido
    """
    if default is None:
        default = {}
    
    if value is None:
        return default
    
    if isinstance(value, dict):
        return value
    
    return default


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Obtiene valor de objeto o diccionario de forma segura
    
    Args:
        obj: Objeto o diccionario
        key: Clave a buscar
        default: Valor por defecto
        
    Returns:
        Valor encontrado o valor por defecto
    """
    if obj is None:
        return default
    
    # Intentar como diccionario
    if isinstance(obj, dict):
        return obj.get(key, default)
    
    # Intentar como atributo
    if hasattr(obj, key):
        val = getattr(obj, key, default)
        return val if val is not None else default
    
    return default


def safe_get_nested(obj: Any, *keys, default: Any = None) -> Any:
    """
    Obtiene valor anidado de forma segura
    
    Ejemplo:
        safe_get_nested(data, "interest_over_time", "timeline_data", default=[])
    
    Args:
        obj: Objeto o diccionario
        *keys: Claves anidadas
        default: Valor por defecto
        
    Returns:
        Valor encontrado o valor por defecto
    """
    current = obj
    
    for key in keys:
        current = safe_get(current, key, None)
        if current is None:
            return default
    
    return current if current is not None else default


def safe_first(lst: Any, default: Any = None) -> Any:
    """
    Obtiene primer elemento de una lista de forma segura
    
    Args:
        lst: Lista
        default: Valor por defecto
        
    Returns:
        Primer elemento o valor por defecto
    """
    if not lst or not isinstance(lst, (list, tuple)):
        return default
    
    return lst[0] if lst else default


def safe_last(lst: Any, default: Any = None) -> Any:
    """
    Obtiene último elemento de una lista de forma segura
    
    Args:
        lst: Lista
        default: Valor por defecto
        
    Returns:
        Último elemento o valor por defecto
    """
    if not lst or not isinstance(lst, (list, tuple)):
        return default
    
    return lst[-1] if lst else default


# ============================================================================
# VALIDACIÓN DE DATOS DE TRENDS
# ============================================================================

def validate_timeline_data(timeline_data: Any) -> List[Dict]:
    """
    Valida y normaliza datos de timeline de Google Trends
    
    Args:
        timeline_data: Datos del timeline
        
    Returns:
        Lista de puntos de datos validados
    """
    if not timeline_data or not isinstance(timeline_data, list):
        return []
    
    validated = []
    
    for point in timeline_data:
        if not isinstance(point, dict):
            continue
        
        # Debe tener date y values
        if "date" not in point:
            continue
        
        values = point.get("values", [])
        if not values or not isinstance(values, list):
            continue
        
        # Extraer valor
        first_value = values[0] if values else {}
        extracted_value = safe_float(
            first_value.get("extracted_value", 0) if isinstance(first_value, dict) else 0,
            0.0
        )
        
        validated.append({
            "date": str(point["date"]),
            "value": extracted_value,
            "values": values
        })
    
    return validated


def extract_trend_values(timeline_data: Any) -> List[float]:
    """
    Extrae solo los valores numéricos de un timeline
    
    Args:
        timeline_data: Datos del timeline
        
    Returns:
        Lista de valores float
    """
    validated = validate_timeline_data(timeline_data)
    return [point["value"] for point in validated]


def validate_related_queries(queries: Any) -> List[Dict]:
    """
    Valida y normaliza queries relacionadas
    
    Args:
        queries: Lista de queries
        
    Returns:
        Lista de queries validadas
    """
    if not queries or not isinstance(queries, list):
        return []
    
    validated = []
    
    for q in queries:
        if not isinstance(q, dict):
            continue
        
        query_text = sanitize_html(q.get("query", ""))
        if not query_text:
            continue
        
        validated.append({
            "query": query_text,
            "value": sanitize_html(str(q.get("value", ""))),
            "extracted_value": safe_percentage(q.get("extracted_value", 0), 0),
            "link": sanitize_html(q.get("link", ""))
        })
    
    return validated


# ============================================================================
# VALIDACIÓN DE COLORES
# ============================================================================

def validate_hex_color(color: Any, default: str = "#7C3AED") -> str:
    """
    Valida que un color sea un código hexadecimal válido
    
    Args:
        color: Color a validar
        default: Color por defecto
        
    Returns:
        Color hexadecimal válido
    """
    if not color or not isinstance(color, str):
        return default
    
    # Limpiar
    color = color.strip()
    
    # Validar formato
    if re.match(r'^#[0-9A-Fa-f]{6}$', color):
        return color
    
    if re.match(r'^#[0-9A-Fa-f]{3}$', color):
        # Expandir formato corto #RGB a #RRGGBB
        return '#' + ''.join(c*2 for c in color[1:])
    
    return default


def hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """
    Convierte color hexadecimal a RGBA
    
    Args:
        hex_color: Color en formato #RRGGBB
        alpha: Transparencia (0-1)
        
    Returns:
        String RGBA
    """
    color = validate_hex_color(hex_color)
    
    try:
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        alpha = clamp(alpha, 0, 1, 1.0)
        return f"rgba({r}, {g}, {b}, {alpha})"
    except (ValueError, IndexError):
        return f"rgba(124, 58, 237, {alpha})"


# ============================================================================
# VALIDACIÓN DE URLs
# ============================================================================

def validate_url(url: Any, allowed_protocols: List[str] = None) -> Optional[str]:
    """
    Valida una URL
    
    Args:
        url: URL a validar
        allowed_protocols: Protocolos permitidos
        
    Returns:
        URL válida o None
    """
    if allowed_protocols is None:
        allowed_protocols = ['http', 'https']
    
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Validar protocolo
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        if parsed.scheme not in allowed_protocols:
            return None
        
        if not parsed.netloc:
            return None
        
        return url
    except Exception:
        return None


# ============================================================================
# CONSTANTES DE VALIDACIÓN
# ============================================================================

MAX_KEYWORD_LENGTH = 200
MAX_RESULTS_LIMIT = 100
MIN_TIMELINE_POINTS = 3
DEFAULT_TIMEOUT = 30
