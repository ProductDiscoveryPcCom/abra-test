"""
Market Intelligence Module
Análisis completo de mercado usando Perplexity para búsquedas en tiempo real

Funcionalidades:
- Análisis de ciclo de vida real de productos
- Sentimiento de mercado
- Contexto competitivo
- Insights accionables
- Detección de oportunidades
"""

import streamlit as st
import requests
import json
import re
import html
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


def _sanitize_input(text: str, max_length: int = 200) -> str:
    """
    Sanitiza input de usuario para prevenir prompt injection
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Convertir a string si no lo es
    text = str(text)
    
    # Escapar HTML
    text = html.escape(text)
    
    # Eliminar caracteres de control y secuencias peligrosas
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Eliminar patrones de prompt injection comunes
    dangerous_patterns = [
        r'ignore\s+(previous|above|all)\s+instructions?',
        r'disregard\s+(previous|above|all)',
        r'forget\s+(everything|all|previous)',
        r'new\s+instructions?:',
        r'system\s*:',
        r'admin\s*:',
        r'override\s*:',
        r'\[INST\]',
        r'\[/INST\]',
        r'<\|.*?\|>',
        r'###\s*(system|instruction)',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Limitar longitud
    if len(text) > max_length:
        text = text[:max_length]
    
    # Eliminar espacios extras
    text = ' '.join(text.split())
    
    return text.strip()


class RealLifecycleStage(Enum):
    """Etapas reales del ciclo de vida basadas en información de mercado"""
    PRE_LAUNCH = "Pre-lanzamiento"
    LAUNCH = "Lanzamiento"
    GROWTH = "Crecimiento"
    MATURITY = "Madurez"
    DECLINE = "Declive"
    DISCONTINUED = "Descatalogado"
    UNKNOWN = "Desconocido"


class SentimentLevel(Enum):
    """Niveles de sentimiento"""
    VERY_POSITIVE = "Muy positivo"
    POSITIVE = "Positivo"
    NEUTRAL = "Neutral"
    NEGATIVE = "Negativo"
    VERY_NEGATIVE = "Muy negativo"
    UNKNOWN = "Sin datos"


@dataclass
class ProductIntelligence:
    """Inteligencia de producto obtenida de Perplexity"""
    name: str
    # Ciclo de vida real
    lifecycle_stage: RealLifecycleStage = RealLifecycleStage.UNKNOWN
    lifecycle_reason: str = ""
    launch_date: str = ""
    # Sentimiento
    sentiment: SentimentLevel = SentimentLevel.UNKNOWN
    sentiment_summary: str = ""
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    # Mercado
    market_position: str = ""
    main_competitors: List[str] = field(default_factory=list)
    price_range: str = ""
    target_audience: str = ""
    # Insights
    opportunities: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    recommendation: str = ""
    # Metadata
    sources: List[str] = field(default_factory=list)
    analysis_date: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class MarketAnalysis:
    """Análisis completo de mercado para una marca/categoría"""
    brand: str
    # Visión general
    brand_overview: str = ""
    market_size: str = ""
    market_trend: str = ""
    # Competencia
    competitive_landscape: str = ""
    main_players: List[Dict[str, str]] = field(default_factory=list)
    brand_positioning: str = ""
    # Productos
    product_portfolio: List[str] = field(default_factory=list)
    best_sellers: List[str] = field(default_factory=list)
    recent_launches: List[str] = field(default_factory=list)
    # Tendencias
    current_trends: List[str] = field(default_factory=list)
    future_outlook: str = ""
    # Oportunidades
    market_opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)
    # Recomendación
    strategic_recommendation: str = ""
    action_items: List[str] = field(default_factory=list)
    # Metadata
    sources: List[str] = field(default_factory=list)
    analysis_date: str = field(default_factory=lambda: datetime.now().isoformat())


class MarketIntelligence:
    """
    Motor de inteligencia de mercado usando Perplexity
    
    Perplexity es ideal porque:
    - Busca información en tiempo real
    - Proporciona fuentes verificables
    - No tiene knowledge cutoff
    
    Modelos disponibles (2025):
    - sonar: Lightweight, rápido, económico ($1/M tokens)
    - sonar-pro: Búsqueda avanzada, 2x más citas ($3/M input, $15/M output)
    - sonar-reasoning: Con capacidades de razonamiento
    - sonar-reasoning-pro: Razonamiento avanzado (basado en DeepSeek R1)
    - sonar-deep-research: Para investigación exhaustiva
    """
    
    BASE_URL = "https://api.perplexity.ai/chat/completions"
    
    # Modelos actualizados (2025)
    MODEL_FAST = "sonar"  # Antes: llama-3.1-sonar-small-128k-online
    MODEL_QUALITY = "sonar-pro"  # Antes: llama-3.1-sonar-large-128k-online
    MODEL_REASONING = "sonar-reasoning"  # Para análisis complejos
    MODEL_DEEP_RESEARCH = "sonar-deep-research"  # Para investigación exhaustiva
    
    def __init__(self, api_key: str):
        """
        Inicializa el módulo de inteligencia de mercado
        
        Args:
            api_key: API key de Perplexity (debe empezar con 'pplx-')
            
        Raises:
            ValueError: Si la API key no es válida
        """
        if not api_key:
            raise ValueError("Perplexity API key es requerida")
        
        # Validar formato de la key
        if not isinstance(api_key, str):
            raise ValueError("API key debe ser un string")
        
        api_key = api_key.strip()
        
        if not api_key.startswith("pplx-"):
            raise ValueError("API key de Perplexity debe empezar con 'pplx-'")
        
        if len(api_key) < 15:
            raise ValueError("API key de Perplexity es demasiado corta")
        
        self.api_key = api_key
        self._cache: Dict[str, Any] = {}
        self._last_error: str = ""
    
    def test_connection(self) -> tuple:
        """
        Prueba la conexión con la API de Perplexity
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        from typing import Tuple
        
        if not self.api_key:
            return False, "API Key no configurada"
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.MODEL_FAST,  # Usar modelo más barato para test
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            }
            
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                return True, f"Conectado ({self.MODEL_FAST})"
            elif response.status_code == 401:
                return False, "API Key inválida"
            elif response.status_code == 429:
                return True, "Conectado (rate limited)"
            else:
                return False, f"Error HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return False, "Timeout de conexión"
        except requests.exceptions.ConnectionError:
            return False, "Error de conexión"
        except Exception as e:
            return False, f"Error: {str(e)[:30]}"
    
    def _call_perplexity(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1500,
        use_quality_model: bool = True,
        search_context_size: str = "medium"  # low, medium, high
    ) -> Dict[str, Any]:
        """
        Llamada base a Perplexity API (actualizado 2025)
        
        Args:
            prompt: Pregunta o consulta
            system_prompt: Instrucciones del sistema
            max_tokens: Máximo de tokens en respuesta
            use_quality_model: True para sonar-pro, False para sonar
            search_context_size: Profundidad de búsqueda (low/medium/high)
        
        Returns:
            Dict con content, citations, y success
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            payload = {
                "model": self.MODEL_QUALITY if use_quality_model else self.MODEL_FAST,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.2,  # Más determinista para análisis
            }
            
            # Añadir web_search_options solo si se especifica (puede causar 400 en algunos casos)
            if search_context_size and search_context_size in ("low", "medium", "high"):
                payload["web_search_options"] = {
                    "search_context_size": search_context_size
                }
            
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=90
            )
            
            # Si falla con 400, reintentar sin web_search_options
            if response.status_code == 400 and "web_search_options" in payload:
                del payload["web_search_options"]
                response = requests.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=90
                )
            
            # Manejar errores HTTP específicos
            if response.status_code == 401:
                self._last_error = "API key de Perplexity inválida o expirada"
                return {"success": False, "error": self._last_error}
            elif response.status_code == 429:
                self._last_error = "Rate limit excedido en Perplexity. Espera unos minutos."
                return {"success": False, "error": self._last_error}
            elif response.status_code == 400:
                error_detail = response.json().get("error", {}).get("message", "Solicitud inválida")
                self._last_error = f"Error en solicitud: {error_detail}"
                return {"success": False, "error": self._last_error}
            
            response.raise_for_status()
            
            data = response.json()
            
            # Extraer citas de la respuesta (vienen por defecto)
            citations = data.get("citations", [])
            
            # También pueden venir en search_results
            search_results = data.get("search_results", [])
            if search_results and not citations:
                citations = [r.get("url", "") for r in search_results if r.get("url")]
            
            return {
                "success": True,
                "content": data["choices"][0]["message"]["content"],
                "citations": citations
            }
            
        except requests.exceptions.Timeout:
            self._last_error = "Timeout: Perplexity no respondió a tiempo (90s)"
            return {"success": False, "error": self._last_error}
        except requests.exceptions.ConnectionError:
            self._last_error = "Error de conexión con Perplexity API"
            return {"success": False, "error": self._last_error}
        except requests.exceptions.RequestException as e:
            self._last_error = f"Error de red: {str(e)}"
            return {"success": False, "error": self._last_error}
        except KeyError as e:
            self._last_error = f"Respuesta inesperada de Perplexity: {str(e)}"
            return {"success": False, "error": self._last_error}
        except Exception as e:
            self._last_error = f"Error inesperado: {str(e)}"
            return {"success": False, "error": self._last_error}
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Intenta parsear JSON de la respuesta"""
        try:
            # Limpiar markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            return json.loads(content.strip())
        except json.JSONDecodeError:
            return None
    
    def analyze_product_lifecycle(
        self,
        product_name: str,
        brand: str = "",
        category: str = "tecnología"
    ) -> ProductIntelligence:
        """
        Analiza el ciclo de vida REAL de un producto
        
        Busca información actual sobre:
        - Fecha de lanzamiento
        - Estado actual del producto
        - Si está descatalogado o tiene sucesor
        """
        # Sanitizar inputs
        product_name = _sanitize_input(product_name, max_length=100)
        brand = _sanitize_input(brand, max_length=50)
        category = _sanitize_input(category, max_length=50)
        
        if not product_name:
            return ProductIntelligence(name="", lifecycle_reason="Nombre de producto inválido")
        
        cache_key = f"lifecycle_{product_name}_{brand}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        full_name = f"{brand} {product_name}".strip() if brand else product_name
        
        prompt = f"""Analiza el ciclo de vida del producto "{full_name}" en el mercado de {category}.

BUSCA Y RESPONDE EN JSON:
{{
    "lifecycle_stage": "pre_launch|launch|growth|maturity|decline|discontinued",
    "lifecycle_reason": "Explicación breve de por qué está en esta etapa",
    "launch_date": "Fecha aproximada de lanzamiento (ej: 'Q1 2023', 'Marzo 2024')",
    "has_successor": true/false,
    "successor_name": "Nombre del sucesor si existe",
    "is_still_sold": true/false,
    "years_in_market": número aproximado
}}

CRITERIOS:
- PRE_LAUNCH: Anunciado pero no disponible
- LAUNCH: Menos de 6 meses en el mercado
- GROWTH: 6 meses a 2 años, ventas en aumento
- MATURITY: Más de 2 años, ventas estables
- DECLINE: Ventas bajando, posible sucesor anunciado
- DISCONTINUED: Ya no se fabrica/vende oficialmente

Responde SOLO con el JSON válido."""

        result = self._call_perplexity(
            prompt=prompt,
            system_prompt="Eres un analista de productos de tecnología. Proporciona información precisa basada en datos actuales.",
            max_tokens=500
        )
        
        intel = ProductIntelligence(name=full_name)
        
        if result["success"]:
            data = self._parse_json_response(result["content"])
            if data:
                # Mapear stage
                stage_map = {
                    "pre_launch": RealLifecycleStage.PRE_LAUNCH,
                    "launch": RealLifecycleStage.LAUNCH,
                    "growth": RealLifecycleStage.GROWTH,
                    "maturity": RealLifecycleStage.MATURITY,
                    "decline": RealLifecycleStage.DECLINE,
                    "discontinued": RealLifecycleStage.DISCONTINUED
                }
                intel.lifecycle_stage = stage_map.get(
                    data.get("lifecycle_stage", "").lower(),
                    RealLifecycleStage.UNKNOWN
                )
                intel.lifecycle_reason = data.get("lifecycle_reason", "")
                intel.launch_date = data.get("launch_date", "")
            
            intel.sources = result.get("citations", [])
        
        self._cache[cache_key] = intel
        return intel
    
    def analyze_product_sentiment(
        self,
        product_name: str,
        brand: str = ""
    ) -> ProductIntelligence:
        """
        Analiza el sentimiento del mercado sobre un producto
        
        Busca:
        - Reviews y opiniones
        - Pros y contras
        - Satisfacción general
        """
        # Sanitizar inputs
        product_name = _sanitize_input(product_name, max_length=100)
        brand = _sanitize_input(brand, max_length=50)
        
        if not product_name:
            return ProductIntelligence(name="", sentiment_summary="Nombre de producto inválido")
        
        cache_key = f"sentiment_{product_name}_{brand}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        full_name = f"{brand} {product_name}".strip() if brand else product_name
        
        prompt = f"""Analiza el sentimiento del mercado sobre "{full_name}" basándote en reviews, opiniones de usuarios y expertos.

BUSCA Y RESPONDE EN JSON:
{{
    "sentiment": "very_positive|positive|neutral|negative|very_negative",
    "sentiment_score": número del 1-10,
    "sentiment_summary": "Resumen de 2-3 frases del sentimiento general",
    "pros": ["Pro 1", "Pro 2", "Pro 3"],
    "cons": ["Contra 1", "Contra 2", "Contra 3"],
    "common_complaints": ["Queja frecuente 1", "Queja frecuente 2"],
    "praised_features": ["Característica elogiada 1", "Característica elogiada 2"],
    "review_sources": ["Fuente 1", "Fuente 2"]
}}

Basa tu análisis en reviews reales de usuarios y expertos. Responde SOLO con JSON válido."""

        result = self._call_perplexity(
            prompt=prompt,
            system_prompt="Eres un analista de reviews de productos. Sintetiza opiniones de múltiples fuentes de forma objetiva.",
            max_tokens=800
        )
        
        intel = ProductIntelligence(name=full_name)
        
        if result["success"]:
            data = self._parse_json_response(result["content"])
            if data:
                sentiment_map = {
                    "very_positive": SentimentLevel.VERY_POSITIVE,
                    "positive": SentimentLevel.POSITIVE,
                    "neutral": SentimentLevel.NEUTRAL,
                    "negative": SentimentLevel.NEGATIVE,
                    "very_negative": SentimentLevel.VERY_NEGATIVE
                }
                intel.sentiment = sentiment_map.get(
                    data.get("sentiment", "").lower(),
                    SentimentLevel.UNKNOWN
                )
                intel.sentiment_summary = data.get("sentiment_summary", "")
                intel.pros = data.get("pros", [])[:5]
                intel.cons = data.get("cons", [])[:5]
            
            intel.sources = result.get("citations", [])
        
        self._cache[cache_key] = intel
        return intel
    
    def analyze_product_complete(
        self,
        product_name: str,
        brand: str = "",
        include_competitors: bool = True
    ) -> ProductIntelligence:
        """
        Análisis completo de un producto: ciclo de vida + sentimiento + mercado
        """
        # Sanitizar inputs
        product_name = _sanitize_input(product_name, max_length=100)
        brand = _sanitize_input(brand, max_length=50)
        
        if not product_name:
            return ProductIntelligence(name="", recommendation="Nombre de producto inválido")
        
        full_name = f"{brand} {product_name}".strip() if brand else product_name
        cache_key = f"complete_{full_name}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        prompt = f"""Realiza un análisis completo del producto "{full_name}" para un retailer de tecnología.

