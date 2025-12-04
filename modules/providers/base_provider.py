"""
Base AI Provider - Clase base abstracta para proveedores de IA

Define la interfaz común que todos los proveedores deben implementar.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any, Optional


class BaseAIProvider(ABC):
    """
    Clase base abstracta para proveedores de IA.
    
    Todos los proveedores (OpenAI, Claude, Perplexity) deben heredar
    de esta clase e implementar los métodos abstractos.
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa el proveedor con una API key.
        
        Args:
            api_key: Clave de API del proveedor
        """
        self.api_key = api_key
        self.client = None
        self._last_error: str = ""
        self._init_client()
    
    @abstractmethod
    def _init_client(self) -> None:
        """Inicializa el cliente específico del proveedor"""
        pass
    
    @abstractmethod
    def test_connection(self) -> Tuple[bool, str]:
        """
        Prueba la conexión con la API.
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        pass
    
    @abstractmethod
    def analyze_trend(self, trend_data: dict) -> dict:
        """
        Analiza datos de tendencia y genera insights.
        
        Args:
            trend_data: Diccionario con datos de tendencia
            
        Returns:
            Dict con análisis e insights
        """
        pass
    
    @abstractmethod
    def generate_blog_ideas(self, trend_data: dict, brand: str) -> dict:
        """
        Genera ideas de contenido para blog.
        
        Args:
            trend_data: Datos de tendencia
            brand: Nombre de la marca
            
        Returns:
            Dict con ideas de contenido
        """
        pass
    
    @abstractmethod
    def explain_seasonality(self, seasonality_data: dict, brand: str) -> str:
        """
        Explica patrones de estacionalidad.
        
        Args:
            seasonality_data: Datos de estacionalidad
            brand: Nombre de la marca
            
        Returns:
            Texto explicativo de la estacionalidad
        """
        pass
    
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible.
        
        Returns:
            True si está configurado y conectado
        """
        return self.client is not None and bool(self.api_key)
    
    def get_last_error(self) -> str:
        """
        Retorna el último error ocurrido.
        
        Returns:
            Mensaje de error o cadena vacía
        """
        return self._last_error
    
    def _build_analysis_prompt(self, trend_data: dict) -> str:
        """
        Construye el prompt para análisis de tendencias.
        
        Este método tiene una implementación base que puede ser
        sobrescrita por subclases si necesitan prompts específicos.
        
        Args:
            trend_data: Datos de tendencia
            
        Returns:
            Prompt formateado para el modelo
        """
        keyword = trend_data.get("keyword", "N/A")
        growth = trend_data.get("growth", {})
        current = trend_data.get("current_value", 0)
        
        return f"""Analiza esta tendencia de búsqueda:

**Término:** {keyword}
**Valor actual:** {current}/100 (índice Google Trends)
**Cambio reciente:** {growth.get("recent_change", 0):.1f}%
**Cambio anual:** {growth.get("annual_change", 0):.1f}%

Datos mensuales recientes: {trend_data.get("monthly_values", [])}

Proporciona:
1. **Estado actual** de la tendencia (creciendo/estable/decayendo)
2. **Factores** que podrían explicar el comportamiento
3. **Predicción** a corto plazo (próximos 3 meses)
4. **Recomendación accionable** para retail de tecnología

Sé conciso y directo. Máximo 200 palabras."""


# =============================================================================
# PROMPTS COMPARTIDOS
# =============================================================================

SYSTEM_PROMPT_ANALYST = """Eres un analista de tendencias de mercado especializado en retail de tecnología. 
Proporcionas insights accionables y directos para equipos de product discovery.
Tus análisis son concisos, basados en datos, y orientados a la acción."""

BLOG_IDEAS_PROMPT_TEMPLATE = """Genera {num_ideas} ideas de contenido para blog sobre "{brand}" basándote en estos datos:

Tendencia: {trend_status}
Crecimiento: {growth}%
Consultas relacionadas: {related_queries}

Para cada idea incluye:
- Título propuesto
- Palabras clave SEO (3-5)
- Ángulo/enfoque del artículo
- Audiencia objetivo

Formato: JSON con lista de objetos."""

SEASONALITY_PROMPT_TEMPLATE = """Analiza este patrón de estacionalidad para "{brand}":

Meses pico: {peak_months}
Meses valle: {low_months}
Variación: {variation}%
Es estacional: {is_seasonal}

Explica:
1. Por qué ocurre este patrón (eventos, temporadas, lanzamientos)
2. Cómo aprovechar los picos
3. Cómo mitigar los valles

Máximo 150 palabras."""
