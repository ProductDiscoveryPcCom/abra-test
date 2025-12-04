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
from collections import Counter
import time

# Import patterns module
try:
    from patterns import (
        # Product detection
        extract_products,
        # Buying signals
        analyze_buying_signals,
        get_budget_keywords,
    )
    PATTERNS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: patterns module not available: {e}")
    PATTERNS_AVAILABLE = False


# =============================================================================
# DATACLASSES
# =============================================================================

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
    # Nuevos campos para deep dive
    language: str = ""  # Idioma detectado
    country: str = ""   # País del canal
    sentiment: str = "" # positive/negative/neutral
    sentiment_score: float = 0.0  # -1 a 1

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
class BrandMention:
    """Marca o producto mencionado en videos - DETECTADO DINÁMICAMENTE"""
    name: str
    mention_count: int = 0
    total_views: int = 0
    avg_sentiment: float = 0.0
    video_ids: List[str] = field(default_factory=list)
    context: str = ""  # "competitor", "budget_alternative", "comparison", "accessory"
    is_budget_option: bool = False  # Detectado como alternativa económica


@dataclass
class ProductMention:
    """Producto específico detectado (modelo, número de serie, etc.)"""
    name: str  # Ej: "RTX 4090", "GMKtec NucBox K8", "Minisforum UM790"
    mention_count: int = 0
    total_views: int = 0
    video_ids: List[str] = field(default_factory=list)
    context: str = ""  # "main", "alternative", "comparison"
    first_seen: Optional[datetime] = None  # Para calcular hype


@dataclass
class BuyingIntent:
    """Señales de intención de compra detectadas"""
    total_signals: int = 0
    where_to_buy: int = 0  # "where to buy", "dónde comprar"
    price_mentions: int = 0  # "precio", "price", "cost"
    availability: int = 0  # "available", "in stock", "disponible"
    europe_mentions: int = 0  # "europe", "españa", "amazon.es"
    sample_queries: List[str] = field(default_factory=list)  # Ejemplos encontrados


@dataclass
class HypeMetrics:
    """Métricas de hype del producto"""
    first_video_date: Optional[datetime] = None
    weeks_since_first: int = 0
    total_videos: int = 0
    videos_per_week: float = 0.0
    hype_score: int = 0  # 0-100
    hype_trend: str = ""  # "exploding", "hot", "warm", "cooling", "cold"


@dataclass
class LanguageStats:
    """Estadísticas por idioma - CONECTADO A MERCADOS OBJETIVO"""
    language: str
    language_name: str
    target_market: str = ""  # ES, PT, FR, IT, DE
    video_count: int = 0
    total_views: int = 0
    avg_engagement: float = 0.0
    percentage: float = 0.0
    market_opportunity: str = ""  # "high", "medium", "low", "saturated"


@dataclass
class CountryStats:
    """Estadísticas por país"""
    country_code: str
    country_name: str
    video_count: int = 0
    total_views: int = 0
    top_channels: List[str] = field(default_factory=list)
    percentage: float = 0.0


@dataclass
class SentimentAnalysis:
    """Análisis de sentimiento agregado"""
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    avg_score: float = 0.0
    positive_percentage: float = 0.0
    negative_percentage: float = 0.0
    top_positive_videos: List[str] = field(default_factory=list)
    top_negative_videos: List[str] = field(default_factory=list)