BUSCA INFORMACIÓN ACTUAL Y RESPONDE EN JSON:
{{
    "lifecycle": {{
        "stage": "pre_launch|launch|growth|maturity|decline|discontinued",
        "reason": "Por qué está en esta etapa",
        "launch_date": "Fecha aproximada",
        "is_current_model": true/false
    }},
    "sentiment": {{
        "level": "very_positive|positive|neutral|negative|very_negative",
        "score": 1-10,
        "summary": "Resumen del sentimiento",
        "pros": ["Pro 1", "Pro 2", "Pro 3"],
        "cons": ["Contra 1", "Contra 2", "Contra 3"]
    }},
    "market": {{
        "position": "Descripción de su posición en el mercado",
        "competitors": ["Competidor 1", "Competidor 2", "Competidor 3"],
        "price_segment": "entrada|medio|premium|ultra-premium",
        "target_audience": "Descripción del público objetivo"
    }},
    "retail_insights": {{
        "opportunities": ["Oportunidad 1", "Oportunidad 2"],
        "risks": ["Riesgo 1", "Riesgo 2"],
        "recommendation": "Recomendación concreta para el retailer",
        "stock_priority": "alta|media|baja"
    }}
}}

Responde SOLO con JSON válido."""

        result = self._call_perplexity(
            prompt=prompt,
            system_prompt="Eres un analista senior de product discovery para retail de tecnología. Proporciona insights accionables basados en datos de mercado actuales.",
            max_tokens=1500
        )
        
        intel = ProductIntelligence(name=full_name)
        
        if result["success"]:
            data = self._parse_json_response(result["content"])
            if data:
                # Lifecycle
                lifecycle_data = data.get("lifecycle", {})
                stage_map = {
                    "pre_launch": RealLifecycleStage.PRE_LAUNCH,
                    "launch": RealLifecycleStage.LAUNCH,
                    "growth": RealLifecycleStage.GROWTH,
                    "maturity": RealLifecycleStage.MATURITY,
                    "decline": RealLifecycleStage.DECLINE,
                    "discontinued": RealLifecycleStage.DISCONTINUED
                }
                intel.lifecycle_stage = stage_map.get(
                    lifecycle_data.get("stage", "").lower(),
                    RealLifecycleStage.UNKNOWN
                )
                intel.lifecycle_reason = lifecycle_data.get("reason", "")
                intel.launch_date = lifecycle_data.get("launch_date", "")
                
                # Sentiment
                sentiment_data = data.get("sentiment", {})
                sentiment_map = {
                    "very_positive": SentimentLevel.VERY_POSITIVE,
                    "positive": SentimentLevel.POSITIVE,
                    "neutral": SentimentLevel.NEUTRAL,
                    "negative": SentimentLevel.NEGATIVE,
                    "very_negative": SentimentLevel.VERY_NEGATIVE
                }
                intel.sentiment = sentiment_map.get(
                    sentiment_data.get("level", "").lower(),
                    SentimentLevel.UNKNOWN
                )
                intel.sentiment_summary = sentiment_data.get("summary", "")
                intel.pros = sentiment_data.get("pros", [])[:5]
                intel.cons = sentiment_data.get("cons", [])[:5]
                
                # Market
                market_data = data.get("market", {})
                intel.market_position = market_data.get("position", "")
                intel.main_competitors = market_data.get("competitors", [])[:5]
                intel.price_range = market_data.get("price_segment", "")
                intel.target_audience = market_data.get("target_audience", "")
                
                # Retail insights
                retail_data = data.get("retail_insights", {})
                intel.opportunities = retail_data.get("opportunities", [])[:5]
                intel.risks = retail_data.get("risks", [])[:5]
                intel.recommendation = retail_data.get("recommendation", "")
            
            intel.sources = result.get("citations", [])
        
        self._cache[cache_key] = intel
        return intel
    
    def analyze_market(
        self,
        brand: str,
        category: str = "tecnología",
        geo: str = "España"
    ) -> MarketAnalysis:
        """
        Análisis completo de mercado para una marca o categoría
        """
        # Sanitizar inputs
        brand = _sanitize_input(brand, max_length=100)
        category = _sanitize_input(category, max_length=50)
        geo = _sanitize_input(geo, max_length=50)
        
        if not brand:
            return MarketAnalysis(brand="", strategic_recommendation="Nombre de marca inválido")
        
        cache_key = f"market_{brand}_{category}_{geo}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        prompt = f"""Realiza un análisis de mercado completo para "{brand}" en el sector de {category} en {geo}.

