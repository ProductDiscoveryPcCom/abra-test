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
    Renderiza un selector de proveedores de IA en Streamlit con info de costos
    Returns: El proveedor seleccionado
    """
    analyzer = AIAnalyzer()
    status = analyzer.get_provider_status()

    # Información de precios por proveedor (por 1M tokens, actualizado 2025)
    PRICING_INFO = {
        "claude": {
            "name": "Claude Sonnet 4.5",
            "input": "$3",
            "output": "$15",
            "speed": "Rápido",
            "best_for": "Análisis profundo"
        },
        "gpt4": {
            "name": "GPT-4o",
            "input": "$2.50",
            "output": "$10",
            "speed": "Muy rápido",
            "best_for": "Balance calidad/precio"
        },
        "perplexity": {
            "name": "Sonar Pro",
            "input": "$3",
            "output": "$15",
            "speed": "Medio",
            "best_for": "Búsqueda en tiempo real"
        }
    }

    # Crear opciones con indicador de disponibilidad y precio
    options = []
    option_map = {}

    for key, info in status.items():
        pricing = PRICING_INFO.get(key, {})
        price_hint = f"~{pricing.get('input', '?')}/M"
        
        if info["available"]:
            label = f"✅ {pricing.get('name', info['display_name'])} ({price_hint})"
        else:
            label = f"○ {pricing.get('name', info['display_name'])} - No configurado"
        options.append(label)
        option_map[label] = key

    # Selector
    selected_label = st.selectbox(
        "Proveedor IA (solo 1)",
        options,
        help="Solo se usa UN proveedor por análisis para evitar costos duplicados",
        label_visibility="collapsed"
    )
    
    selected_key = option_map.get(selected_label, "claude")
    
    # Mostrar info del seleccionado
    if selected_key in PRICING_INFO and status.get(selected_key, {}).get("available"):
        pricing = PRICING_INFO[selected_key]
        st.caption(f"💰 {pricing['input']} input · {pricing['output']} output | ⚡ {pricing['speed']}")

    return selected_key

