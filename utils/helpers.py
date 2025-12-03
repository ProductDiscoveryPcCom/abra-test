"""
Shared Helper Functions
Funciones de utilidad compartidas para evitar duplicación de código

Nota: Este módulo reexporta funciones de validation.py para evitar duplicaciones.
"""

from typing import Union

# Importar funciones de validation.py para evitar duplicación
from .validation import (
    sanitize_html,
    safe_get,
    safe_float,
    safe_int,
    safe_divide,
    hex_to_rgba
)


def format_number(num: Union[int, float]) -> str:
    """
    Formatea número de forma legible (K, M, B)

    Args:
        num: Número a formatear

    Returns:
        String formateado (ej: "1.5M", "3.2K", "500")
    """
    if num is None:
        return "0"

    try:
        num = float(num)
    except (ValueError, TypeError):
        return "0"

    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(int(num))


def format_percentage(value: Union[int, float], decimals: int = 1) -> str:
    """
    Formatea un valor como porcentaje

    Args:
        value: Valor numérico
        decimals: Decimales a mostrar

    Returns:
        String formateado con signo y % (ej: "+15.3%", "-2.1%")
    """
    if value is None:
        return "0%"

    try:
        value = float(value)
    except (ValueError, TypeError):
        return "0%"

    return f"{value:+.{decimals}f}%"


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Trunca texto si excede longitud máxima

    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a añadir si se trunca

    Returns:
        Texto truncado o original si no excede
    """
    if text is None:
        return ""

    text = str(text)
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def parse_number(value, default: float = 0.0) -> float:
    """
    Parsea valor a número de forma segura

    Args:
        value: Valor a parsear (puede ser string, int, float)
        default: Valor por defecto si falla

    Returns:
        Valor numérico
    """
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        # Manejar casos especiales
        value_clean = value.strip().lower()
        if value_clean == "breakout":
            return 5000.0

        # Limpiar caracteres no numéricos
        import re
        numbers = re.findall(r'[\d.]+', value)
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass

    return default


def get_growth_indicator(growth: float) -> tuple:
    """
    Obtiene indicadores visuales para crecimiento

    Args:
        growth: Porcentaje de crecimiento

    Returns:
        Tupla (color, icono)
    """
    if growth > 20:
        return ("#10B981", "📈")  # Verde
    elif growth < -10:
        return ("#EF4444", "📉")  # Rojo
    else:
        return ("#6B7280", "➡️")  # Gris


def calculate_percentage_change(current: float, previous: float) -> float:
    """
    Calcula cambio porcentual entre dos valores

    Args:
        current: Valor actual
        previous: Valor anterior

    Returns:
        Cambio porcentual
    """
    if previous == 0:
        return 0.0 if current == 0 else 100.0

    return ((current - previous) / previous) * 100


# Re-exportar para uso conveniente
__all__ = [
    'format_number',
    'format_percentage',
    'truncate_text',
    'parse_number',
    'get_growth_indicator',
    'calculate_percentage_change',
    'sanitize_html',
    'safe_get',
    'safe_float',
    'safe_int',
    'safe_divide',
    'hex_to_rgba'
]