BUSCA INFORMACIÓN ACTUAL Y RESPONDE EN JSON:
{{
    "brand_overview": "Descripción de la marca/categoría (2-3 frases)",
    "market_info": {{
        "size": "Estimación del tamaño de mercado",
        "trend": "crecimiento|estable|declive",
        "growth_rate": "Tasa de crecimiento si se conoce"
    }},
    "competition": {{
        "landscape": "Descripción del panorama competitivo",
        "main_players": [
            {{"name": "Competidor 1", "position": "Líder/Challenger/etc", "strength": "Fortaleza principal"}},
            {{"name": "Competidor 2", "position": "...", "strength": "..."}}
        ],
        "brand_positioning": "Posicionamiento de {brand} vs competencia"
    }},
    "products": {{
        "portfolio": ["Categoría/línea 1", "Categoría/línea 2"],
        "best_sellers": ["Producto estrella 1", "Producto estrella 2"],
        "recent_launches": ["Lanzamiento reciente 1", "Lanzamiento reciente 2"]
    }},
    "trends": {{
        "current": ["Tendencia actual 1", "Tendencia actual 2"],
        "future_outlook": "Perspectiva a 12-24 meses"
    }},
    "opportunities_threats": {{
        "opportunities": ["Oportunidad 1", "Oportunidad 2", "Oportunidad 3"],
        "threats": ["Amenaza 1", "Amenaza 2"]
    }},
    "recommendation": {{
        "strategic": "Recomendación estratégica principal",
        "action_items": ["Acción 1", "Acción 2", "Acción 3"]
    }}
}}

