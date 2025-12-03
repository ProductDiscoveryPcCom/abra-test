"""
YouTube Module
Obtiene datos de videos, canales y métricas de YouTube via API oficial v3

API: YouTube Data API v3
Docs: https://developers.google.com/youtube/v3
"""

import streamlit as st
import requests
import html
import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time


@dataclass
class YouTubeVideo:
    """Video de YouTube normalizado"""
    video_id: str
    title: str
    channel: str
    channel_id: str = ""
    views: int = 0
    likes: int = 0
    comments: int = 0
    published: str = ""
    published_date: Optional[datetime] = None
    duration: str = ""
    thumbnail: str = ""
    description: str = ""
    link: str = ""

    @property
    def views_formatted(self) -> str:
        """Formatea vistas de forma legible"""
        if self.views >= 1_000_000:
            return f"{self.views / 1_000_000:.1f}M"
        elif self.views >= 1_000:
            return f"{self.views / 1_000:.1f}K"
        return str(self.views)

    @property
    def engagement_rate(self) -> float:
        """Calcula tasa de engagement"""
        if self.views > 0:
            return ((self.likes + self.comments) / self.views) * 100
        return 0.0


@dataclass
class YouTubeMetrics:
    """Métricas agregadas de búsqueda en YouTube"""
    keyword: str
    total_videos: int = 0
    total_views: int = 0
    avg_views: int = 0
    max_views: int = 0
    recent_videos_30d: int = 0
    recent_videos_7d: int = 0
    top_channels: List[str] = field(default_factory=list)
    has_reviews: bool = False
    has_unboxings: bool = False
    has_comparisons: bool = False
    content_score: int = 0  # 0-100
    api_error: str = ""  # Para debug


