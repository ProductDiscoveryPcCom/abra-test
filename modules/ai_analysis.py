"""
AI Analysis Module
Orquestador que gestiona múltiples proveedores de IA
"""

from typing import Optional, Literal
import streamlit as st

from .providers import ClaudeProvider, OpenAIProvider, PerplexityProvider


ProviderType = Literal["claude", "gpt4", "perplexity"]


class AIAnalyzer:
    """Orquestador de análisis con múltiples proveedores de IA"""
    
    PROVIDER_NAMES = {
        "claude": "Claude (Anthropic)",
        "gpt4": "GPT-4 (OpenAI)",
        "perplexity": "Perplexity"
    }
    
    def __init__(self):
        self.providers = {}
        self._init_providers()
    
    def _init_providers(self):
        """Inicializa los proveedores disponibles basándose en las API keys"""
        # Claude
        claude_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if claude_key:
            try:
                self.providers["claude"] = ClaudeProvider(claude_key)
            except Exception as e:
                st.warning(f"Error inicializando Claude: {e}")
        
        # GPT-4
        openai_key = st.secrets.get("OPENAI_API_KEY", "")
        if openai_key:
            try:
                self.providers["gpt4"] = OpenAIProvider(openai_key)
            except Exception as e:
                st.warning(f"Error inicializando GPT-4: {e}")
        
        # Perplexity
        perplexity_key = st.secrets.get("PERPLEXITY_API_KEY", "")
        if perplexity_key:
            try:
                self.providers["perplexity"] = PerplexityProvider(perplexity_key)
            except Exception as e:
                st.warning(f"Error inicializando Perplexity: {e}")
    
    def get_available_providers(self) -> list:
        """Retorna lista de proveedores disponibles"""
        return list(self.providers.keys())
    
    def get_provider_status(self) -> dict:
        """Retorna el estado de cada proveedor"""
        status = {}
        for name in ["claude", "gpt4", "perplexity"]:
            if name in self.providers:
                status[name] = {
                    "available": True,
                    "display_name": self.PROVIDER_NAMES[name]
                }
            else:
                status[name] = {
                    "available": False,
                    "display_name": self.PROVIDER_NAMES[name]
                }
        return status
    
    def analyze(
        self,
        trend_data: dict,
        provider: ProviderType = "claude"
    ) -> dict:
        """
        Ejecuta análisis con el proveedor seleccionado
        
        Args:
            trend_data: Diccionario con todos los datos de tendencia
            provider: Proveedor a usar (claude, gpt4, perplexity)
        
        Returns:
            dict con análisis, ideas de blog, etc.
        """
        if provider not in self.providers:
            available = self.get_available_providers()
            if available:
                provider = available[0]
            else:
                return {
                    "success": False,
                    "error": "No hay proveedores de IA configurados"
                }
        
        selected_provider = self.providers[provider]
        
        # Ejecutar análisis
        analysis_result = selected_provider.analyze_trend(trend_data)
        
        # Generar ideas de blog
        blog_result = selected_provider.generate_blog_ideas(
            trend_data, 
            trend_data.get("keyword", "")
        )
        
        return {
            "success": analysis_result["success"],
            "analysis": analysis_result.get("analysis", ""),
            "blog_ideas": blog_result.get("ideas", []),
            "provider": self.PROVIDER_NAMES.get(provider, provider),
            "error": analysis_result.get("error") or blog_result.get("error")
        }
    
    def explain_seasonality(
        self,
        seasonality_data: dict,
        brand: str,
        provider: ProviderType = "claude"
    ) -> str:
        """Genera explicación de estacionalidad con el proveedor seleccionado"""
        if provider not in self.providers:
            available = self.get_available_providers()
            if available:
                provider = available[0]
            else:
                return "No hay proveedores de IA configurados para generar explicación."
        
        return self.providers[provider].explain_seasonality(seasonality_data, brand)
    
    def get_brand_context(
        self,
        brand: str,
        provider: ProviderType = "perplexity"
    ) -> dict:
        """
        Obtiene contexto adicional de la marca
        Usa Perplexity por defecto (tiene búsqueda en tiempo real)
        """
        # Perplexity es ideal para esto por su búsqueda en tiempo real
        if "perplexity" in self.providers and provider == "perplexity":
            return self.providers["perplexity"].search_brand_context(brand)
        
        # Fallback a otros proveedores con prompt genérico
        if provider in self.providers:
            result = self.providers[provider].analyze_trend({
                "keyword": brand,
                "current_value": "N/A",
                "growth_rate": "N/A"
            })
            return {
                "success": result["success"],
                "context": result.get("analysis", ""),
                "provider": result.get("provider", "")
            }
        
        return {
            "success": False,
            "error": "No hay proveedores disponibles"
        }


def render_provider_selector() -> str:
    """
    Renderiza un selector de proveedores de IA en Streamlit
    Returns: El proveedor seleccionado
    """
    analyzer = AIAnalyzer()
    status = analyzer.get_provider_status()
    
    # Crear opciones con indicador de disponibilidad
    options = []
    option_map = {}
    
    for key, info in status.items():
        if info["available"]:
            label = f"✅ {info['display_name']}"
        else:
            label = f"⚠️ {info['display_name']} (no configurado)"
        options.append(label)
        option_map[label] = key
    
    selected_label = st.selectbox(
        "Proveedor de IA",
        options,
        help="Selecciona qué modelo de IA usar para el análisis"
    )
    
    return option_map.get(selected_label, "claude")
