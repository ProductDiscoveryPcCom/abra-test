"""
Google Trends Module
Obtiene datos de tendencias usando SerpAPI

APIs utilizadas:
- Interest over Time: engine=google_trends, data_type=TIMESERIES
- Interest by Region: engine=google_trends, data_type=GEO_MAP_0 (single) / GEO_MAP (compare)
- Trending Now: engine=google_trends_trending_now
- Autocomplete: engine=google_trends_autocomplete
- News: engine=google_trends_news
"""

import requests
from typing import Optional, List
from datetime import datetime, timedelta
import streamlit as st
import re


class GoogleTrendsModule:
    """Módulo para obtener datos de Google Trends via SerpAPI"""

    BASE_URL = "https://serpapi.com/search.json"

    # Mapeo de países a códigos geo
    COUNTRIES = {
        "España": "ES",
        "Portugal": "PT",
        "Francia": "FR",
        "Italia": "IT",
        "Alemania": "DE",
        "Global": ""
    }

    # Períodos de tiempo disponibles
    TIME_RANGES = {
        "Última hora": "now 1-H",
        "Últimas 4 horas": "now 4-H",
        "Último día": "now 1-d",
        "Última semana": "now 7-d",
        "Último mes": "today 1-m",
        "Últimos 3 meses": "today 3-m",
        "Último año": "today 12-m",
        "Últimos 5 años": "today 5-y"
    }

    # Categorías principales para hardware/tech
    CATEGORIES = {
        "Todas": 0,
        "Electrónica de consumo": 78,
        "Informática y electrónica": 5,
        "Compras": 18,
        "Internet y telecomunicaciones": 13
    }

    # Palabras que indican que una marca podría confundirse con otra cosa
    AMBIGUOUS_TERMS = [
        "attack", "shark", "wolf", "dragon", "tiger", "eagle", "bear",
        "hunter", "killer", "ninja", "warrior", "storm", "thunder",
        "fire", "ice", "shadow", "dark", "light", "black", "red"
    ]

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _should_use_exact_match(self, keyword: str) -> bool:
        """
        Determina si debemos usar búsqueda exacta para evitar contaminación.

        Returns:
            True si el keyword contiene términos ambiguos
        """
        keyword_lower = keyword.lower()
        words = keyword_lower.split()

        # Si alguna palabra es un término ambiguo común
        for word in words:
            if word in self.AMBIGUOUS_TERMS:
                return True

        # Si tiene 2+ palabras y podría confundirse
        if len(words) >= 2:
            # Verificar si parece un nombre de marca (mezcla de palabras comunes)
            common_words = ["the", "a", "an", "of", "and", "or", "for", "to", "in", "on"]
            non_common = [w for w in words if w not in common_words]
            if len(non_common) >= 2:
                return True

        return False

    def _prepare_query(self, keyword: str, force_exact: bool = False) -> str:
        """
        Prepara la query para búsqueda, añadiendo comillas si es necesario.

        Args:
            keyword: Término de búsqueda
            force_exact: Forzar búsqueda exacta

        Returns:
            Query preparada
        """
        # Si ya tiene comillas, dejarlo como está
        if keyword.startswith('"') and keyword.endswith('"'):
            return keyword

        # Si debe ser exacta
        if force_exact or self._should_use_exact_match(keyword):
            return f'"{keyword}"'

        return keyword

    def get_interest_over_time(
        self,
        keyword: str,
        geo: str = "ES",
        timeframe: str = "today 12-m",
        category: int = 0,
        exact_match: bool = None
    ) -> dict:
        """
        Obtiene el interés a lo largo del tiempo para una keyword
        Usa: engine=google_trends, data_type=TIMESERIES

        Args:
            keyword: Término de búsqueda
            geo: Código de país
            timeframe: Período de tiempo
            category: ID de categoría (0=todas, 5=informática, 78=electrónica)
            exact_match: Forzar búsqueda exacta (None=auto-detectar)

        Returns:
            dict con 'timeline_data', 'averages' y metadata
        """
        # Preparar query (auto-detectar si necesita comillas)
        use_exact = exact_match if exact_match is not None else self._should_use_exact_match(keyword)
        query = self._prepare_query(keyword, force_exact=use_exact)

        # Si no se especifica categoría y parece tech/gaming, usar electrónica
        if category == 0 and self._looks_like_tech_brand(keyword):
            category = 5  # Informática y electrónica

        params = {
            "engine": "google_trends",
            "q": query,
            "data_type": "TIMESERIES",
            "geo": geo,
            "date": timeframe,
            "cat": category,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "timeline_data": data.get("interest_over_time", {}).get("timeline_data", []),
                "averages": data.get("interest_over_time", {}).get("averages", []),
                "keyword": keyword,
                "query_used": query,
                "exact_match": use_exact,
                "category": category,
                "geo": geo,
                "timeframe": timeframe
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "keyword": keyword
            }

    def _looks_like_tech_brand(self, keyword: str) -> bool:
        """
        Detecta si el keyword parece ser una marca de tecnología/gaming.

        Returns:
            True si parece una marca tech
        """
        keyword_lower = keyword.lower()

        # Indicadores de marcas tech/gaming
        tech_indicators = [
            # Sufijos comunes
            "tech", "gaming", "pc", "pro", "max", "ultra", "mini",
            "rgb", "wireless", "bluetooth", "usb", "hdmi",
            # Categorías de producto
            "mouse", "keyboard", "headset", "monitor", "laptop",
            "tablet", "phone", "watch", "speaker", "earbuds",
            "gpu", "cpu", "ram", "ssd", "nvme",
            # Marcas conocidas (para contexto)
            "beelink", "minisforum", "geekom", "trigkey", "acemagic",
            "attack shark", "redragon", "razer", "logitech", "corsair",
            "hyperx", "steelseries", "roccat", "glorious", "ducky"
        ]

        for indicator in tech_indicators:
            if indicator in keyword_lower:
                return True

        return False

    def get_interest_by_region(
        self,
        keyword: str,
        geo: str = "",
        timeframe: str = "today 12-m"
    ) -> dict:
        """
        Obtiene el interés por región geográfica para UNA consulta
        Usa: engine=google_trends, data_type=GEO_MAP_0

        Returns:
            dict con 'interest_by_region' array
        """
        params = {
            "engine": "google_trends",
            "q": keyword,
            "data_type": "GEO_MAP_0",
            "geo": geo,
            "date": timeframe,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "interest_by_region": data.get("interest_by_region", []),
                "keyword": keyword,
                "geo": geo
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_compared_breakdown(
        self,
        keywords: List[str],
        geo: str = "",
        timeframe: str = "today 12-m"
    ) -> dict:
        """
        Obtiene comparativa de interés por región para MÚLTIPLES consultas
        Usa: engine=google_trends, data_type=GEO_MAP

        Args:
            keywords: Lista de keywords a comparar (ej: ["nvidia", "amd"])
        """
        # Formatear keywords como "keyword1,keyword2"
        q = ",".join(keywords)

        params = {
            "engine": "google_trends",
            "q": q,
            "data_type": "GEO_MAP",
            "geo": geo,
            "date": timeframe,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "compared_breakdown_by_region": data.get("compared_breakdown_by_region", []),
                "keywords": keywords,
                "geo": geo
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_multi_country_data(
        self,
        keyword: str,
        countries: list = None,
        timeframe: str = "today 12-m"
    ) -> dict:
        """
        Obtiene datos de tendencia para múltiples países

        Args:
            countries: Lista de códigos de país (ES, PT, FR, IT, DE)
        """
        if countries is None:
            countries = ["ES", "PT", "FR", "IT", "DE"]

        results = {}

        for country in countries:
            data = self.get_interest_over_time(
                keyword=keyword,
                geo=country,
                timeframe=timeframe
            )
            results[country] = data

        return {
            "success": True,
            "countries": results,
            "keyword": keyword
        }

    def get_trending_now(
        self,
        geo: str = "ES",
        hours: int = 24,
        category_id: int = None,
        only_active: bool = True
    ) -> dict:
        """
        Obtiene las búsquedas de moda del momento
        Usa: engine=google_trends_trending_now

        Args:
            geo: Código de país (obligatorio)
            hours: Rango temporal en horas
            category_id: Filtrar por categoría
            only_active: Solo tendencias activas

        Returns:
            dict con 'trending_searches' array incluyendo:
            - query, timestamp, is_active, search_volume
            - increase_percentage, categories, serpapi_link
        """
        params = {
            "engine": "google_trends_trending_now",
            "geo": geo,
            "hours": hours,
            "api_key": self.api_key
        }

        if category_id:
            params["category_id"] = category_id

        if only_active:
            params["only_active"] = "true"

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "trending_searches": data.get("trending_searches", []),
                "geo": geo
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_autocomplete(
        self,
        keyword: str
    ) -> dict:
        """
        Obtiene sugerencias de autocompletado de Google Trends
        Usa: engine=google_trends_autocomplete

        Returns:
            dict con sugerencias incluyendo:
            - q (texto sugerido), title, type (topic/search term), links
        """
        params = {
            "engine": "google_trends_autocomplete",
            "q": keyword,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "suggestions": data.get("suggestions", []),
                "keyword": keyword
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "suggestions": []
            }

    def get_news(
        self,
        keyword: str,
        geo: str = "ES"
    ) -> dict:
        """
        Obtiene noticias asociadas a un término de tendencia
        Usa: engine=google_trends_news

        Returns:
            dict con noticias incluyendo:
            - title, link, source, date, thumbnail
        """
        params = {
            "engine": "google_trends_news",
            "q": keyword,
            "geo": geo,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "news": data.get("news_results", []),
                "keyword": keyword,
                "geo": geo
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "news": []
            }

    # Alias para mantener compatibilidad
    def get_trending_searches(self, geo: str = "ES") -> dict:
        """Alias de get_trending_now para compatibilidad"""
        result = self.get_trending_now(geo=geo)
        result["trending"] = result.get("trending_searches", [])
        return result


def calculate_growth_rate(timeline_data: list) -> dict:
    """
    Calcula la tasa de crecimiento de una serie temporal

    Args:
        timeline_data: Datos del timeline de Google Trends

    Returns:
        Dict con current_value, avg_value, growth_rate, peak_value
    """
    if not timeline_data:
        return {
            "current_value": 0,
            "avg_value": 0,
            "growth_rate": 0,
            "peak_value": 0
        }

    # Extraer valores
    values = []
    for point in timeline_data:
        if "values" in point and len(point["values"]) > 0:
            val = point["values"][0].get("extracted_value", 0)
            try:
                values.append(float(val) if val else 0)
            except (ValueError, TypeError):
                values.append(0)

    if not values:
        return {
            "current_value": 0,
            "avg_value": 0,
            "growth_rate": 0,
            "peak_value": 0
        }

    current_value = values[-1] if values else 0
    avg_value = sum(values) / len(values) if values else 0
    peak_value = max(values) if values else 0

    # Calcular crecimiento (últimos 3 puntos vs anteriores)
    if len(values) >= 6:
        recent = sum(values[-3:]) / 3
        previous = sum(values[:-3]) / max(1, len(values) - 3)
        if previous > 0:
            growth_rate = ((recent - previous) / previous) * 100
        else:
            growth_rate = 100 if recent > 0 else 0
    else:
        growth_rate = 0

    return {
        "current_value": round(current_value, 1),
        "avg_value": round(avg_value, 1),
        "growth_rate": round(growth_rate, 1),
        "peak_value": round(peak_value, 1)
    }


def calculate_seasonality(timeline_data: list) -> dict:
    """
    Calcula el patrón de estacionalidad

    Args:
        timeline_data: Datos del timeline de Google Trends

    Returns:
        Dict con is_seasonal, seasonality_score, peak_month, low_month, monthly_pattern
    """
    if not timeline_data or len(timeline_data) < 12:
        return {
            "is_seasonal": False,
            "seasonality_score": 0,
            "peak_month": None,
            "low_month": None,
            "monthly_pattern": {},
            "explanation": "Datos insuficientes para análisis estacional"
        }

    from datetime import datetime
    import re

    # Agrupar valores por mes
    monthly_values = {}

    for point in timeline_data:
        date_str = point.get("date", "")
        if not date_str:
            continue

        # Limpiar rangos de fecha
        if " – " in date_str:
            date_str = date_str.split(" – ")[0]
        if " - " in date_str:
            date_str = date_str.split(" - ")[0]
        date_str = date_str.strip()

        # Intentar extraer mes
        month = None

        # Intentar múltiples formatos
        formats_to_try = [
            "%b %d, %Y",      # Nov 3, 2024
            "%B %d, %Y",      # November 3, 2024
            "%b %Y",          # Nov 2024
            "%B %Y",          # November 2024
            "%Y-%m-%d",       # 2024-11-03
            "%d/%m/%Y",       # 03/11/2024
            "%d %b %Y",       # 03 Nov 2024
        ]

        for fmt in formats_to_try:
            try:
                dt = datetime.strptime(date_str, fmt)
                month = dt.month
                break
            except ValueError:
                continue

        # Fallback: extraer mes con regex
        if month is None:
            month_map = {
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
                'ene': 1, 'abr': 4, 'ago': 8, 'dic': 12
            }
            match = re.search(r'(\w{3,})\s+\d', date_str.lower())
            if match:
                month_str = match.group(1)[:3]
                month = month_map.get(month_str)

        if month is None:
            continue

        # Extraer valor
        val = 0
        if "values" in point and len(point["values"]) > 0:
            try:
                val = float(point["values"][0].get("extracted_value", 0) or 0)
            except (ValueError, TypeError):
                val = 0

        if month not in monthly_values:
            monthly_values[month] = []
        monthly_values[month].append(val)

    if len(monthly_values) < 6:
        return {
            "is_seasonal": False,
            "seasonality_score": 0,
            "peak_month": None,
            "low_month": None,
            "monthly_pattern": {},
            "explanation": "Datos insuficientes para análisis estacional"
        }

    # Calcular promedio por mes
    monthly_avg = {}
    for month, vals in monthly_values.items():
        monthly_avg[month] = sum(vals) / len(vals) if vals else 0

    if not monthly_avg:
        return {
            "is_seasonal": False,
            "seasonality_score": 0,
            "peak_month": None,
            "low_month": None,
            "monthly_pattern": {},
            "explanation": "No hay datos válidos"
        }

    # Calcular promedio global
    all_values = [v for vals in monthly_values.values() for v in vals]
    global_avg = sum(all_values) / len(all_values) if all_values else 1

    # Calcular desviación de cada mes respecto al promedio
    monthly_pattern = {}
    for month, avg in monthly_avg.items():
        if global_avg > 0:
            deviation = ((avg - global_avg) / global_avg) * 100
        else:
            deviation = 0
        monthly_pattern[month] = round(deviation, 1)

    # Determinar pico y valle
    if monthly_pattern:
        peak_month = max(monthly_pattern, key=monthly_pattern.get)
        low_month = min(monthly_pattern, key=monthly_pattern.get)

        # Calcular score de estacionalidad (diferencia entre pico y valle)
        seasonality_score = abs(monthly_pattern[peak_month] - monthly_pattern[low_month])
    else:
        peak_month = None
        low_month = None
        seasonality_score = 0

    # Determinar si es estacional (diferencia significativa)
    is_seasonal = seasonality_score > 30

    # Nombres de meses
    month_names = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    return {
        "is_seasonal": is_seasonal,
        "seasonality_score": round(seasonality_score, 1),
        "peak_month": month_names.get(peak_month, f"Mes {peak_month}") if peak_month else None,
        "peak_month_num": peak_month,
        "peak_value": monthly_pattern.get(peak_month, 0) if peak_month else 0,
        "low_month": month_names.get(low_month, f"Mes {low_month}") if low_month else None,
        "low_month_num": low_month,
        "low_value": monthly_pattern.get(low_month, 0) if low_month else 0,
        "monthly_pattern": monthly_pattern,
        "explanation": "Patrón estacional detectado" if is_seasonal else "Sin patrón estacional claro"
    }


# Añadir métodos al módulo para acceso estático
GoogleTrendsModule.calculate_growth_rate = staticmethod(lambda timeline_data: calculate_growth_rate(timeline_data))
GoogleTrendsModule.calculate_seasonality = staticmethod(lambda timeline_data: calculate_seasonality(timeline_data))


# Función de ayuda para tests
def test_module():
    """Test básico del módulo"""
    api_key = st.secrets.get("SERPAPI_KEY", "")
    if not api_key:
        print("No API key found")
        return

    module = GoogleTrendsModule(api_key)
    result = module.get_interest_over_time("nvidia", geo="ES")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Data points: {len(result['timeline_data'])}")


if __name__ == "__main__":
    test_module()

