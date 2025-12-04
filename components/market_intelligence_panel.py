"""
Market Intelligence Panel
Componente de UI para mostrar análisis de mercado con Perplexity
"""

import streamlit as st
import html as html_module
import re
from typing import Optional, Dict, Any, List
from dataclasses import asdict


def _sanitize_perplexity_data(text: str) -> str:
    """
    Sanitiza datos que vienen de Perplexity para mostrar con unsafe_allow_html
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        Texto seguro para mostrar en HTML
    """
    if not text:
        return ""
    
    # Convertir a string
    text = str(text)
    
    # Escapar HTML
    text = html_module.escape(text)
    
    # Limitar longitud para evitar DoS
    if len(text) > 5000:
        text = text[:5000] + "..."
    
    return text


def render_market_intelligence_panel(
    keyword: str,
    market_analysis: Any = None,
    product_intelligence: Any = None
) -> None:
    """
    Renderiza el panel completo de inteligencia de mercado
    
    Args:
        keyword: Keyword/marca analizada
        market_analysis: MarketAnalysis object de Perplexity
        product_intelligence: ProductIntelligence object de Perplexity
    """
    st.markdown("### 🧠 Inteligencia de Mercado")
    st.caption(f"Análisis en tiempo real para: **{html_module.escape(keyword)}**")
    
    if not market_analysis and not product_intelligence:
        st.info("""
        **Perplexity no está configurado.**
        
        Para activar el análisis de mercado inteligente, añade tu API key en `secrets.toml`:
        ```
        PERPLEXITY_API_KEY = "pplx-xxxx..."
        ```
        
        Obtén tu API key en [Perplexity Settings](https://www.perplexity.ai/settings/api)
        """)
        return
    
    # Tabs para diferentes vistas
    tabs = st.tabs([
        "📊 Visión General",
        "🎯 Ciclo de Vida",
        "💬 Sentimiento",
        "⚔️ Competencia",
        "💡 Oportunidades"
    ])
    
    with tabs[0]:
        _render_overview_tab(market_analysis, product_intelligence, keyword)
    
    with tabs[1]:
        _render_lifecycle_tab(product_intelligence)
    
    with tabs[2]:
        _render_sentiment_tab(product_intelligence)
    
    with tabs[3]:
        _render_competition_tab(market_analysis)
    
    with tabs[4]:
        _render_opportunities_tab(market_analysis, product_intelligence)


def _render_overview_tab(
    market_analysis: Any,
    product_intelligence: Any,
    keyword: str
) -> None:
    """Tab de visión general del mercado"""
    
    if market_analysis and market_analysis.brand_overview:
        st.markdown("#### 📋 Resumen")
        st.write(market_analysis.brand_overview)
        
        # Tendencia de mercado
        if market_analysis.market_trend:
            trend_icons = {
                "crecimiento": "📈",
                "estable": "➡️",
                "declive": "📉"
            }
            trend = market_analysis.market_trend.lower()
            icon = trend_icons.get(trend, "📊")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Tendencia de Mercado",
                    f"{icon} {market_analysis.market_trend.capitalize()}"
                )
            with col2:
                if market_analysis.market_size:
                    st.metric("Tamaño de Mercado", market_analysis.market_size)
    
    # Productos destacados
    if market_analysis and market_analysis.best_sellers:
        st.markdown("#### 🏆 Productos Destacados")
        cols = st.columns(min(3, len(market_analysis.best_sellers)))
        for i, product in enumerate(market_analysis.best_sellers[:3]):
            with cols[i]:
                st.info(f"**{product}**")
    
    # Lanzamientos recientes
    if market_analysis and market_analysis.recent_launches:
        st.markdown("#### 🆕 Lanzamientos Recientes")
        for launch in market_analysis.recent_launches[:5]:
            st.markdown(f"• {launch}")
    
    # Fuentes
    sources = []
    if market_analysis and market_analysis.sources:
        sources.extend(market_analysis.sources)
    if product_intelligence and product_intelligence.sources:
        sources.extend(product_intelligence.sources)
    
    if sources:
        with st.expander("📚 Fuentes"):
            for source in sources[:10]:
                st.caption(f"• {source}")