Responde SOLO con JSON válido."""

        result = self._call_perplexity(
            prompt=prompt,
            system_prompt="Eres un analista de mercado senior especializado en retail de tecnología en Europa. Proporciona análisis basados en datos actuales con recomendaciones accionables.",
            max_tokens=2000
        )
        
        analysis = MarketAnalysis(brand=brand)
        
        if result["success"]:
            data = self._parse_json_response(result["content"])
            if data:
                analysis.brand_overview = data.get("brand_overview", "")
                
                # Market info
                market = data.get("market_info", {})
                analysis.market_size = market.get("size", "")
                analysis.market_trend = market.get("trend", "")
                
                # Competition
                comp = data.get("competition", {})
                analysis.competitive_landscape = comp.get("landscape", "")
                analysis.main_players = comp.get("main_players", [])[:5]
                analysis.brand_positioning = comp.get("brand_positioning", "")
                
                # Products
                products = data.get("products", {})
                analysis.product_portfolio = products.get("portfolio", [])
                analysis.best_sellers = products.get("best_sellers", [])[:5]
                analysis.recent_launches = products.get("recent_launches", [])[:5]
                
                # Trends
                trends = data.get("trends", {})
                analysis.current_trends = trends.get("current", [])[:5]
                analysis.future_outlook = trends.get("future_outlook", "")
                
                # Opportunities/Threats
                opp_threats = data.get("opportunities_threats", {})
                analysis.market_opportunities = opp_threats.get("opportunities", [])[:5]
                analysis.threats = opp_threats.get("threats", [])[:5]
                
                # Recommendation
                rec = data.get("recommendation", {})
                analysis.strategic_recommendation = rec.get("strategic", "")
                analysis.action_items = rec.get("action_items", [])[:5]
            
            analysis.sources = result.get("citations", [])
        
        self._cache[cache_key] = analysis
        return analysis
    
    def get_breakout_explanation(
        self,
        keyword: str,
        growth_rate: float
    ) -> str:
        """
        Explica por qué un término está en breakout
        """
        # Sanitizar input
        keyword = _sanitize_input(keyword, max_length=100)
        
        if not keyword:
            return "No se pudo analizar: keyword inválido"
        
        # Validar growth_rate
        try:
            growth_rate = float(growth_rate)
        except (ValueError, TypeError):
            growth_rate = 0.0
        
        prompt = f"""El término "{keyword}" está experimentando un crecimiento explosivo ({growth_rate}% en Google Trends).

