"""
Social Score Module
Combina métricas de YouTube y TikTok para un score unificado
"""

import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class SocialMetrics:
    """Métricas combinadas de redes sociales"""
    keyword: str
    
    # YouTube
    youtube_videos: int = 0
    youtube_views: int = 0
    youtube_recent_30d: int = 0
    youtube_content_score: int = 0
    youtube_has_reviews: bool = False
    youtube_has_unboxings: bool = False
    youtube_top_channels: List[str] = field(default_factory=list)
    
    # TikTok
    tiktok_hashtag_views: int = 0
    tiktok_videos: int = 0
    tiktok_viral_score: int = 0
    tiktok_top_creators: List[str] = field(default_factory=list)
    
    # Combinados
    social_score: int = 0
    opportunity_type: str = ""
    opportunity_description: str = ""
    
    @property
    def youtube_views_formatted(self) -> str:
        return _format_number(self.youtube_views)
    
    @property
    def tiktok_views_formatted(self) -> str:
        return _format_number(self.tiktok_hashtag_views)


class SocialScoreCalculator:
    """Calculadora de Social Score combinado"""
    
    # Pesos para el score final
    YOUTUBE_WEIGHT = 0.6
    TIKTOK_WEIGHT = 0.4
    
    def calculate(
        self,
        keyword: str,
        youtube_metrics: Optional[Any] = None,
        tiktok_metrics: Optional[Any] = None,
        trends_score: int = 0
    ) -> SocialMetrics:
        """
        Calcula métricas combinadas de redes sociales
        
        Args:
            keyword: Término buscado
            youtube_metrics: Métricas de YouTube
            tiktok_metrics: Métricas de TikTok
            trends_score: Score de Google Trends (0-100)
            
        Returns:
            Métricas combinadas con análisis de oportunidad
        """
        metrics = SocialMetrics(keyword=keyword)
        
        # Rellenar datos de YouTube
        if youtube_metrics:
            metrics.youtube_videos = youtube_metrics.total_videos
            metrics.youtube_views = youtube_metrics.total_views
            metrics.youtube_recent_30d = youtube_metrics.recent_videos_30d
            metrics.youtube_content_score = youtube_metrics.content_score
            metrics.youtube_has_reviews = youtube_metrics.has_reviews
            metrics.youtube_has_unboxings = youtube_metrics.has_unboxings
            metrics.youtube_top_channels = youtube_metrics.top_channels[:3]
        
        # Rellenar datos de TikTok
        if tiktok_metrics:
            metrics.tiktok_hashtag_views = tiktok_metrics.hashtag_views
            metrics.tiktok_videos = tiktok_metrics.total_videos
            metrics.tiktok_viral_score = tiktok_metrics.viral_score
            metrics.tiktok_top_creators = tiktok_metrics.top_creators[:3]
        
        # Calcular Social Score combinado
        metrics.social_score = self._calculate_combined_score(
            youtube_score=metrics.youtube_content_score,
            tiktok_score=metrics.tiktok_viral_score
        )
        
        # Detectar oportunidad
        opportunity = self._detect_opportunity(
            trends_score=trends_score,
            youtube_score=metrics.youtube_content_score,
            tiktok_score=metrics.tiktok_viral_score,
            youtube_recent=metrics.youtube_recent_30d
        )
        metrics.opportunity_type = opportunity["type"]
        metrics.opportunity_description = opportunity["description"]
        
        return metrics
    
    def _calculate_combined_score(
        self,
        youtube_score: int,
        tiktok_score: int
    ) -> int:
        """Calcula score combinado ponderado"""
        # Si solo tenemos YouTube
        if youtube_score > 0 and tiktok_score == 0:
            return youtube_score
        
        # Si solo tenemos TikTok
        if tiktok_score > 0 and youtube_score == 0:
            return tiktok_score
        
        # Si tenemos ambos
        if youtube_score > 0 and tiktok_score > 0:
            return int(
                youtube_score * self.YOUTUBE_WEIGHT +
                tiktok_score * self.TIKTOK_WEIGHT
            )
        
        return 0
    
    def _detect_opportunity(
        self,
        trends_score: int,
        youtube_score: int,
        tiktok_score: int,
        youtube_recent: int
    ) -> Dict[str, str]:
        """
        Detecta tipo de oportunidad basado en la matriz de datos
        
        Matriz de decisión:
        - Trends bajo + Social alto = Oportunidad temprana
        - Trends alto + Social bajo = Gap de contenido
        - Trends alto + Social alto = Tendencia establecida
        - Trends bajo + Social bajo = Nicho/Sin demanda
        """
        social_avg = (youtube_score + tiktok_score) // 2 if tiktok_score > 0 else youtube_score
        
        # Definir umbrales
        trends_high = trends_score >= 50
        trends_low = trends_score < 30
        social_high = social_avg >= 50
        social_low = social_avg < 30
        
        # Oportunidad temprana: Social alto, Trends bajo
        if social_high and trends_low:
            return {
                "type": "early_opportunity",
                "description": """🚀 **OPORTUNIDAD TEMPRANA**
                
Los creadores ya hablan del producto pero las búsquedas aún no despegaron.
Esto indica que el producto está ganando tracción entre influencers antes de llegar al público general.

**Acción recomendada**: Posicionar el producto AHORA, antes de que suban las búsquedas y la competencia."""
            }
        
        # Gap de contenido: Trends alto, Social bajo
        if trends_high and social_low:
            return {
                "type": "content_gap",
                "description": """📝 **GAP DE CONTENIDO**
                
La gente busca el producto pero hay poco contenido sobre él.
Puede indicar un producto nuevo o un hueco en el mercado de contenido.

**Acción recomendada**: Crear contenido propio (reviews, comparativas) para capturar el interés."""
            }
        
        # Tendencia establecida
        if trends_high and social_high:
            return {
                "type": "established",
                "description": """📈 **TENDENCIA ESTABLECIDA**
                
Alto interés en búsquedas y mucho contenido disponible.
El producto/marca está consolidado en el mercado.

**Acción recomendada**: Competir en precio y disponibilidad. Diferenciarse es difícil."""
            }
        
        # Emergente: Contenido reciente
        if youtube_recent >= 5 and trends_low:
            return {
                "type": "emerging",
                "description": """🌱 **TENDENCIA EMERGENTE**
                
Actividad reciente de creadores con bajo volumen de búsquedas actual.
Puede estar en fase inicial de crecimiento.

**Acción recomendada**: Monitorizar evolución las próximas semanas."""
            }
        
        # Nicho o sin demanda
        if trends_low and social_low:
            return {
                "type": "low_traction",
                "description": """📉 **BAJA TRACCIÓN**
                
Poco interés tanto en búsquedas como en contenido.
Puede ser muy nicho o no tener mercado en España.

**Acción recomendada**: Investigar en otros mercados (US, UK, DE)."""
            }
        
        # Caso por defecto
        return {
            "type": "moderate",
            "description": """📊 **TRACCIÓN MODERADA**
            
Niveles normales de interés y contenido.
Sin señales claras de oportunidad o riesgo.

**Acción recomendada**: Evaluar márgenes y competencia antes de decidir."""
        }


def get_social_score_calculator() -> SocialScoreCalculator:
    """Factory para obtener calculadora"""
    return SocialScoreCalculator()


def _format_number(num: int) -> str:
    """Formatea número de forma legible"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)