def _render_lifecycle_tab(product_intelligence: Any) -> None:
    """Tab de ciclo de vida del producto"""
    
    if not product_intelligence:
        st.info("No hay datos de ciclo de vida disponibles.")
        return
    
    # Indicador visual de ciclo de vida
    lifecycle_config = {
        "Pre-lanzamiento": {"color": "#8B5CF6", "icon": "🔮", "desc": "Producto anunciado pero no disponible aún"},
        "Lanzamiento": {"color": "#3B82F6", "icon": "🚀", "desc": "Producto nuevo en el mercado (< 6 meses)"},
        "Crecimiento": {"color": "#10B981", "icon": "📈", "desc": "Ventas en aumento, ganando tracción"},
        "Madurez": {"color": "#F59E0B", "icon": "⭐", "desc": "Producto establecido, ventas estables"},
        "Declive": {"color": "#EF4444", "icon": "📉", "desc": "Ventas bajando, posible sucesor"},
        "Descatalogado": {"color": "#6B7280", "icon": "🔴", "desc": "Ya no se fabrica/vende"},
        "Desconocido": {"color": "#9CA3AF", "icon": "❓", "desc": "No se pudo determinar"}
    }
    
    stage = product_intelligence.lifecycle_stage.value if hasattr(product_intelligence.lifecycle_stage, 'value') else str(product_intelligence.lifecycle_stage)
    config = lifecycle_config.get(stage, lifecycle_config["Desconocido"])
    
    # Mostrar indicador principal
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {config['color']}22, {config['color']}11);
        border-left: 4px solid {config['color']};
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    ">
        <h2 style="margin: 0; color: {config['color']};">
            {config['icon']} {stage}
        </h2>
        <p style="margin: 10px 0 0 0; color: #666;">
            {config['desc']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Detalles
    col1, col2 = st.columns(2)
    
    with col1:
        if product_intelligence.launch_date:
            st.metric("📅 Fecha de Lanzamiento", product_intelligence.launch_date)
    
    with col2:
        if product_intelligence.price_range:
            st.metric("💰 Segmento de Precio", product_intelligence.price_range.capitalize())
    
    # Razón del ciclo de vida
    if product_intelligence.lifecycle_reason:
        st.markdown("#### 📝 Análisis")
        st.write(product_intelligence.lifecycle_reason)
    
    # Timeline visual
    st.markdown("#### 📊 Posición en el Ciclo")
    stages = ["Pre-lanzamiento", "Lanzamiento", "Crecimiento", "Madurez", "Declive"]
    current_idx = stages.index(stage) if stage in stages else -1
    
    cols = st.columns(5)
    for i, s in enumerate(stages):
        with cols[i]:
            if i == current_idx:
                st.markdown(f"**🔵 {s}**")
            elif i < current_idx:
                st.markdown(f"✅ {s}")
            else:
                st.markdown(f"⚪ {s}")


def _render_sentiment_tab(product_intelligence: Any) -> None:
    """Tab de análisis de sentimiento"""
    
    if not product_intelligence:
        st.info("No hay datos de sentimiento disponibles.")
        return
    
    # Indicador de sentimiento
    sentiment_config = {
        "Muy positivo": {"color": "#059669", "icon": "😍", "score": 5},
        "Positivo": {"color": "#10B981", "icon": "😊", "score": 4},
        "Neutral": {"color": "#F59E0B", "icon": "😐", "score": 3},
        "Negativo": {"color": "#EF4444", "icon": "😕", "score": 2},
        "Muy negativo": {"color": "#DC2626", "icon": "😠", "score": 1},
        "Sin datos": {"color": "#9CA3AF", "icon": "❓", "score": 0}
    }
    
    sentiment = product_intelligence.sentiment.value if hasattr(product_intelligence.sentiment, 'value') else str(product_intelligence.sentiment)
    config = sentiment_config.get(sentiment, sentiment_config["Sin datos"])
    
    # Indicador visual
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="
            background: {config['color']}22;
            border: 2px solid {config['color']};
            padding: 30px;
            border-radius: 50%;
            text-align: center;
            width: 150px;
            margin: 0 auto;
        ">
            <span style="font-size: 48px;">{config['icon']}</span>
            <p style="margin: 10px 0 0 0; font-weight: bold; color: {config['color']};">
                {sentiment}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Resumen
    if product_intelligence.sentiment_summary:
        st.markdown("---")
        st.write(product_intelligence.sentiment_summary)
    
    # Pros y contras
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👍 Puntos Positivos")
        if product_intelligence.pros:
            for pro in product_intelligence.pros:
                st.success(f"✅ {pro}")
        else:
            st.info("Sin datos")
    
    with col2:
        st.markdown("#### 👎 Puntos Negativos")
        if product_intelligence.cons:
            for con in product_intelligence.cons:
                st.error(f"❌ {con}")
        else:
            st.info("Sin datos")


def _render_competition_tab(market_analysis: Any) -> None:
    """Tab de análisis competitivo"""
    
    if not market_analysis:
        st.info("No hay datos de competencia disponibles.")
        return
    
    # Panorama competitivo
    if market_analysis.competitive_landscape:
        st.markdown("#### 🎯 Panorama Competitivo")
        st.write(market_analysis.competitive_landscape)
    
    # Posicionamiento
    if market_analysis.brand_positioning:
        st.markdown("#### 📍 Posicionamiento")
        st.info(market_analysis.brand_positioning)
    
    # Principales competidores
    if market_analysis.main_players:
        st.markdown("#### ⚔️ Principales Competidores")
        
        for player in market_analysis.main_players[:5]:
            if isinstance(player, dict):
                name = player.get('name', 'N/A')
                position = player.get('position', '')
                strength = player.get('strength', '')
                
                with st.expander(f"**{name}** - {position}"):
                    if strength:
                        st.write(f"💪 Fortaleza: {strength}")
            else:
                st.markdown(f"• **{player}**")
    
    # Tendencias del sector
    if market_analysis.current_trends:
        st.markdown("#### 📈 Tendencias del Sector")
        for trend in market_analysis.current_trends:
            st.markdown(f"• {trend}")


def _render_opportunities_tab(market_analysis: Any, product_intelligence: Any) -> None:
    """Tab de oportunidades y recomendaciones"""
    
    # Oportunidades
    opportunities = []
    if market_analysis and market_analysis.market_opportunities:
        opportunities.extend(market_analysis.market_opportunities)
    if product_intelligence and product_intelligence.opportunities:
        opportunities.extend(product_intelligence.opportunities)
    
    if opportunities:
        st.markdown("#### 💡 Oportunidades Detectadas")
        for opp in list(set(opportunities))[:7]:  # Deduplicar y limitar
            st.success(f"✅ {opp}")
    
    # Amenazas/Riesgos
    threats = []
    if market_analysis and market_analysis.threats:
        threats.extend(market_analysis.threats)
    if product_intelligence and product_intelligence.risks:
        threats.extend(product_intelligence.risks)
    
    if threats:
        st.markdown("#### ⚠️ Amenazas y Riesgos")
        for threat in list(set(threats))[:5]:
            st.warning(f"🔸 {threat}")
    
    # Recomendación estratégica
    recommendation = None
    if market_analysis and market_analysis.strategic_recommendation:
        recommendation = market_analysis.strategic_recommendation
    elif product_intelligence and product_intelligence.recommendation:
        recommendation = product_intelligence.recommendation
    
    if recommendation:
        st.markdown("#### 🎯 Recomendación Estratégica")
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #6366F122, #8B5CF622);
            border-left: 4px solid #6366F1;
            padding: 20px;
            border-radius: 8px;
        ">
            <p style="margin: 0; font-size: 16px;">
                <strong>{_sanitize_perplexity_data(recommendation)}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Action items
    if market_analysis and market_analysis.action_items:
        st.markdown("#### 📋 Acciones Sugeridas")
        for i, action in enumerate(market_analysis.action_items[:5], 1):
            st.markdown(f"**{i}.** {_sanitize_perplexity_data(action)}")
    
    # Outlook futuro
    if market_analysis and market_analysis.future_outlook:
        st.markdown("#### 🔮 Perspectiva Futura")
        st.info(market_analysis.future_outlook)


def render_market_intelligence_mini(
    keyword: str,
    product_intelligence: Any = None
) -> Dict[str, Any]:
    """
    Versión compacta para mostrar en sidebar o resumen
    Retorna datos para usar en otras partes de la app
    """
    result = {
        "lifecycle": "Desconocido",
        "sentiment": "Sin datos",
        "has_data": False
    }
    
    if not product_intelligence:
        return result
    
    result["has_data"] = True
    
    # Ciclo de vida
    if hasattr(product_intelligence.lifecycle_stage, 'value'):
        result["lifecycle"] = product_intelligence.lifecycle_stage.value
    
    # Sentimiento
    if hasattr(product_intelligence.sentiment, 'value'):
        result["sentiment"] = product_intelligence.sentiment.value
    
    # Mostrar compacto
    col1, col2 = st.columns(2)
    
    lifecycle_icons = {
        "Pre-lanzamiento": "🔮",
        "Lanzamiento": "🚀",
        "Crecimiento": "📈",
        "Madurez": "⭐",
        "Declive": "📉",
        "Descatalogado": "🔴"
    }
    
    sentiment_icons = {
        "Muy positivo": "😍",
        "Positivo": "😊",
        "Neutral": "😐",
        "Negativo": "😕",
        "Muy negativo": "😠"
    }
    
    with col1:
        icon = lifecycle_icons.get(result["lifecycle"], "❓")
        st.metric("Ciclo de Vida", f"{icon} {result['lifecycle']}")
    
    with col2:
        icon = sentiment_icons.get(result["sentiment"], "❓")
        st.metric("Sentimiento", f"{icon} {result['sentiment']}")
    
    return result


def get_intelligence_for_pdf(
    market_analysis: Any = None,
    product_intelligence: Any = None
) -> Dict[str, Any]:
    """
    Extrae datos de inteligencia para el PDF
    """
    data = {
        "market_intelligence": {},
        "sentiment_data": {}
    }
    
    if market_analysis:
        data["market_intelligence"] = {
            "brand_overview": market_analysis.brand_overview,
            "market_size": market_analysis.market_size,
            "market_trend": market_analysis.market_trend,
            "competitive_landscape": market_analysis.competitive_landscape,
            "brand_positioning": market_analysis.brand_positioning,
            "main_players": market_analysis.main_players,
            "best_sellers": market_analysis.best_sellers,
            "recent_launches": market_analysis.recent_launches,
            "current_trends": market_analysis.current_trends,
            "future_outlook": market_analysis.future_outlook,
            "market_opportunities": market_analysis.market_opportunities,
            "threats": market_analysis.threats,
            "strategic_recommendation": market_analysis.strategic_recommendation,
            "action_items": market_analysis.action_items,
            "sources": market_analysis.sources
        }
    
    if product_intelligence:
        lifecycle = product_intelligence.lifecycle_stage.value if hasattr(product_intelligence.lifecycle_stage, 'value') else str(product_intelligence.lifecycle_stage)
        sentiment = product_intelligence.sentiment.value if hasattr(product_intelligence.sentiment, 'value') else str(product_intelligence.sentiment)
        
        data["sentiment_data"] = {
            "sentiment": sentiment,
            "sentiment_summary": product_intelligence.sentiment_summary,
            "pros": product_intelligence.pros,
            "cons": product_intelligence.cons,
            "lifecycle": lifecycle,
            "lifecycle_reason": product_intelligence.lifecycle_reason,
            "launch_date": product_intelligence.launch_date,
            "market_position": product_intelligence.market_position,
            "competitors": product_intelligence.main_competitors,
            "opportunities": product_intelligence.opportunities,
            "risks": product_intelligence.risks,
            "recommendation": product_intelligence.recommendation
        }
    
    return data