Busca información actual y explica en 2-3 frases:
1. ¿Por qué está creciendo tanto?
2. ¿Hay algún evento, lanzamiento o noticia que lo explique?

Sé específico y menciona fechas/eventos concretos si los encuentras."""

        result = self._call_perplexity(
            prompt=prompt,
            system_prompt="Eres un analista de tendencias. Explica los picos de interés de forma concisa.",
            max_tokens=300,
            use_quality_model=False  # Más rápido para explicaciones simples
        )
        
        if result["success"]:
            return result["content"]
        return f"Crecimiento significativo detectado para {keyword}."
    
    def compare_products(
        self,
        products: List[str],
        criteria: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compara múltiples productos
        """
        # Sanitizar inputs
        if not products:
            return {"error": "No se proporcionaron productos"}
        
        # Sanitizar cada producto
        sanitized_products = [_sanitize_input(p, max_length=100) for p in products[:5]]
        sanitized_products = [p for p in sanitized_products if p]  # Eliminar vacíos
        
        if not sanitized_products:
            return {"error": "Nombres de productos inválidos"}
        
        if not criteria:
            criteria = ["precio", "rendimiento", "calidad", "soporte", "valor"]
        else:
            criteria = [_sanitize_input(c, max_length=30) for c in criteria[:10]]
            criteria = [c for c in criteria if c]
        
        products_str = ", ".join(sanitized_products)
        criteria_str = ", ".join(criteria)
        
        prompt = f"""Compara estos productos: {products_str}

Criterios de comparación: {criteria_str}

RESPONDE EN JSON:
{{
    "comparison_table": [
        {{"product": "Producto 1", "precio": "€XXX", "rendimiento": "X/10", ...}},
        ...
    ],
    "winner_overall": "Nombre del mejor producto general",
    "winner_by_criteria": {{
        "precio": "Mejor en precio",
        "rendimiento": "Mejor en rendimiento",
        ...
    }},
    "summary": "Resumen de la comparación en 2-3 frases",
    "recommendation": "Recomendación según caso de uso"
}}

Responde SOLO con JSON válido."""

        result = self._call_perplexity(
            prompt=prompt,
            system_prompt="Eres un experto en comparativas de productos tecnológicos. Sé objetivo y basa las comparaciones en datos.",
            max_tokens=1200
        )
        
        if result["success"]:
            data = self._parse_json_response(result["content"])
            if data:
                data["sources"] = result.get("citations", [])
                return data
        
        return {"error": "No se pudo completar la comparación"}
    
    def get_last_error(self) -> str:
        """Devuelve el último error"""
        return self._last_error
    
    def clear_cache(self):
        """Limpia la caché"""
        self._cache.clear()


def get_market_intelligence() -> Optional[MarketIntelligence]:
    """Factory para obtener módulo configurado"""
    api_key = st.secrets.get("PERPLEXITY_API_KEY", "")
    
    # Validar formato básico de la key
    if api_key and api_key.startswith("pplx-") and len(api_key) > 10:
        try:
            return MarketIntelligence(api_key=api_key)
        except ValueError as e:
            st.warning(f"Error configurando Perplexity: {str(e)}")
            return None
    return None


def check_perplexity_config() -> Dict[str, bool]:
    """Verifica si Perplexity está configurado"""
    api_key = st.secrets.get("PERPLEXITY_API_KEY", "")
    
    is_valid_format = (
        bool(api_key) and 
        api_key.startswith("pplx-") and 
        len(api_key) > 10 and
        len(api_key) < 100  # Límite razonable
    )
    
    return {
        "configured": is_valid_format,
        "has_key": bool(api_key),
        "key_format_valid": is_valid_format
    }