@dataclass
class YouTubeDeepDive:
    """Análisis profundo orientado a PRODUCT DISCOVERY"""
    keyword: str
    total_videos_analyzed: int = 0
    total_views: int = 0
    total_engagement: int = 0
    
    # Por tipo de contenido
    videos_by_type: Dict[str, List[YouTubeVideo]] = field(default_factory=dict)
    
    # NUEVO: Productos detectados dinámicamente (no hardcodeados)
    products_mentioned: List[ProductMention] = field(default_factory=list)
    budget_alternatives: List[ProductMention] = field(default_factory=list)
    
    # NUEVO: Señales de intención de compra
    buying_intent: Optional[BuyingIntent] = None
    
    # NUEVO: Métricas de hype
    hype: Optional[HypeMetrics] = None
    
    # Competidores detectados en comparativas
    competitor_mentions: List[BrandMention] = field(default_factory=list)
    
    # Por idioma (conectado a mercados objetivo)
    languages: List[LanguageStats] = field(default_factory=list)
    
    # Por país
    countries: List[CountryStats] = field(default_factory=list)
    
    # Top channels
    top_channels: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timeline (videos por mes)
    timeline: Dict[str, int] = field(default_factory=dict)
    
    # Métricas calculadas
    avg_views_per_video: int = 0
    avg_engagement_rate: float = 0.0
    growth_trend: str = ""  # "growing", "stable", "declining"
    content_freshness: str = ""  # "very_fresh", "fresh", "aging", "stale"
    
    # NUEVO: Score de oportunidad de producto
    product_opportunity_score: int = 0  # 0-100
    countries: List[CountryStats] = field(default_factory=list)
    
    # Top channels
    top_channels: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timeline (videos por mes)
    timeline: Dict[str, int] = field(default_factory=dict)
    
    # Métricas calculadas
    avg_views_per_video: int = 0
    avg_engagement_rate: float = 0.0
    growth_trend: str = ""  # "growing", "stable", "declining"
    content_freshness: str = ""  # "very_fresh", "fresh", "aging", "stale"


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

    def test_connection(self) -> Tuple[bool, str]:
        """
        Prueba la conexión con la API de YouTube
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        if not self.api_key:
            return False, "API Key no configurada"
        
        try:
            # Hacer una búsqueda mínima para verificar la key
            params = {
                "key": self.api_key,
                "part": "snippet",
                "q": "test",
                "type": "video",
                "maxResults": 1
            }
            
            response = requests.get(
                self.SEARCH_URL,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "items" in data:
                    self._is_valid = True
                    return True, "Conectado (YouTube API v3)"
                return False, "Respuesta inválida"
            elif response.status_code == 400:
                error = response.json().get("error", {})
                reason = error.get("errors", [{}])[0].get("reason", "unknown")
                if reason == "keyInvalid":
                    return False, "API Key inválida"
                return False, f"Error: {reason}"
            elif response.status_code == 403:
                error = response.json().get("error", {})
                reason = error.get("errors", [{}])[0].get("reason", "unknown")
                if reason == "quotaExceeded":
                    # La key es válida pero sin cuota
                    self._is_valid = True
                    return True, "Conectado (cuota agotada)"
                elif reason == "accessNotConfigured":
                    return False, "API no habilitada en GCP"
                return False, f"Acceso denegado: {reason}"
            elif response.status_code == 401:
                return False, "API Key inválida"
            else:
                return False, f"Error HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout de conexión"
        except requests.exceptions.ConnectionError:
            return False, "Error de conexión"
        except Exception as e:
            return False, f"Error: {str(e)[:30]}"

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

    # =========================================================================
    # DEEP DIVE ANALYSIS - PRODUCT DISCOVERY FOCUSED
    # =========================================================================
    
    # Idiomas → Mercados objetivo de PCComponentes
    LANGUAGE_TO_MARKET = {
        "es": {"market": "ES", "name": "España", "priority": 1},
        "pt": {"market": "PT", "name": "Portugal", "priority": 2},
        "fr": {"market": "FR", "name": "Francia", "priority": 3},
        "it": {"market": "IT", "name": "Italia", "priority": 4},
        "de": {"market": "DE", "name": "Alemania", "priority": 5},
        "en": {"market": "GLOBAL", "name": "Global (EN)", "priority": 6},
    }
    
    LANGUAGE_PATTERNS = {
        "es": ["análisis", "prueba", "comparativa", "vale la pena", "español", "españa"],
        "en": ["review", "worth it", "should you buy", "honest review"],
        "pt": ["análise", "teste", "vale a pena", "português", "brasil"],
        "fr": ["test", "avis", "vaut le coup", "français"],
        "de": ["test", "lohnt sich", "deutsch", "kaufen"],
        "it": ["recensione", "vale la pena", "italiano"],
    }
    
    # Señales de ALTERNATIVA ECONÓMICA (fallback si patterns no disponible)
    BUDGET_SIGNALS = [
        "budget", "affordable", "cheap", "cheaper", "barato", "económico",
        "best value", "value for money", "bang for buck", "relación calidad",
        "alternative", "alternativa", "instead of", "en lugar de",
        "vs", "versus", "compared to", "comparado con",
        "killer", "beater", "better than", "mejor que"
    ]

    def detect_language(self, text: str) -> str:
        """Detecta el idioma del texto"""
        if not text:
            return "en"
        
        text_lower = text.lower()
        scores = {}
        
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = sum(1 for p in patterns if p in text_lower)
            if score > 0:
                scores[lang] = score
        
        # Heurísticas de caracteres
        if "ñ" in text_lower or "¿" in text_lower or "¡" in text_lower:
            scores["es"] = scores.get("es", 0) + 3
        if "ç" in text_lower or "ã" in text_lower or "õ" in text_lower:
            scores["pt"] = scores.get("pt", 0) + 3
        if "ü" in text_lower or "ß" in text_lower:
            scores["de"] = scores.get("de", 0) + 3
        if "è" in text_lower or "ù" in text_lower or "ò" in text_lower:
            scores["it"] = scores.get("it", 0) + 2
        
        return max(scores, key=scores.get) if scores else "en"

    def extract_products_dynamic(self, videos: List[YouTubeVideo], main_keyword: str) -> List[ProductMention]:
        """
        Extrae productos DINÁMICAMENTE de los videos usando el módulo patterns.
        Usa detección multinivel: marcas conocidas + patrones estructurales genéricos.
        """
        product_data = {}
        
        for video in videos:
            text = f"{video.title} {video.description}"
            
            if PATTERNS_AVAILABLE:
                # Usar el nuevo sistema de detección multinivel
                detected = extract_products(text, main_keyword=main_keyword, use_structural=True)
                
                for product in detected:
                    name = product.name
                    
                    if name not in product_data:
                        product_data[name] = {
                            "count": 0,
                            "views": 0,
                            "video_ids": [],
                            "first_seen": video.published_date,
                            "category": product.category.value if product.category else "",
                            "confidence": product.confidence,
                            "detection_level": product.detection_level.name
                        }
                    
                    product_data[name]["count"] += 1
                    product_data[name]["views"] += video.views
                    if video.video_id not in product_data[name]["video_ids"]:
                        product_data[name]["video_ids"].append(video.video_id)
                    
                    # Actualizar first_seen si este video es más antiguo
                    if video.published_date and product_data[name]["first_seen"]:
                        if video.published_date < product_data[name]["first_seen"]:
                            product_data[name]["first_seen"] = video.published_date
        
        # Convertir a lista ordenada por confianza y menciones
        products = []
        sorted_products = sorted(
            product_data.items(),
            key=lambda x: (x[1]["confidence"], x[1]["count"]),
            reverse=True
        )
        
        for name, data in sorted_products:
            if data["count"] >= 2:  # Solo productos mencionados 2+ veces
                products.append(ProductMention(
                    name=name,
                    mention_count=data["count"],
                    total_views=data["views"],
                    video_ids=data["video_ids"][:5],
                    first_seen=data["first_seen"],
                    context=data.get("category", "")
                ))
        
        return products[:20]  # Top 20

    def detect_budget_alternatives(self, videos: List[YouTubeVideo]) -> List[ProductMention]:
        """
        Detecta productos mencionados como alternativas económicas.
        """
        budget_products = {}
        
        # Obtener keywords de budget del módulo patterns o usar fallback
        budget_keywords = get_budget_keywords() if PATTERNS_AVAILABLE else self.BUDGET_SIGNALS
        
        for video in videos:
            text = f"{video.title} {video.description}"
            text_lower = text.lower()
            
            # ¿Este video habla de alternativas económicas?
            has_budget_signal = any(signal in text_lower for signal in budget_keywords)
            
            if has_budget_signal and PATTERNS_AVAILABLE:
                # Extraer productos de este video usando el nuevo sistema
                detected = extract_products(text, use_structural=True)
                
                for product in detected:
                    name = product.name
                    
                    if name not in budget_products:
                        budget_products[name] = {
                            "count": 0,
                            "views": 0,
                            "video_ids": []
                        }
                    
                    budget_products[name]["count"] += 1
                    budget_products[name]["views"] += video.views
                    if video.video_id not in budget_products[name]["video_ids"]:
                        budget_products[name]["video_ids"].append(video.video_id)
        
        # Convertir a lista
        products = []
        for name, data in sorted(budget_products.items(), key=lambda x: x[1]["count"], reverse=True):
            products.append(ProductMention(
                name=name,
                mention_count=data["count"],
                total_views=data["views"],
                video_ids=data["video_ids"][:3],
                context="budget_alternative"
            ))
        
        return products[:10]

    def analyze_buying_intent(self, videos: List[YouTubeVideo]) -> BuyingIntent:
        """
        Analiza señales de intención de compra usando el módulo patterns.
        Las señales están definidas por país y tipo en patterns/__init__.py
        """
        intent = BuyingIntent()
        sample_queries = []
        
        if PATTERNS_AVAILABLE:
            # Combinar todos los textos
            all_text = " ".join([f"{v.title} {v.description}" for v in videos])
            
            # Usar la nueva función de análisis
            analysis = analyze_buying_signals(all_text)
            
            intent.total_signals = analysis["total_signals"]
            intent.where_to_buy = analysis["by_type"].get("where_to_buy", 0)
            intent.price_mentions = analysis["by_type"].get("price_check", 0)
            intent.availability = analysis["by_type"].get("availability", 0)
            intent.europe_mentions = (
                analysis["by_type"].get("retailer", 0) + 
                analysis["by_type"].get("shipping", 0)
            )
            
            # Añadir ejemplos de matches
            for match in analysis.get("matches", [])[:5]:
                sample_queries.append(
                    f"[{match['market']}] '{match['phrase']}'"
                )
        else:
            # Fallback a búsqueda simple
            fallback_signals = {
                "where_to_buy": ["where to buy", "dónde comprar", "donde comprar"],
                "price": ["price", "precio", "€"],
                "availability": ["in stock", "disponible", "available"],
                "europe": ["europe", "españa", "amazon.es", "pccomponentes"]
            }
            
            for video in videos:
                text = f"{video.title} {video.description}".lower()
                
                for signal in fallback_signals["where_to_buy"]:
                    if signal in text:
                        intent.where_to_buy += 1
                        intent.total_signals += 1
                        break
                
                for signal in fallback_signals["price"]:
                    if signal in text:
                        intent.price_mentions += 1
                        intent.total_signals += 1
                        break
                
                for signal in fallback_signals["availability"]:
                    if signal in text:
                        intent.availability += 1
                        intent.total_signals += 1
                        break
                
                for signal in fallback_signals["europe"]:
                    if signal in text:
                        intent.europe_mentions += 1
                        intent.total_signals += 1
                        break
        
        intent.sample_queries = sample_queries
        return intent

    def calculate_hype_metrics(self, videos: List[YouTubeVideo]) -> HypeMetrics:
        """
        Calcula el ratio de hype basado en videos / tiempo desde lanzamiento
        """
        hype = HypeMetrics()
        
        # Encontrar el video más antiguo (proxy de fecha de lanzamiento)
        dated_videos = [v for v in videos if v.published_date]
        if not dated_videos:
            return hype
        
        oldest_video = min(dated_videos, key=lambda v: v.published_date)
        hype.first_video_date = oldest_video.published_date
        
        now = datetime.utcnow()
        days_since = (now - hype.first_video_date).days
        hype.weeks_since_first = max(1, days_since // 7)
        hype.total_videos = len(videos)
        
        # Videos por semana
        hype.videos_per_week = hype.total_videos / hype.weeks_since_first
        
        # Calcular hype score (0-100)
        # Más videos/semana = más hype
        # Ajustado: 5+ videos/semana = máximo hype
        if hype.videos_per_week >= 5:
            hype.hype_score = 100
        elif hype.videos_per_week >= 2:
            hype.hype_score = 80
        elif hype.videos_per_week >= 1:
            hype.hype_score = 60
        elif hype.videos_per_week >= 0.5:
            hype.hype_score = 40
        else:
            hype.hype_score = 20
        
        # Ajustar por recencia (videos en últimos 30 días)
        recent_30d = sum(1 for v in dated_videos if (now - v.published_date).days <= 30)
        if recent_30d >= 5:
            hype.hype_score = min(100, hype.hype_score + 20)
        
        # Determinar tendencia
        if hype.hype_score >= 80:
            hype.hype_trend = "exploding" if hype.weeks_since_first <= 4 else "hot"
        elif hype.hype_score >= 60:
            hype.hype_trend = "hot" if recent_30d >= 3 else "warm"
        elif hype.hype_score >= 40:
            hype.hype_trend = "warm"
        else:
            hype.hype_trend = "cooling" if hype.weeks_since_first > 12 else "cold"
        
        return hype

    def calculate_product_opportunity_score(
        self, 
        hype: HypeMetrics, 
        buying_intent: BuyingIntent,
        budget_alternatives: List[ProductMention],
        languages: List[LanguageStats]
    ) -> int:
        """
        Calcula un score de oportunidad de producto (0-100)
        Combina: hype, intención de compra, alternativas budget, cobertura de mercado
        """
        score = 0
        
        # Hype (0-30 puntos)
        if hype:
            score += int(hype.hype_score * 0.30)
        
        # Intención de compra (0-25 puntos)
        if buying_intent:
            if buying_intent.where_to_buy >= 3:
                score += 15
            elif buying_intent.where_to_buy >= 1:
                score += 10
            
            if buying_intent.europe_mentions >= 2:
                score += 10
            elif buying_intent.europe_mentions >= 1:
                score += 5
        
        # Alternativas budget detectadas (0-20 puntos) - indica nicho activo
        if budget_alternatives:
            score += min(20, len(budget_alternatives) * 4)
        
        # Cobertura de mercados objetivo (0-25 puntos)
        if languages:
            target_markets = ["es", "pt", "fr", "it", "de"]
            covered = sum(1 for lang in languages if lang.language in target_markets)
            score += covered * 5
        
        return min(100, score)

    def deep_dive_analysis(
        self,
        brand: str,
        geo: str = "ES",
        max_videos: int = 50
    ) -> YouTubeDeepDive:
        """
        Realiza un análisis profundo ORIENTADO A PRODUCT DISCOVERY
        """
        deep_dive = YouTubeDeepDive(keyword=brand)
        
        try:
            # 1. Obtener videos por tipo
            videos_by_type = self.search_brand(brand, geo)
            deep_dive.videos_by_type = videos_by_type
            
            # 2. Recopilar todos los videos únicos
            all_videos = []
            seen_ids = set()
            
            for video_type, video_list in videos_by_type.items():
                for video in video_list:
                    if video.video_id not in seen_ids:
                        seen_ids.add(video.video_id)
                        all_videos.append(video)
            
            if not all_videos:
                return deep_dive
            
            # 3. Detectar idioma de cada video
            for video in all_videos:
                text = f"{video.title} {video.description}"
                video.language = self.detect_language(text)
            
            # 4. Estadísticas generales
            deep_dive.total_videos_analyzed = len(all_videos)
            deep_dive.total_views = sum(v.views for v in all_videos)
            deep_dive.total_engagement = sum(v.likes + v.comments for v in all_videos)
            
            if all_videos:
                deep_dive.avg_views_per_video = deep_dive.total_views // len(all_videos)
                total_engagement_rate = sum(v.engagement_rate for v in all_videos)
                deep_dive.avg_engagement_rate = total_engagement_rate / len(all_videos)
            
            # 5. NUEVO: Productos mencionados (detección dinámica)
            deep_dive.products_mentioned = self.extract_products_dynamic(all_videos, brand)
            
            # 6. NUEVO: Alternativas económicas
            deep_dive.budget_alternatives = self.detect_budget_alternatives(all_videos)
            
            # 7. NUEVO: Señales de intención de compra
            deep_dive.buying_intent = self.analyze_buying_intent(all_videos)
            
            # 8. NUEVO: Métricas de hype
            deep_dive.hype = self.calculate_hype_metrics(all_videos)
            
            # 9. Estadísticas por idioma (conectado a mercados)
            language_counter = Counter(v.language for v in all_videos)
            
            # Calcular métricas globales para comparación relativa
            total_views_all = sum(v.views for v in all_videos) if all_videos else 1
            total_videos = len(all_videos) if all_videos else 1
            avg_views_per_video = total_views_all / total_videos
            
            for lang, count in language_counter.most_common():
                lang_videos = [v for v in all_videos if v.language == lang]
                market_info = self.LANGUAGE_TO_MARKET.get(lang, {"market": "OTHER", "name": lang})
                
                # Métricas del idioma
                lang_views = sum(v.views for v in lang_videos)
                lang_percentage = (count / total_videos) * 100
                views_share = (lang_views / total_views_all) * 100 if total_views_all > 0 else 0
                
                # Oportunidad RELATIVA basada en share de mercado
                # No juzgamos "saturado" sin contexto - solo indicamos presencia
                if lang_percentage >= 40:
                    opportunity = "dominant"  # Este idioma domina el contenido
                elif lang_percentage >= 20:
                    opportunity = "significant"  # Presencia significativa
                elif lang_percentage >= 10:
                    opportunity = "moderate"  # Presencia moderada
                elif count >= 2:
                    opportunity = "emerging"  # Pocos videos pero hay actividad
                else:
                    opportunity = "minimal"  # Apenas hay contenido
                
                deep_dive.languages.append(LanguageStats(
                    language=lang,
                    language_name=market_info["name"],
                    target_market=market_info["market"],
                    video_count=count,
                    total_views=lang_views,
                    avg_engagement=sum(v.engagement_rate for v in lang_videos) / len(lang_videos) if lang_videos else 0,
                    percentage=lang_percentage,
                    market_opportunity=opportunity
                ))
            
            # 10. Top canales
            channel_stats = {}
            for video in all_videos:
                if video.channel not in channel_stats:
                    channel_stats[video.channel] = {
                        "videos": 0,
                        "views": 0,
                        "channel_id": video.channel_id
                    }
                channel_stats[video.channel]["videos"] += 1
                channel_stats[video.channel]["views"] += video.views
            
            sorted_channels = sorted(channel_stats.items(), key=lambda x: x[1]["views"], reverse=True)
            for channel, stats in sorted_channels[:10]:
                deep_dive.top_channels.append({
                    "name": channel,
                    "video_count": stats["videos"],
                    "total_views": stats["views"],
                    "channel_id": stats["channel_id"]
                })
            
            # 11. Timeline (videos por mes)
            for video in all_videos:
                if video.published_date:
                    month_key = video.published_date.strftime("%Y-%m")
                    deep_dive.timeline[month_key] = deep_dive.timeline.get(month_key, 0) + 1
            
            # 12. Tendencia de crecimiento
            if deep_dive.timeline and len(deep_dive.timeline) >= 3:
                sorted_months = sorted(deep_dive.timeline.keys())
                recent_avg = sum(deep_dive.timeline[m] for m in sorted_months[-3:]) / 3
                older_avg = sum(deep_dive.timeline[m] for m in sorted_months[:-3]) / max(1, len(sorted_months) - 3)
                
                if recent_avg > older_avg * 1.3:
                    deep_dive.growth_trend = "growing"
                elif recent_avg < older_avg * 0.7:
                    deep_dive.growth_trend = "declining"
                else:
                    deep_dive.growth_trend = "stable"
            
            # 13. Frescura del contenido
            now = datetime.utcnow()
            recent_30d = sum(1 for v in all_videos if v.published_date and (now - v.published_date).days <= 30)
            recent_90d = sum(1 for v in all_videos if v.published_date and (now - v.published_date).days <= 90)
            
            if recent_30d >= 5:
                deep_dive.content_freshness = "very_fresh"
            elif recent_30d >= 2 or recent_90d >= 10:
                deep_dive.content_freshness = "fresh"
            elif recent_90d >= 3:
                deep_dive.content_freshness = "aging"
            else:
                deep_dive.content_freshness = "stale"
            
            # 14. NUEVO: Score de oportunidad de producto
            deep_dive.product_opportunity_score = self.calculate_product_opportunity_score(
                deep_dive.hype,
                deep_dive.buying_intent,
                deep_dive.budget_alternatives,
                deep_dive.languages
            )
            
        except Exception as e:
            self._last_error = f"Error en deep dive: {str(e)}"
        
        return deep_dive

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

