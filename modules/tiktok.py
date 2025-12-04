"""
TikTok Module
Obtiene datos de hashtags, videos trending y métricas de TikTok

NOTA: Este módulo está preparado para integrar la API de TikTok.
Configurar cuando se tengan las credenciales.
"""

import streamlit as st
import requests
import html
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class TikTokVideo:
    """Video de TikTok normalizado"""
    video_id: str
    description: str
    author: str
    author_followers: int = 0
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    created_time: str = ""
    thumbnail: str = ""
    music_title: str = ""
    hashtags: List[str] = field(default_factory=list)

    @property
    def engagement_rate(self) -> float:
        """Calcula tasa de engagement"""
        if self.views > 0:
            return ((self.likes + self.comments + self.shares) / self.views) * 100
        return 0.0

    @property
    def views_formatted(self) -> str:
        """Formatea vistas de forma legible"""
        if self.views >= 1_000_000:
            return f"{self.views / 1_000_000:.1f}M"
        elif self.views >= 1_000:
            return f"{self.views / 1_000:.1f}K"
        return str(self.views)


@dataclass
class TikTokHashtag:
    """Hashtag de TikTok"""
    name: str
    views: int = 0
    video_count: int = 0

    @property
    def views_formatted(self) -> str:
        if self.views >= 1_000_000_000:
            return f"{self.views / 1_000_000_000:.1f}B"
        elif self.views >= 1_000_000:
            return f"{self.views / 1_000_000:.1f}M"
        elif self.views >= 1_000:
            return f"{self.views / 1_000:.1f}K"
        return str(self.views)


@dataclass
class TikTokMetrics:
    """Métricas agregadas de TikTok"""
    keyword: str
    hashtag_views: int = 0
    total_videos: int = 0
    avg_views: int = 0
    avg_engagement: float = 0.0
    trending_videos: int = 0
    top_creators: List[str] = field(default_factory=list)
    related_hashtags: List[str] = field(default_factory=list)
    viral_score: int = 0  # 0-100


class TikTokModule:
    """
    Módulo para obtener datos de TikTok

    TODO: Implementar cuando se tengan credenciales de API
    Opciones de API:
    - TikTok Research API (requiere aprobación)
    - TikTok for Developers
    - RapidAPI wrappers
    - SerpAPI (si añaden soporte)
    """

    def __init__(self, api_key: str = "", api_secret: str = ""):
        """
        Inicializa el módulo de TikTok

        Args:
            api_key: API Key de TikTok
            api_secret: API Secret
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self._initialized = False

    def search_hashtag(self, hashtag: str) -> Optional[TikTokHashtag]:
        """
        Busca información de un hashtag

        Args:
            hashtag: Nombre del hashtag (sin #)

        Returns:
            Datos del hashtag o None
        """
        # TODO: Implementar cuando se tenga API
        return None

    def search_videos(
        self,
        query: str,
        max_results: int = 20
    ) -> List[TikTokVideo]:
        """
        Busca videos por keyword

        Args:
            query: Término de búsqueda
            max_results: Máximo de resultados

        Returns:
            Lista de videos
        """
        # TODO: Implementar cuando se tenga API
        return []

    def get_trending_videos(
        self,
        keyword: str,
        max_results: int = 10
    ) -> List[TikTokVideo]:
        """
        Obtiene videos trending para un keyword

        Args:
            keyword: Término de búsqueda
            max_results: Máximo de resultados

        Returns:
            Lista de videos trending
        """
        # TODO: Implementar cuando se tenga API
        return []

    def search_brand(self, brand: str) -> Dict[str, Any]:
        """
        Búsqueda completa de una marca

        Args:
            brand: Nombre de la marca

        Returns:
            Dict con hashtags, videos y métricas
        """
        # TODO: Implementar cuando se tenga API
        return {
            "hashtags": [],
            "videos": [],
            "trending": [],
            "metrics": None
        }

    def calculate_metrics(
        self,
        brand: str,
        hashtags: List[TikTokHashtag],
        videos: List[TikTokVideo]
    ) -> TikTokMetrics:
        """
        Calcula métricas agregadas

        Args:
            brand: Nombre de la marca
            hashtags: Lista de hashtags
            videos: Lista de videos

        Returns:
            Métricas calculadas
        """
        if not videos and not hashtags:
            return TikTokMetrics(keyword=brand)

        # Calcular métricas básicas
        total_hashtag_views = sum(h.views for h in hashtags)
        total_views = sum(v.views for v in videos)
        avg_views = total_views // len(videos) if videos else 0

        avg_engagement = 0.0
        if videos:
            engagements = [v.engagement_rate for v in videos]
            avg_engagement = sum(engagements) / len(engagements)

        # Top creators
        from collections import Counter
        creators = Counter(v.author for v in videos if v.author)
        top_creators = [c for c, _ in creators.most_common(5)]

        # Viral score
        viral_score = self._calculate_viral_score(
            hashtag_views=total_hashtag_views,
            video_count=len(videos),
            avg_engagement=avg_engagement
        )

        return TikTokMetrics(
            keyword=brand,
            hashtag_views=total_hashtag_views,
            total_videos=len(videos),
            avg_views=avg_views,
            avg_engagement=avg_engagement,
            trending_videos=len([v for v in videos if v.views > 100000]),
            top_creators=top_creators,
            related_hashtags=[h.name for h in hashtags[:5]],
            viral_score=viral_score
        )

    def _calculate_viral_score(
        self,
        hashtag_views: int,
        video_count: int,
        avg_engagement: float
    ) -> int:
        """Calcula score de viralidad 0-100"""
        score = 0

        # Vistas de hashtag (0-40 pts)
        if hashtag_views >= 1_000_000_000:  # 1B+
            score += 40
        elif hashtag_views >= 100_000_000:  # 100M+
            score += 35
        elif hashtag_views >= 10_000_000:  # 10M+
            score += 25
        elif hashtag_views >= 1_000_000:  # 1M+
            score += 15
        elif hashtag_views > 0:
            score += 5

        # Videos (0-30 pts)
        if video_count >= 100:
            score += 30
        elif video_count >= 50:
            score += 25
        elif video_count >= 20:
            score += 20
        elif video_count >= 10:
            score += 15
        elif video_count > 0:
            score += 5

        # Engagement (0-30 pts)
        if avg_engagement >= 10:
            score += 30
        elif avg_engagement >= 5:
            score += 25
        elif avg_engagement >= 3:
            score += 20
        elif avg_engagement >= 1:
            score += 10

        return min(100, score)


def check_tiktok_config() -> Dict[str, bool]:
    """Verifica si TikTok está configurado"""
    return {
        "has_key": bool(st.secrets.get("TIKTOK_API_KEY")),
        "has_secret": bool(st.secrets.get("TIKTOK_API_SECRET")),
        "configured": False  # Cambiar a True cuando se implemente
    }


def get_tiktok_module() -> Optional[TikTokModule]:
    """Factory para obtener módulo configurado"""
    config = check_tiktok_config()

    if not config["configured"]:
        return None

    return TikTokModule(
        api_key=st.secrets.get("TIKTOK_API_KEY", ""),
        api_secret=st.secrets.get("TIKTOK_API_SECRET", "")
    )

