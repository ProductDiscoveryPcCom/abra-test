"""
UI Sections - Secciones de la interfaz de Abra Trend Hunter

Este módulo contiene las funciones de renderizado para cada sección
de la aplicación, extraídas de main() para mejor mantenibilidad.
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from utils import sanitize_html, sanitize_for_query


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class AnalysisContext:
    """Contexto compartido entre secciones de análisis"""
    keyword: str
    serpapi_key: str
    geo: str
    timeframe: str
    
    # Datos obtenidos
    trends_data: Dict = None
    timeline_data: List = None
    growth_data: Dict = None
    seasonality_data: Dict = None
    related_data: Dict = None
    paa_data: Dict = None
    questions: List = None
    
    # Scores calculados
    trend_score: Dict = None
    potential_score: Dict = None
    opportunity: Dict = None
    
    # Módulos
    trends_module: Any = None
    related_module: Any = None
    paa_module: Any = None
    news_module: Any = None
    product_analyzer: Any = None
    scoring_engine: Any = None
    ai_analyzer: Any = None


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar_config() -> Dict[str, Any]:
    """
    Renderiza la configuración del sidebar.
    
    Returns:
        Dict con la configuración seleccionada
    """
    from utils import render_logo, render_api_status
    from modules.ai_analysis import render_provider_selector
    
    render_logo()
    st.markdown("---")

    # Selector de modo
    st.markdown("#### 🎯 Modo de Análisis")
    mode = st.radio(
        "Selecciona modo",
        options=["deep_dive", "scanner", "quick"],
        format_func=lambda x: {
            "deep_dive": "🔬 Deep Dive (1 marca)",
            "scanner": "🚀 Scanner (CSV)",
            "quick": "⚡ Quick Ranking"
        }.get(x),
        label_visibility="collapsed",
        key="analysis_mode"
    )

    st.markdown("---")

    # Selector de IA
    st.markdown("#### 🤖 Proveedor IA")
    ai_provider = render_provider_selector()
    st.session_state.ai_provider = ai_provider

    st.markdown("---")

    # Estado de APIs
    render_api_status()

    st.markdown("---")
    st.markdown(
        '<p style="font-size: 0.75rem; color: #9CA3AF; text-align: center;">'
        'Abra Trend Hunter v1.0<br>PCComponentes Product Discovery</p>',
        unsafe_allow_html=True
    )
    
    return {
        "mode": mode,
        "ai_provider": ai_provider
    }


# =============================================================================
# SEARCH BAR
# =============================================================================

def render_search_bar() -> tuple[str, bool]:
    """
    Renderiza la barra de búsqueda con opciones avanzadas.
    
    Returns:
        Tuple (keyword, search_clicked)
    """
    from utils import render_search_history
    
    # Header de búsqueda
    st.markdown("""
    <div class="search-container">
        <div class="search-header">
            <span class="search-icon">🔍</span>
            <span class="search-title">Buscar tendencias</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col_search, col_button = st.columns([4, 1])

    with col_search:
        keyword = st.text_input(
            "Buscar marca o producto",
            placeholder="Ej: RTX 5090, Framework Laptop, Steam Deck...",
            label_visibility="collapsed",
            key="search_input",
            max_chars=200
        )

    with col_button:
        search_clicked = st.button("🔍 Analizar", type="primary", use_container_width=True)
    
    # Guía de sintaxis
    with st.expander("💡 **Sintaxis de búsqueda avanzada**", expanded=False):
        st.markdown("""
        | Sintaxis | Descripción | Ejemplo |
        |----------|-------------|---------|
        | `"frase"` | Búsqueda exacta | `"gaming laptop"` |
        | `a + b` | Suma interés | `nvidia + amd` |
        | `a, b` | Comparar | `iphone, samsung` |
        | `a - b` | Excluir | `apple - fruit` |
        """)
    
    # Historial
    history_selection = render_search_history()
    if history_selection:
        keyword = history_selection
        search_clicked = True
    
    return keyword, search_clicked