class YouTubeModule:
    """Módulo para buscar en YouTube via API oficial v3"""

    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(self, api_key: str):
        """
        Inicializa el módulo de YouTube

        Args:
            api_key: API key de Google Cloud (YouTube Data API v3)

        Raises:
            ValueError: Si la API key está vacía o tiene formato inválido
        """
        if not api_key:
            raise ValueError("YouTube API key es requerida")

        # Validar formato básico (las keys de Google empiezan con AIza)
        if not api_key.startswith("AIza"):
            print(f"[YouTube] Advertencia: API key no tiene formato típico de Google (AIza...)")

        self.api_key = api_key
        self._cache: Dict[str, Any] = {}
        self._last_error: str = ""
        self._is_valid: Optional[bool] = None  # Se verificará en primera llamada

    def search_videos(
        self,
        query: str,
        max_results: int = 20,
        order: str = "relevance",
        region: str = "ES",
        language: str = "es",
        published_after: Optional[datetime] = None
    ) -> List[YouTubeVideo]:
        """
        Busca videos en YouTube

        Args:
            query: Término de búsqueda
            max_results: Máximo de resultados (1-50)
            order: Ordenar por (relevance, date, rating, viewCount)
            region: Código de país ISO
            language: Código de idioma ISO
            published_after: Filtrar videos después de esta fecha

        Returns:
            Lista de videos (vacía si hay error)
        """
        cache_key = f"search_{query}_{order}_{region}_{max_results}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            # Paso 1: Buscar videos (obtiene IDs y snippets básicos)
            video_ids, snippets = self._search_video_ids(
                query=query,
                max_results=min(max_results, 50),
                order=order,
                region=region,
                language=language,
                published_after=published_after
            )

            if not video_ids:
                # Log para debug
                if self._last_error:
                    print(f"[YouTube] No videos found. Last error: {self._last_error}")
                return []

            # Paso 2: Obtener estadísticas de los videos
            stats = self._get_video_statistics(video_ids)

            # Paso 3: Combinar datos
            videos = self._combine_data(video_ids, snippets, stats)

            self._cache[cache_key] = videos
            return videos

        except requests.exceptions.Timeout:
            self._last_error = "Timeout: YouTube API no respondió a tiempo"
            return []
        except requests.exceptions.ConnectionError:
            self._last_error = "Error de conexión con YouTube API"
            return []
        except Exception as e:
            self._last_error = str(e)
            return []

    def search_brand(
        self,
        brand: str,
        geo: str = "ES"
    ) -> Dict[str, List[YouTubeVideo]]:
        """
        Búsqueda completa de una marca con diferentes tipos de contenido

        Args:
            brand: Nombre de la marca/producto
            geo: País

        Returns:
            Dict con videos por tipo (vacío si hay error)
        """
        results = {
            "reviews": [],
            "unboxings": [],
            "comparisons": [],
            "general": []
        }

        try:
            # Búsqueda general (por vistas)
            results["general"] = self._safe_search(
                query=brand,
                max_results=10,
                order="viewCount",
                region=geo
            )

            # Reviews (por relevancia)
            results["reviews"] = self._safe_search(
                query=f"{brand} review",
                max_results=10,
                order="relevance",
                region=geo
            )

            # Unboxings (más recientes)
            results["unboxings"] = self._safe_search(
                query=f"{brand} unboxing",
                max_results=5,
                order="date",
                region=geo
            )

            # Comparativas
            results["comparisons"] = self._safe_search(
                query=f"{brand} vs",
                max_results=5,
                order="viewCount",
                region=geo
            )

        except Exception as e:
            self._last_error = f"Error en búsqueda de marca: {str(e)}"

        return results

    def get_recent_videos(
        self,
        query: str,
        days: int = 30,
        geo: str = "ES"
    ) -> List[YouTubeVideo]:
        """
        Obtiene videos recientes

        Args:
            query: Término de búsqueda
            days: Últimos N días
            geo: País

        Returns:
            Lista de videos recientes
        """
        try:
            published_after = datetime.utcnow() - timedelta(days=days)
            return self.search_videos(
                query=query,
                max_results=20,
                order="date",
                region=geo,
                published_after=published_after
            )
        except Exception:
            return []

    def calculate_metrics(
        self,
        brand: str,
        videos_by_type: Dict[str, List[YouTubeVideo]]
    ) -> YouTubeMetrics:
        """
        Calcula métricas agregadas de YouTube

        Args:
            brand: Nombre de la marca
            videos_by_type: Dict de videos por tipo

        Returns:
            Métricas calculadas (con valores por defecto si hay error)
        """
        try:
            # Recopilar todos los videos únicos
            all_videos = []
            for video_list in videos_by_type.values():
                if video_list:  # Verificar que no sea None
                    all_videos.extend(video_list)

            # Deduplicar por ID
            seen_ids = set()
            unique_videos = []
            for v in all_videos:
                if v and v.video_id and v.video_id not in seen_ids:
                    seen_ids.add(v.video_id)
                    unique_videos.append(v)

            if not unique_videos:
                return YouTubeMetrics(keyword=brand, api_error=self._last_error)

            # Calcular métricas
            views = [v.views for v in unique_videos if v.views > 0]
            total_views = sum(views) if views else 0
            avg_views = total_views // len(views) if views else 0
            max_views = max(views) if views else 0

            # Contar videos recientes
            now = datetime.utcnow()
            recent_30d = 0
            recent_7d = 0

            for v in unique_videos:
                if v.published_date:
                    days_ago = (now - v.published_date).days
                    if days_ago <= 30:
                        recent_30d += 1
                    if days_ago <= 7:
                        recent_7d += 1

            # Top canales
            from collections import Counter
            channels = Counter(v.channel for v in unique_videos if v.channel)
            top_channels = [ch for ch, _ in channels.most_common(5)]

            # Verificar tipos de contenido
            has_reviews = len(videos_by_type.get("reviews") or []) > 0
            has_unboxings = len(videos_by_type.get("unboxings") or []) > 0
            has_comparisons = len(videos_by_type.get("comparisons") or []) > 0

            # Calcular content score
            content_score = self._calculate_content_score(
                total_videos=len(unique_videos),
                total_views=total_views,
                recent_30d=recent_30d,
                has_reviews=has_reviews,
                has_unboxings=has_unboxings
            )

            return YouTubeMetrics(
                keyword=brand,
                total_videos=len(unique_videos),
                total_views=total_views,
                avg_views=avg_views,
                max_views=max_views,
                recent_videos_30d=recent_30d,
                recent_videos_7d=recent_7d,
                top_channels=top_channels,
                has_reviews=has_reviews,
                has_unboxings=has_unboxings,
                has_comparisons=has_comparisons,
                content_score=content_score
            )

        except Exception as e:
            return YouTubeMetrics(keyword=brand, api_error=str(e))

    def _safe_search(self, **kwargs) -> List[YouTubeVideo]:
        """Wrapper seguro para search_videos"""
        try:
            return self.search_videos(**kwargs)
        except Exception:
            return []

    def _search_video_ids(
        self,
        query: str,
        max_results: int,
        order: str,
        region: str,
        language: str,
        published_after: Optional[datetime]
    ) -> Tuple[List[str], Dict[str, dict]]:
        """
        Busca videos y devuelve IDs + snippets

        Returns:
            Tuple de (lista de IDs, dict de snippets por ID)
        """
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "order": order,
            "regionCode": region,
            "relevanceLanguage": language,
            "safeSearch": "moderate",
            "key": self.api_key
        }

        if published_after:
            params["publishedAfter"] = published_after.strftime("%Y-%m-%dT%H:%M:%SZ")

        response = requests.get(self.SEARCH_URL, params=params, timeout=10)

        if response.status_code == 403:
            error_data = response.json().get("error", {})
            error_reason = error_data.get("errors", [{}])[0].get("reason", "unknown")
            if error_reason == "quotaExceeded":
                self._last_error = "Cuota de YouTube API excedida. Intenta mañana."
            elif error_reason == "accessNotConfigured":
                self._last_error = "YouTube Data API v3 no está habilitada en tu proyecto de Google Cloud."
            else:
                self._last_error = f"Acceso denegado: {error_reason}"
            return [], {}

        if response.status_code == 400:
            error_data = response.json().get("error", {})
            self._last_error = f"Solicitud inválida: {error_data.get('message', 'Unknown')}"
            return [], {}

        if response.status_code != 200:
            self._last_error = f"YouTube API error: {response.status_code} - {response.text[:200]}"
            return [], {}

        data = response.json()

        if "error" in data:
            self._last_error = data["error"].get("message", "Unknown API error")
            return [], {}

        items = data.get("items", [])
        video_ids = []
        snippets = {}

        for item in items:
            try:
                video_id = item.get("id", {}).get("videoId")
                if video_id:
                    video_ids.append(video_id)
                    snippets[video_id] = item.get("snippet", {})
            except Exception:
                continue

        return video_ids, snippets

    def _get_video_statistics(self, video_ids: List[str]) -> Dict[str, dict]:
        """
        Obtiene estadísticas de videos (vistas, likes, etc.)

        Args:
            video_ids: Lista de IDs de videos

        Returns:
            Dict de estadísticas por ID
        """
        if not video_ids:
            return {}

        # La API permite hasta 50 IDs por llamada
        params = {
            "part": "statistics,contentDetails",
            "id": ",".join(video_ids[:50]),
            "key": self.api_key
        }

        try:
            response = requests.get(self.VIDEOS_URL, params=params, timeout=10)

            if response.status_code != 200:
                return {}

            data = response.json()
            stats = {}

            for item in data.get("items", []):
                video_id = item.get("id")
                if video_id:
                    stats[video_id] = {
                        "statistics": item.get("statistics", {}),
                        "contentDetails": item.get("contentDetails", {})
                    }

            return stats

        except Exception:
            return {}

    def _combine_data(
        self,
        video_ids: List[str],
        snippets: Dict[str, dict],
        stats: Dict[str, dict]
    ) -> List[YouTubeVideo]:
        """Combina snippets y estadísticas en objetos YouTubeVideo"""
        videos = []

        for video_id in video_ids:
            try:
                snippet = snippets.get(video_id, {})
                stat = stats.get(video_id, {})
                statistics = stat.get("statistics", {})
                content_details = stat.get("contentDetails", {})

                # Parsear fecha
                published_str = snippet.get("publishedAt", "")
                published_date = self._parse_iso_date(published_str)
                published_display = self._format_relative_date(published_date) if published_date else ""

                # Parsear duración
                duration = self._parse_duration(content_details.get("duration", ""))

                # Thumbnail (preferir alta calidad)
                thumbnails = snippet.get("thumbnails", {})
                thumbnail = (
                    thumbnails.get("high", {}).get("url") or
                    thumbnails.get("medium", {}).get("url") or
                    thumbnails.get("default", {}).get("url") or
                    ""
                )

                video = YouTubeVideo(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    channel=snippet.get("channelTitle", ""),
                    channel_id=snippet.get("channelId", ""),
                    views=self._safe_int(statistics.get("viewCount", 0)),
                    likes=self._safe_int(statistics.get("likeCount", 0)),
                    comments=self._safe_int(statistics.get("commentCount", 0)),
                    published=published_display,
                    published_date=published_date,
                    duration=duration,
                    thumbnail=thumbnail,
                    description=snippet.get("description", "")[:200],
                    link=f"https://www.youtube.com/watch?v={video_id}"
                )
                videos.append(video)

            except Exception:
                continue

        return videos

    def _parse_iso_date(self, date_str: str) -> Optional[datetime]:
        """Parsea fecha ISO 8601"""
        if not date_str:
            return None
        try:
            # Formato: 2024-01-15T10:30:00Z
            return datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None

    def _format_relative_date(self, dt: datetime) -> str:
        """Formatea fecha como texto relativo"""
        if not dt:
            return ""

        now = datetime.utcnow()
        diff = now - dt
        days = diff.days

        if days == 0:
            hours = diff.seconds // 3600
            if hours == 0:
                return "Hace unos minutos"
            elif hours == 1:
                return "Hace 1 hora"
            else:
                return f"Hace {hours} horas"
        elif days == 1:
            return "Hace 1 día"
        elif days < 7:
            return f"Hace {days} días"
        elif days < 30:
            weeks = days // 7
            return f"Hace {weeks} semana{'s' if weeks > 1 else ''}"
        elif days < 365:
            months = days // 30
            return f"Hace {months} mes{'es' if months > 1 else ''}"
        else:
            years = days // 365
            return f"Hace {years} año{'s' if years > 1 else ''}"

    def _parse_duration(self, duration: str) -> str:
        """Parsea duración ISO 8601 (PT1H2M3S) a formato legible"""
        if not duration:
            return ""

        try:
            # Ejemplo: PT1H2M3S, PT10M30S, PT45S
            match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
            if not match:
                return ""

            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)

            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        except Exception:
            return ""

    def _safe_int(self, value: Any) -> int:
        """Convierte a int de forma segura"""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0

    def _calculate_content_score(
        self,
        total_videos: int,
        total_views: int,
        recent_30d: int,
        has_reviews: bool,
        has_unboxings: bool
    ) -> int:
        """Calcula score de contenido 0-100"""
        score = 0

        # Videos totales (0-25 pts)
        if total_videos >= 50:
            score += 25
        elif total_videos >= 20:
            score += 20
        elif total_videos >= 10:
            score += 15
        elif total_videos >= 5:
            score += 10
        elif total_videos > 0:
            score += 5

        # Vistas totales (0-30 pts)
        if total_views >= 10_000_000:
            score += 30
        elif total_views >= 1_000_000:
            score += 25
        elif total_views >= 100_000:
            score += 20
        elif total_views >= 10_000:
            score += 15
        elif total_views >= 1_000:
            score += 10
        elif total_views > 0:
            score += 5

        # Videos recientes (0-25 pts)
        if recent_30d >= 10:
            score += 25
        elif recent_30d >= 5:
            score += 20
        elif recent_30d >= 3:
            score += 15
        elif recent_30d >= 1:
            score += 10

        # Tipo de contenido (0-20 pts)
        if has_reviews:
            score += 10
        if has_unboxings:
            score += 10

        return min(100, score)

    def get_last_error(self) -> str:
        """Devuelve el último error para debug"""
        return self._last_error


def check_youtube_config() -> Dict[str, bool]:
    """Verifica si YouTube está configurado"""
    has_key = bool(st.secrets.get("YOUTUBE_API_KEY"))
    has_serpapi = bool(st.secrets.get("SERPAPI_KEY"))  # Fallback

    return {
        "has_key": has_key,
        "has_fallback": has_serpapi,
        "configured": has_key or has_serpapi
    }


def get_youtube_module() -> Optional[YouTubeModule]:
    """Factory para obtener módulo configurado"""
    # Preferir API oficial de YouTube
    youtube_key = st.secrets.get("YOUTUBE_API_KEY")

    if youtube_key:
        return YouTubeModule(api_key=youtube_key)

    # No hay configuración
    return None

