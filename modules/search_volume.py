"""
Search Volume Estimation Module
Estima volúmenes de búsqueda reales combinando múltiples fuentes

Fuentes utilizadas:
- Google Trends (índice 0-100)
- Google Search Results (número de resultados)
- Factores de categoría y región

Nota: Para volúmenes exactos se recomienda integrar:
- Google Ads API (gratis con cuenta activa)
- DataForSEO API (~$50/mes)
- Keyword Tool API (~$69/mes)
"""

import requests
from typing import Optional, Dict, Tuple
import re


class SearchVolumeEstimator:
    """Estima volúmenes de búsqueda reales basándose en múltiples señales"""
    
    BASE_URL = "https://serpapi.com/search.json"
    
    # Factores de escala por categoría (basados en promedios de industria)
    CATEGORY_MULTIPLIERS = {
        0: 1.0,      # Todas las categorías
        78: 0.8,     # Electrónica de consumo
        5: 1.2,      # Informática y electrónica
        18: 1.5,     # Compras
        13: 1.0,     # Internet y telecomunicaciones
    }
    
    # Factores por país (población relativa de usuarios de internet)
    COUNTRY_MULTIPLIERS = {
        "ES": 0.12,   # España ~47M
        "PT": 0.03,   # Portugal ~10M
        "FR": 0.18,   # Francia ~67M
        "IT": 0.15,   # Italia ~60M
        "DE": 0.22,   # Alemania ~83M
        "US": 1.0,    # USA (base)
        "": 1.0,      # Global
    }
    
    # Rangos de volumen mensual estimado por índice de trends
    # Basado en correlaciones conocidas entre Google Trends y volumen real
    VOLUME_RANGES = {
        # (min_index, max_index): (min_volume, max_volume)
        (0, 10): (100, 1000),
        (10, 25): (1000, 5000),
        (25, 50): (5000, 20000),
        (50, 75): (20000, 100000),
        (75, 90): (100000, 500000),
        (90, 100): (500000, 5000000),
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._cache = {}
    
    def estimate_volume(
        self,
        keyword: str,
        trends_index: int,
        geo: str = "ES",
        category: int = 0,
        use_search_results: bool = True
    ) -> Dict:
        """
        Estima el volumen de búsqueda mensual para un keyword
        
        Args:
            keyword: Término de búsqueda
            trends_index: Índice de Google Trends (0-100)
            geo: Código de país
            category: ID de categoría
            use_search_results: Si debe usar el número de resultados de Google
            
        Returns:
            Dict con volumen estimado, rango y confianza
        """
        # Obtener rango base por índice de trends
        base_min, base_max = self._get_volume_range(trends_index)
        
        # Aplicar multiplicadores
        cat_mult = self.CATEGORY_MULTIPLIERS.get(category, 1.0)
        country_mult = self.COUNTRY_MULTIPLIERS.get(geo, 0.1)
        
        # Calcular estimación base
        estimated_min = int(base_min * cat_mult * country_mult)
        estimated_max = int(base_max * cat_mult * country_mult)
        
        # Refinar con número de resultados de Google si está habilitado
        search_results_count = None
        refinement_factor = 1.0
        
        if use_search_results:
            search_results_count = self._get_search_results_count(keyword, geo)
            if search_results_count:
                refinement_factor = self._calculate_refinement_factor(search_results_count)
                estimated_min = int(estimated_min * refinement_factor)
                estimated_max = int(estimated_max * refinement_factor)
        
        # Calcular punto medio y confianza
        estimated_volume = (estimated_min + estimated_max) // 2
        confidence = self._calculate_confidence(trends_index, search_results_count)
        
        return {
            "estimated_volume": estimated_volume,
            "volume_min": estimated_min,
            "volume_max": estimated_max,
            "trends_index": trends_index,
            "confidence": confidence,
            "confidence_label": self._get_confidence_label(confidence),
            "search_results": search_results_count,
            "factors": {
                "category_multiplier": cat_mult,
                "country_multiplier": country_mult,
                "refinement_factor": refinement_factor
            },
            "formatted": self._format_volume(estimated_volume),
            "formatted_range": f"{self._format_volume(estimated_min)} - {self._format_volume(estimated_max)}"
        }
    
    def estimate_timeline_volumes(
        self,
        keyword: str,
        timeline_data: list,
        geo: str = "ES",
        category: int = 0
    ) -> list:
        """
        Estima volúmenes para toda la línea temporal de Google Trends
        
        Returns:
            Lista de dicts con fecha y volumen estimado
        """
        if not timeline_data:
            return []
        
        # Obtener volumen base actual
        current_index = 0
        if timeline_data:
            last_point = timeline_data[-1]
            if "values" in last_point and len(last_point["values"]) > 0:
                current_index = last_point["values"][0].get("extracted_value", 50)
        
        base_estimate = self.estimate_volume(
            keyword, 
            current_index, 
            geo, 
            category,
            use_search_results=True
        )
        
        # El índice 100 corresponde al máximo del periodo
        # Escalar todos los puntos proporcionalmente
        max_index = max(
            point["values"][0].get("extracted_value", 0) 
            for point in timeline_data 
            if "values" in point and len(point["values"]) > 0
        ) or 100
        
        # Factor de escala: volumen estimado actual / índice actual
        if current_index > 0:
            scale_factor = base_estimate["estimated_volume"] / current_index
        else:
            scale_factor = base_estimate["estimated_volume"] / 50  # Fallback
        
        result = []
        for point in timeline_data:
            if "values" in point and len(point["values"]) > 0:
                index = point["values"][0].get("extracted_value", 0)
                estimated = int(index * scale_factor)
                
                result.append({
                    "date": point.get("date", ""),
                    "trends_index": index,
                    "estimated_volume": estimated,
                    "formatted": self._format_volume(estimated)
                })
        
        return result
    
    def _get_volume_range(self, index: int) -> Tuple[int, int]:
        """Obtiene el rango de volumen para un índice dado"""
        for (min_idx, max_idx), (min_vol, max_vol) in self.VOLUME_RANGES.items():
            if min_idx <= index < max_idx:
                # Interpolar dentro del rango
                ratio = (index - min_idx) / (max_idx - min_idx) if max_idx > min_idx else 0.5
                interpolated_min = int(min_vol + (max_vol - min_vol) * ratio * 0.5)
                interpolated_max = int(min_vol + (max_vol - min_vol) * (0.5 + ratio * 0.5))
                return interpolated_min, interpolated_max
        
        # Fallback para index = 100
        return 500000, 5000000
    
    def _get_search_results_count(self, keyword: str, geo: str = "ES") -> Optional[int]:
        """Obtiene el número de resultados de Google para un keyword"""
        cache_key = f"{keyword}_{geo}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Mapeo de geo a dominio y hl
        geo_config = {
            "ES": {"google_domain": "google.es", "hl": "es", "gl": "es"},
            "PT": {"google_domain": "google.pt", "hl": "pt", "gl": "pt"},
            "FR": {"google_domain": "google.fr", "hl": "fr", "gl": "fr"},
            "IT": {"google_domain": "google.it", "hl": "it", "gl": "it"},
            "DE": {"google_domain": "google.de", "hl": "de", "gl": "de"},
        }
        
        config = geo_config.get(geo, {"google_domain": "google.com", "hl": "en", "gl": "us"})
        
        params = {
            "engine": "google",
            "q": keyword,
            "num": 1,  # Solo necesitamos el conteo
            "api_key": self.api_key,
            **config
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Extraer número de resultados
            search_info = data.get("search_information", {})
            total_results = search_info.get("total_results", 0)
            
            self._cache[cache_key] = total_results
            return total_results
            
        except Exception:
            return None
    
    def _calculate_refinement_factor(self, search_results: int) -> float:
        """Calcula factor de refinamiento basado en resultados de búsqueda"""
        # Escala logarítmica: más resultados = mayor interés
        if search_results <= 0:
            return 1.0
        
        import math
        # Normalizar: 1M resultados = factor 1.0
        log_results = math.log10(search_results + 1)
        log_baseline = math.log10(1_000_000)
        
        factor = log_results / log_baseline
        
        # Limitar entre 0.5 y 2.0
        return max(0.5, min(2.0, factor))
    
    def _calculate_confidence(self, trends_index: int, search_results: Optional[int]) -> float:
        """Calcula nivel de confianza de la estimación (0-1)"""
        base_confidence = 0.4  # Base sin datos adicionales
        
        # Mayor confianza con índice de trends más estable
        if 20 <= trends_index <= 80:
            base_confidence += 0.2
        elif 10 <= trends_index <= 90:
            base_confidence += 0.1
        
        # Mayor confianza si tenemos datos de búsqueda
        if search_results is not None:
            base_confidence += 0.2
            if search_results > 100_000:
                base_confidence += 0.1
        
        return min(0.85, base_confidence)  # Nunca 100% sin datos reales
    
    def _get_confidence_label(self, confidence: float) -> str:
        """Convierte confianza numérica a etiqueta"""
        if confidence >= 0.7:
            return "Alta"
        elif confidence >= 0.5:
            return "Media"
        else:
            return "Baja"
    
    def _format_volume(self, volume: int) -> str:
        """Formatea volumen para mostrar"""
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"{volume / 1_000:.1f}K"
        else:
            return str(volume)


def estimate_from_trends_data(
    api_key: str,
    keyword: str,
    timeline_data: list,
    geo: str = "ES",
    category: int = 0
) -> Dict:
    """
    Función helper para estimar volumen desde datos de Google Trends
    
    Returns:
        Dict con estimación actual y timeline con volúmenes
    """
    estimator = SearchVolumeEstimator(api_key)
    
    # Obtener índice actual
    current_index = 50  # Default
    if timeline_data:
        last_point = timeline_data[-1]
        if "values" in last_point and len(last_point["values"]) > 0:
            current_index = last_point["values"][0].get("extracted_value", 50)
    
    # Estimación actual
    current_estimate = estimator.estimate_volume(keyword, current_index, geo, category)
    
    # Timeline con volúmenes
    volume_timeline = estimator.estimate_timeline_volumes(keyword, timeline_data, geo, category)
    
    return {
        "current": current_estimate,
        "timeline": volume_timeline,
        "keyword": keyword,
        "geo": geo
    }