def render_search_options() -> Dict[str, Any]:
    """
    Renderiza las opciones avanzadas de búsqueda.
    
    Returns:
        Dict con las opciones seleccionadas
    """
    with st.expander("⚙️ **Opciones de búsqueda**", expanded=False):
        col_region, col_time, col_cat = st.columns(3)
        
        with col_region:
            countries = {
                "ES": "🇪🇸 España",
                "PT": "🇵🇹 Portugal",
                "FR": "🇫🇷 Francia",
                "IT": "🇮🇹 Italia",
                "DE": "🇩🇪 Alemania",
                "US": "🇺🇸 Estados Unidos",
                "GB": "🇬🇧 Reino Unido",
                "": "🌍 Global"
            }
            selected_country = st.selectbox(
                "País",
                options=list(countries.keys()),
                format_func=lambda x: countries.get(x, x),
                index=0,
                key="selected_country"
            )

        with col_time:
            timeframes = {
                "today 3-m": "Últimos 90 días",
                "today 12-m": "Último año",
                "today 5-y": "Últimos 5 años"
            }
            selected_timeframe = st.selectbox(
                "Periodo",
                options=list(timeframes.keys()),
                format_func=lambda x: timeframes.get(x, x),
                index=1,
                key="selected_timeframe"
            )

        with col_cat:
            categories = {
                0: "🌐 Todas",
                5: "💻 Informática",
                7: "🎮 Juegos",
                174: "🛒 Compras"
            }
            search_category = st.selectbox(
                "Categoría",
                options=list(categories.keys()),
                format_func=lambda x: categories.get(x, str(x)),
                index=1,
                key="search_category"
            )
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            exact_match = st.checkbox(
                '🎯 Usar comillas (búsqueda exacta)',
                value=True,
                key="exact_match",
                help="Busca la frase exacta en lugar de variaciones"
            )
        with col_opt2:
            show_volume = st.checkbox(
                "📊 Estimar volumen de búsqueda",
                value=False,
                key="show_volume_estimate"
            )
    
    return {
        "country": selected_country,
        "timeframe": selected_timeframe,
        "category": search_category,
        "exact_match": exact_match,
        "show_volume": show_volume
    }


# =============================================================================
# TREND OVERVIEW
# =============================================================================

def render_trend_overview(ctx: AnalysisContext) -> None:
    """Renderiza el gráfico de tendencia y scores principales"""
    from components.trend_chart import render_trend_chart
    from components.score_cards import render_score_cards, render_score_breakdown
    from components.seasonality import render_seasonality_panel
    
    st.markdown("### 📈 Tendencia temporal")
    render_trend_chart(
        timeline_data=ctx.timeline_data,
        keyword=ctx.keyword,
        show_trajectory=st.session_state.get("show_trajectory", True),
        show_predictions=st.session_state.get("show_predictions", False)
    )
    
    # Scores y estacionalidad
    col_scores, col_season = st.columns([2, 1])
    
    with col_scores:
        render_score_cards(ctx.trend_score, ctx.potential_score, ctx.opportunity)
        
        with st.expander("Ver desglose de factores"):
            col_t, col_p = st.columns(2)
            with col_t:
                render_score_breakdown(
                    ctx.trend_score.get("factors", {}),
                    "Trend Score"
                )
            with col_p:
                render_score_breakdown(
                    ctx.potential_score.get("factors", {}),
                    "Potential Score"
                )
    
    with col_season:
        if ctx.seasonality_data:
            render_seasonality_panel(
                seasonality_data=ctx.seasonality_data,
                keyword=ctx.keyword,
                ai_analyzer=ctx.ai_analyzer
            )


# =============================================================================
# RELATED QUERIES & TOPICS
# =============================================================================

def render_related_section(ctx: AnalysisContext) -> None:
    """Renderiza queries y topics relacionados"""
    from components.related_cards import render_related_queries, render_related_topics
    
    st.markdown("### 🔍 Búsquedas relacionadas")
    
    col_queries, col_topics = st.columns(2)
    
    with col_queries:
        render_related_queries(
            queries=ctx.related_data.get("queries", {}),
            main_keyword=ctx.keyword
        )
    
    with col_topics:
        render_related_topics(ctx.related_data.get("topics", {}))


# =============================================================================
# PRODUCTS SECTION
# =============================================================================

def render_products_section(ctx: AnalysisContext) -> None:
    """Renderiza análisis de productos"""
    from components.product_matrix import render_product_section
    
    st.markdown("### 📦 Productos detectados")
    
    try:
        product_analysis = ctx.product_analyzer.full_analysis(
            brand=ctx.keyword,
            geo=ctx.geo,
            timeframe=ctx.timeframe
        )
        render_product_section(product_analysis, ctx.keyword)
    except Exception as e:
        st.warning(f"No se pudo analizar productos: {str(e)}")


# =============================================================================
# YOUTUBE SECTION
# =============================================================================

def render_youtube_section(ctx: AnalysisContext) -> None:
    """Renderiza sección de YouTube Deep Dive"""
    from modules.youtube import get_youtube_module, check_youtube_config
    
    with st.expander("📺 YouTube Deep Dive", expanded=False):
        youtube_configured, yt_message = check_youtube_config()
        
        if youtube_configured:
            youtube_module = get_youtube_module()
            
            if youtube_module:
                with st.spinner("🎬 Analizando videos de YouTube..."):
                    try:
                        deep_dive = youtube_module.deep_dive_analysis(
                            keyword=ctx.keyword,
                            max_results=50,
                            days_back=90
                        )
                        
                        if deep_dive and deep_dive.videos_analyzed > 0:
                            from components.youtube_panel import render_youtube_deep_dive
                            render_youtube_deep_dive(
                                deep_dive=deep_dive,
                                keyword=ctx.keyword
                            )
                        else:
                            st.info("No se encontraron videos recientes para esta búsqueda")
                    except Exception as e:
                        st.error(f"Error en YouTube: {str(e)}")
            else:
                st.warning(yt_message)
        else:
            st.info("🔑 Configura YouTube API en secrets para habilitar esta sección")


# =============================================================================
# SOCIAL MEDIA SECTION
# =============================================================================

def render_social_section(ctx: AnalysisContext) -> None:
    """Renderiza sección de redes sociales"""
    from components.social_media_panel import render_social_media_section
    
    with st.expander("📱 Redes Sociales", expanded=False):
        try:
            render_social_media_section(
                keyword=ctx.keyword,
                serpapi_key=ctx.serpapi_key,
                geo=ctx.geo
            )
        except Exception as e:
            st.warning(f"Error en redes sociales: {str(e)}")


# =============================================================================
# MARKET INTELLIGENCE
# =============================================================================

def render_intelligence_section(ctx: AnalysisContext) -> None:
    """Renderiza inteligencia de mercado con Perplexity"""
    from modules.market_intelligence import check_perplexity_config, get_market_intelligence
    from components.market_intelligence_panel import render_market_intelligence_panel
    
    with st.expander("🧠 Inteligencia de Mercado (Perplexity)", expanded=False):
        perplexity_configured, pplx_msg = check_perplexity_config()
        
        if perplexity_configured:
            if st.button("🔍 Analizar mercado", key="btn_intelligence"):
                with st.spinner("🧠 Analizando mercado con IA..."):
                    try:
                        intelligence = get_market_intelligence()
                        if intelligence:
                            analysis = intelligence.analyze_product_complete(ctx.keyword)
                            if analysis.get("success"):
                                render_market_intelligence_panel(
                                    keyword=ctx.keyword,
                                    analysis=analysis
                                )
                            else:
                                st.error("No se pudo obtener análisis")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        else:
            st.info("🔑 Configura PERPLEXITY_API_KEY para habilitar")


# =============================================================================
# ALIEXPRESS SECTION
# =============================================================================

def render_aliexpress_section(ctx: AnalysisContext) -> None:
    """Renderiza sección de AliExpress"""
    from modules.aliexpress import check_aliexpress_config, get_aliexpress_module
    from components.aliexpress_panel import render_aliexpress_panel
    
    aliexpress_configured, ali_msg = check_aliexpress_config()
    
    if aliexpress_configured:
        with st.expander("🛒 Datos de AliExpress", expanded=False):
            aliexpress = get_aliexpress_module()
            if aliexpress:
                with st.spinner("🛒 Obteniendo datos de AliExpress..."):
                    try:
                        ali_data = aliexpress.search_products(ctx.keyword, max_results=20)
                        if ali_data.get("success"):
                            render_aliexpress_panel(
                                ctx.keyword,
                                ali_data.get("products", []),
                                ali_data.get("hot_products", []),
                                ali_data.get("metrics", {})
                            )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    else:
        with st.expander("🛒 AliExpress (no configurado)", expanded=False):
            st.info("🔑 Configura las claves de AliExpress para habilitar")


# =============================================================================
# KEYWORDS & QUESTIONS
# =============================================================================

def render_keywords_section(ctx: AnalysisContext) -> None:
    """Renderiza keywords y preguntas frecuentes"""
    from components.keyword_table import render_keyword_table, render_questions_panel
    
    st.markdown("### 🔤 Keywords y Preguntas")
    
    col_keywords, col_questions = st.columns([2, 1])
    
    with col_keywords:
        render_keyword_table(ctx.paa_data)
    
    with col_questions:
        render_questions_panel(ctx.questions)


# =============================================================================
# NEWS SECTION
# =============================================================================

def render_news_section(ctx: AnalysisContext) -> None:
    """Renderiza sección de noticias"""
    from components.news_panel import render_news_panel
    
    with st.expander("📰 Noticias recientes", expanded=False):
        try:
            news_data = ctx.news_module.get_news(ctx.keyword)
            if news_data.get("success"):
                render_news_panel(
                    news=news_data.get("articles", []),
                    keyword=ctx.keyword,
                    ai_analyzer=ctx.ai_analyzer
                )
            else:
                st.info("No se encontraron noticias recientes")
        except Exception as e:
            st.warning(f"Error obteniendo noticias: {str(e)}")


# =============================================================================
# GEO SECTION
# =============================================================================

def render_geo_section(ctx: AnalysisContext) -> None:
    """Renderiza comparación geográfica"""
    from components.geo_map import render_geo_comparison
    from components.trend_chart import render_comparison_chart
    
    with st.expander("🌍 Comparación geográfica", expanded=False):
        try:
            geo_data = ctx.trends_module.get_interest_by_region(
                keyword=ctx.keyword,
                geo="",  # Global
                resolution="COUNTRY"
            )
            
            if geo_data.get("success"):
                render_geo_comparison(
                    geo_data.get("regions", []),
                    ctx.keyword
                )
                
                # Comparativa PCComponentes markets
                render_comparison_chart(
                    keyword=ctx.keyword,
                    countries=["ES", "PT", "FR", "IT", "DE"],
                    trends_module=ctx.trends_module
                )
        except Exception as e:
            st.warning(f"Error en datos geográficos: {str(e)}")


# =============================================================================
# EXPORT SECTION
# =============================================================================

def render_export_section(ctx: AnalysisContext) -> None:
    """Renderiza opciones de exportación"""
    from modules.pdf_report import generate_trend_report
    
    st.markdown("### 📥 Exportar informe")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📄 Generar PDF", type="primary", use_container_width=True):
            with st.spinner("Generando informe PDF..."):
                try:
                    pdf_bytes = generate_trend_report(
                        keyword=ctx.keyword,
                        trends_data=ctx.trends_data,
                        timeline_data=ctx.timeline_data,
                        growth_data=ctx.growth_data,
                        seasonality_data=ctx.seasonality_data,
                        trend_score=ctx.trend_score,
                        potential_score=ctx.potential_score,
                        opportunity=ctx.opportunity,
                        related_data=ctx.related_data,
                        paa_data=ctx.paa_data
                    )
                    
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"trend_report_{ctx.keyword.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error generando PDF: {str(e)}")
