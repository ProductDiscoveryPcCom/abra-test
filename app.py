"""
🔮 Abra Trend Hunter
Detecta tendencias de hardware antes que la competencia

PCComponentes - Product Discovery Tool
"""

import streamlit as st
import html

# Configuración de página (DEBE ser lo primero)
st.set_page_config(
    page_title="Abra Trend Hunter",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Imports
from modules.google_trends import GoogleTrendsModule, calculate_growth_rate, calculate_seasonality
from modules.related_queries import RelatedQueriesModule
from modules.serp_paa import PeopleAlsoAskModule
from modules.google_news import GoogleNewsModule
from modules.product_analysis import ProductAnalyzer
from modules.scoring import ScoringEngine
from modules.ai_analysis import AIAnalyzer, render_provider_selector
from modules.aliexpress import get_aliexpress_module, check_aliexpress_config
from modules.youtube import get_youtube_module, check_youtube_config
from modules.social_score import get_social_score_calculator
from modules.market_intelligence import get_market_intelligence, check_perplexity_config
from modules.pdf_report import generate_trend_report

from components.trend_chart import render_trend_chart, render_comparison_chart
from components.seasonality import render_seasonality_panel
from components.score_cards import render_score_cards, render_score_breakdown
from components.related_cards import render_related_queries, render_related_topics, render_competitor_brands
from components.keyword_table import render_keyword_table, render_questions_panel
from components.geo_map import render_geo_comparison, render_country_selector
from components.news_panel import render_news_panel, render_news_comparison
from components.product_matrix import render_product_section
from components.brand_scanner import render_brand_scanner, render_quick_ranking
from components.aliexpress_panel import (
    render_aliexpress_panel,
    render_aliexpress_mini,
    render_aliexpress_comparison
)
from components.social_media_panel import render_social_media_section
from components.market_intelligence_panel import (
    render_market_intelligence_panel,
    render_market_intelligence_mini,
    get_intelligence_for_pdf
)

from utils import (
    load_css, render_logo, check_api_keys, render_api_status,
    init_session_state, add_to_history, render_search_history,
    render_empty_state, render_loading_state, sanitize_html, sanitize_for_query
)


# ============================================
# UI Helper Functions
# ============================================

def section_header(title: str, icon: str, subtitle: str = "") -> None:
    """
    Renderiza un header de sección con estilo consistente
    
    Args:
        title: Título de la sección
        icon: Emoji o icono
        subtitle: Texto secundario opcional
    """
    subtitle_html = f'<span class="section-subtitle">{sanitize_html(subtitle)}</span>' if subtitle else ''
    st.markdown(f"""
    <div class="section-header">
        <span class="section-icon">{icon}</span>
        <span class="section-title">{sanitize_html(title)}</span>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def section_spacer(size: str = "normal") -> None:
    """
    Añade espaciado entre secciones (reemplaza st.markdown("---"))
    
    Args:
        size: "small", "normal", "large"
    """
    sizes = {
        "small": "section-spacer-sm",
        "normal": "section-spacer",
        "large": "section-spacer"
    }
    css_class = sizes.get(size, "section-spacer")
    st.markdown(f'<div class="{css_class}"></div>', unsafe_allow_html=True)


def preview_badge(text: str, variant: str = "gold") -> str:
    """
    Genera HTML para un badge de preview
    
    Args:
        text: Texto del badge
        variant: "gold", "purple", "success"
    
    Returns:
        HTML string del badge
    """
    variants = {
        "gold": "preview-badge",
        "purple": "preview-badge preview-badge-purple",
        "success": "preview-badge preview-badge-success"
    }
    css_class = variants.get(variant, "preview-badge")
    return f'<span class="{css_class}">{sanitize_html(text)}</span>'


def main():
    """Función principal de la aplicación"""

    # Inicializar
    load_css()
    init_session_state()

    # Sidebar
    with st.sidebar:
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

    # Verificar API key
    api_status = check_api_keys()
    if not api_status["serpapi"]:
        st.error("⚠️ SerpAPI no está configurada. Añade tu API key en los secrets.")
        st.info("Ve a Settings > Secrets y añade: SERPAPI_KEY = 'tu_api_key'")
        return

    serpapi_key = st.secrets.get("SERPAPI_KEY", "")
    geo = st.session_state.get("selected_country", "ES")

    # Renderizar según modo seleccionado
    mode = st.session_state.get("analysis_mode", "deep_dive")

    if mode == "scanner":
        # Modo Scanner: análisis masivo de marcas
        render_brand_scanner(serpapi_key, geo)
        return

    elif mode == "quick":
        # Modo Quick: ranking rápido
        render_quick_ranking(serpapi_key, geo)
        return

    # ===== MODO DEEP DIVE =====
    # Contenido principal - análisis profundo de 1 marca
    
    # Barra de búsqueda mejorada con guía de operadores
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
            max_chars=200  # Limitar longitud
        )

    with col_button:
        search_clicked = st.button("🔍 Analizar", type="primary", use_container_width=True)
    
    # Guía de operadores de búsqueda (colapsable)
    with st.expander("💡 **Sintaxis de búsqueda avanzada**", expanded=False):
        st.markdown("""
        <div class="search-syntax-guide">
            <div class="syntax-grid">
                <div class="syntax-item">
                    <code class="syntax-code">"frase exacta"</code>
                    <span class="syntax-desc">Busca la frase completa tal cual</span>
                    <span class="syntax-example">Ej: "gaming laptop"</span>
                </div>
                <div class="syntax-item">
                    <code class="syntax-code">término1 + término2</code>
                    <span class="syntax-desc">Suma el interés de ambos términos</span>
                    <span class="syntax-example">Ej: nvidia + amd</span>
                </div>
                <div class="syntax-item">
                    <code class="syntax-code">término1, término2</code>
                    <span class="syntax-desc">Compara términos lado a lado</span>
                    <span class="syntax-example">Ej: iphone, samsung</span>
                </div>
                <div class="syntax-item">
                    <code class="syntax-code">término1 - término2</code>
                    <span class="syntax-desc">Excluye el segundo término</span>
                    <span class="syntax-example">Ej: apple - fruit</span>
                </div>
            </div>
            <div class="syntax-tips">
                <p><strong>💡 Tips:</strong></p>
                <ul>
                    <li>Sin comillas = búsqueda amplia (incluye variaciones)</li>
                    <li>Con comillas = búsqueda exacta (solo esa frase)</li>
                    <li>Usa inglés para marcas internacionales</li>
                    <li>Sé específico: "RTX 4090" mejor que "nvidia gpu"</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Opciones de búsqueda (debajo de sintaxis)
    with st.expander("⚙️ **Opciones de búsqueda**", expanded=False):
        col_region, col_time, col_cat = st.columns(3)
        
        with col_region:
            region = st.selectbox(
                "🌍 Región",
                options=["ES", "PT", "FR", "IT", "DE"],
                format_func=lambda x: {
                    "ES": "🇪🇸 España",
                    "PT": "🇵🇹 Portugal",
                    "FR": "🇫🇷 Francia",
                    "IT": "🇮🇹 Italia",
                    "DE": "🇩🇪 Alemania"
                }.get(x, x),
                index=0,
                key="region_select"
            )
            st.session_state.selected_country = region
        
        with col_time:
            timeframe = st.selectbox(
                "📅 Período",
                options=[
                    "today 5-y",
                    "today 12-m",
                    "today 3-m",
                    "today 1-m"
                ],
                format_func=lambda x: {
                    "today 1-m": "Último mes",
                    "today 3-m": "3 meses",
                    "today 12-m": "1 año",
                    "today 5-y": "5 años"
                }.get(x, x),
                index=0,
                help="Zoom interactivo disponible en el gráfico",
                key="timeframe_select"
            )
            st.session_state.selected_timeframe = timeframe
        
        with col_cat:
            category = st.selectbox(
                "📂 Categoría",
                options=[0, 5, 78, 18],
                format_func=lambda x: {
                    0: "Todas",
                    5: "Informática",
                    78: "Electrónica",
                    18: "Compras"
                }.get(x, f"Cat {x}"),
                index=1,
                help="Filtrar por categoría",
                key="category_select"
            )
            st.session_state.search_category = category
        
        # Segunda fila de opciones
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            exact_match = st.checkbox(
                "🎯 Búsqueda exacta",
                value=True,
                help="Usar comillas para buscar la marca exacta",
                key="exact_match_check"
            )
            st.session_state.exact_match = exact_match
        
        with col_opt2:
            show_volume_estimate = st.checkbox(
                "📊 Volumen estimado",
                value=False,
                help="⚠️ Estimaciones aproximadas",
                key="volume_check"
            )
            st.session_state.show_volume_estimate = show_volume_estimate
        
        if show_volume_estimate:
            st.caption("⚠️ Volúmenes son ESTIMACIONES. Índice Google Trends (0-100) es el dato real.")

    # Historial de búsquedas
    history_selection = render_search_history()
    if history_selection:
        keyword = history_selection
        search_clicked = True

    # Si no hay búsqueda, mostrar estado vacío
    if not keyword or not search_clicked:
        if not st.session_state.current_keyword:
            render_empty_state()
            return
        else:
            keyword = st.session_state.current_keyword

    # Sanitizar keyword para seguridad
    keyword = sanitize_for_query(keyword)

    if not keyword:
        st.warning("Por favor, introduce un término de búsqueda válido.")
        return

    # Guardar keyword actual
    st.session_state.current_keyword = keyword
    add_to_history(keyword)

    # Análisis
    keyword_display = sanitize_html(keyword)
    st.markdown(f"## 📊 Análisis: **{keyword_display}**")

    # Inicializar módulos
    try:
        serpapi_key = st.secrets.get("SERPAPI_KEY", "")
        trends_module = GoogleTrendsModule(serpapi_key)
        related_module = RelatedQueriesModule(serpapi_key)
        paa_module = PeopleAlsoAskModule(serpapi_key)
        news_module = GoogleNewsModule(serpapi_key)
        product_analyzer = ProductAnalyzer(serpapi_key)
        scoring_engine = ScoringEngine()
        ai_analyzer = AIAnalyzer()
    except Exception as e:
        st.error(f"Error inicializando módulos: {sanitize_html(str(e))}")
        return

    # Obtener datos
    with st.spinner("🔮 Consultando Google Trends..."):
        try:
            # Obtener opciones del sidebar
            search_category = st.session_state.get("search_category", 5)  # Default: Informática
            exact_match = st.session_state.get("exact_match", True)

            trends_data = trends_module.get_interest_over_time(
                keyword=keyword,
                geo=st.session_state.selected_country,
                timeframe=st.session_state.selected_timeframe,
                category=search_category,
                exact_match=exact_match
            )

            # Mostrar info de búsqueda si usó comillas
            if trends_data.get("exact_match"):
                st.caption(f"🔍 Búsqueda: `{trends_data.get('query_used', keyword)}` | Categoría: {search_category}")

        except Exception as e:
            st.error(f"Error consultando Google Trends: {sanitize_html(str(e))}")
            return

    if not trends_data.get("success"):
        error_msg = trends_data.get('error', 'Error desconocido')
        st.error(f"Error obteniendo datos: {sanitize_html(str(error_msg))}")
        st.info("💡 Esto puede ocurrir si la marca es muy nueva o tiene poco volumen de búsqueda.")
        return

    timeline_data = trends_data.get("timeline_data", [])

    if not timeline_data:
        st.warning(f"No se encontraron datos para '{keyword_display}'.")
        st.info("💡 Prueba con otro término o verifica que la marca existe.")
        return

    # Calcular métricas (manejando valores cero)
    growth_data = calculate_growth_rate(timeline_data)
    seasonality_data = calculate_seasonality(timeline_data)

    # Obtener datos relacionados
    with st.spinner("🔍 Obteniendo búsquedas relacionadas..."):
        try:
            related_data = related_module.get_all_related(
                keyword=keyword,
                geo=st.session_state.selected_country,
                timeframe=st.session_state.selected_timeframe
            )
            
            # Enriquecer con breakout_score para comparación
            if related_data.get("success"):
                # Enriquecer queries
                queries = related_data.get("queries", {})
                if queries.get("rising"):
                    queries["rising"] = related_module.enrich_with_breakout_scores(
                        queries["rising"], is_topic=False
                    )
                
                # Enriquecer topics
                topics = related_data.get("topics", {})
                if topics.get("rising"):
                    topics["rising"] = related_module.enrich_with_breakout_scores(
                        topics["rising"], is_topic=True
                    )
                    
        except Exception as e:
            related_data = {"success": False, "queries": {"rising": [], "top": []}, "topics": {"rising": [], "top": []}}

    # Obtener PAA expandido
    with st.spinner("❓ Buscando preguntas frecuentes..."):
        try:
            paa_data = paa_module.categorize_searches(
                keyword=keyword,
                country=st.session_state.selected_country
            )
        except Exception as e:
            paa_data = {"success": False, "categorized": {"all": [], "questions": [], "comparatives": [], "others": []}}

        try:
            expanded_questions = paa_module.get_expanded_questions(
                keyword=keyword,
                country=st.session_state.selected_country,
                max_depth=2,
                max_questions=25
            )
            questions = expanded_questions.get("questions", [])
        except Exception as e:
            questions = []

    # Calcular scores (manejando valores cero)
    try:
        trend_score = scoring_engine.calculate_trend_score(
            timeline_data=timeline_data,
            related_queries_count=len(related_data.get("queries", {}).get("rising", []))
        )
    except Exception:
        trend_score = {"score": 0, "grade": "F", "factors": {}}

    try:
        potential_score = scoring_engine.calculate_potential_score(
            timeline_data=timeline_data,
            rising_queries=related_data.get("queries", {}).get("rising", []),
            current_value=growth_data.get("current_value", 0),
            is_seasonal=seasonality_data.get("is_seasonal", False)
        )
    except Exception:
        potential_score = {"score": 0, "grade": "F", "factors": {}}

    try:
        opportunity = scoring_engine.calculate_opportunity_level(
            trend_score=trend_score.get("score", 0),
            potential_score=potential_score.get("score", 0)
        )
    except Exception:
        opportunity = {"level": "MUY BAJA", "combined_score": 0, "color": "#EF4444", "icon": "❄️", "action": "No prioritario"}

    # === LAYOUT PRINCIPAL ===

    # Fila 1: Gráfico de tendencia
    st.markdown("### 📈 Tendencia temporal")
    render_trend_chart(
        timeline_data=timeline_data,
        keyword=keyword,
        show_trajectory=st.session_state.get("show_trajectory", True),
        api_key=st.secrets.get("SERPAPI_KEY", ""),
        geo=st.session_state.selected_country,
        show_volume_estimate=st.session_state.get("show_volume_estimate", True)
    )

    # Fila 2: Scores y Estacionalidad
    col_scores, col_season = st.columns([2, 1])

    with col_scores:
        st.markdown("### 🎯 Scoring")
        render_score_cards(trend_score, potential_score, opportunity)

        # Desglose de scores
        with st.expander("Ver desglose de factores"):
            col_t, col_p = st.columns(2)
            with col_t:
                render_score_breakdown(
                    "Trend Score",
                    trend_score.get("factors", {}),
                    "#F5C518"
                )
            with col_p:
                render_score_breakdown(
                    "Potential Score",
                    potential_score.get("factors", {}),
                    "#7C3AED"
                )

    with col_season:
        # Explicación IA de estacionalidad
        ai_explanation = None
        if ai_analyzer.get_available_providers():
            try:
                with st.spinner("🤖 Generando explicación..."):
                    ai_explanation = ai_analyzer.explain_seasonality(
                        seasonality_data=seasonality_data,
                        brand=keyword,
                        provider=st.session_state.ai_provider
                    )
            except Exception:
                ai_explanation = None

        render_seasonality_panel(
            seasonality_data=seasonality_data,
            ai_explanation=ai_explanation
        )

    st.markdown("---")

    # Fila 3: Related Queries y Topics
    col_queries, col_topics = st.columns(2)

    with col_queries:
        render_related_queries(
            related_data.get("queries", {}),
            country=st.session_state.selected_country
        )

    with col_topics:
        render_related_topics(related_data.get("topics", {}))

    st.markdown("---")

    # Fila 4: Análisis de Productos de la Marca
    with st.spinner("🏷️ Analizando productos de la marca..."):
        try:
            # Combinar queries rising y top para detección
            all_related_queries = (
                related_data.get("queries", {}).get("rising", []) +
                related_data.get("queries", {}).get("top", [])
            )

            product_analysis = product_analyzer.full_analysis(
                brand=keyword,
                related_queries=all_related_queries,
                geo=st.session_state.selected_country,
                timeframe=st.session_state.selected_timeframe
            )
        except Exception as e:
            product_analysis = {"success": False, "products": [], "classified": {}, "insights": {}}

    render_product_section(product_analysis, keyword)

    st.markdown("---")

    # Fila 4.5: Social Media Intelligence (YouTube Deep Dive)
    with st.expander("📺 YouTube Deep Dive", expanded=False):
        youtube_data = None
        youtube_metrics = None
        youtube_deep_dive = None
        tiktok_metrics = None
        social_metrics = None

        # Verificar configuración de YouTube
        yt_config = check_youtube_config()

        if not yt_config.get("configured"):
            st.info("""
            **YouTube no está configurado.**

            Para activar análisis de YouTube, añade tu API key en `secrets.toml`:
            ```
            YOUTUBE_API_KEY = "AIzaSy..."
            ```

            Obtén tu API key en [Google Cloud Console](https://console.cloud.google.com):
            1. Crear proyecto
            2. Habilitar "YouTube Data API v3"
            3. Crear credenciales > API Key
            """)
        else:
            with st.spinner("🔍 Analizando YouTube (Deep Dive)..."):
                try:
                    yt_module = get_youtube_module()
                    if yt_module:
                        # Deep Dive Analysis (incluye sentimiento, marcas, idiomas)
                        youtube_deep_dive = yt_module.deep_dive_analysis(
                            brand=keyword,
                            geo=st.session_state.selected_country,
                            max_videos=50
                        )
                        
                        # También obtener métricas básicas para compatibilidad
                        if youtube_deep_dive and youtube_deep_dive.videos_by_type:
                            youtube_data = youtube_deep_dive.videos_by_type
                            youtube_metrics = yt_module.calculate_metrics(keyword, youtube_data)

                        # Mostrar error de API si lo hubo
                        if youtube_metrics and youtube_metrics.api_error:
                            st.warning(f"⚠️ API: {youtube_metrics.api_error}")

                except Exception as e:
                    st.warning(f"Error consultando YouTube: {sanitize_html(str(e))}")

        # Renderizar Deep Dive si hay datos
        if youtube_deep_dive and youtube_deep_dive.total_videos_analyzed > 0:
            from components.youtube_panel import render_youtube_deep_dive
            render_youtube_deep_dive(
                keyword=keyword,
                deep_dive=youtube_deep_dive,
                metrics=youtube_metrics
            )
        elif youtube_data and youtube_metrics:
            # Fallback a panel básico
            from components.youtube_panel import render_youtube_panel
            render_youtube_panel(
                keyword=keyword,
                videos_by_type=youtube_data,
                metrics=youtube_metrics
            )

        # Calcular Social Score (funciona incluso sin datos)
        try:
            current_index = growth_data.get("current_value", 0)
            calculator = get_social_score_calculator()
            social_metrics = calculator.calculate(
                keyword=keyword,
                youtube_metrics=youtube_metrics,
                tiktok_metrics=tiktok_metrics,
                trends_score=current_index
            )

            # Solo mostrar score si hay YouTube configurado pero sin datos aún
            if not youtube_deep_dive and not youtube_data and yt_config.get("configured"):
                render_social_media_section(
                    keyword=keyword,
                    youtube_data=youtube_data,
                    youtube_metrics=youtube_metrics,
                    tiktok_data=None,
                    tiktok_metrics=tiktok_metrics,
                    social_metrics=social_metrics,
                    trends_score=current_index
                )

        except Exception as e:
            st.warning(f"Error calculando Social Score: {sanitize_html(str(e))}")

    st.markdown("---")

    # Fila 4.6: Market Intelligence (Perplexity)
    market_analysis = None
    product_intelligence = None

    with st.expander("🧠 Inteligencia de Mercado (Perplexity)", expanded=False):
        pplx_config = check_perplexity_config()

        if not pplx_config.get("configured"):
            st.info("""
            **Perplexity no está configurado.**

            Para activar análisis de mercado inteligente, añade tu API key en `secrets.toml`:
            ```
            PERPLEXITY_API_KEY = "pplx-xxxx..."
            ```

            Obtén tu API key en [Perplexity Settings](https://www.perplexity.ai/settings/api)

            **Perplexity proporciona:**
            - 🎯 Ciclo de vida REAL del producto (no estimaciones)
            - 💬 Sentimiento del mercado basado en reviews
            - ⚔️ Análisis competitivo actualizado
            - 💡 Oportunidades y amenazas
            """)
        else:
            with st.spinner("Analizando mercado con Perplexity..."):
                try:
                    mi_module = get_market_intelligence()
                    if mi_module:
                        # Análisis completo del producto/marca
                        product_intelligence = mi_module.analyze_product_complete(
                            product_name=keyword,
                            brand="",
                            include_competitors=True
                        )

                        # Análisis de mercado
                        market_analysis = mi_module.analyze_market(
                            brand=keyword,
                            category="tecnología",
                            geo="España" if st.session_state.selected_country == "ES" else st.session_state.selected_country
                        )

                        # Renderizar panel completo
                        render_market_intelligence_panel(
                            keyword=keyword,
                            market_analysis=market_analysis,
                            product_intelligence=product_intelligence
                        )

                except Exception as e:
                    st.warning(f"Error en análisis de mercado: {sanitize_html(str(e))}")

    st.markdown("---")

    # Fila 4.7: AliExpress (si está configurado)
    ali_config = check_aliexpress_config()
    if ali_config["has_key"] and ali_config["has_secret"]:
        with st.expander("🛒 Datos de AliExpress", expanded=False):
            with st.spinner("Consultando AliExpress..."):
                try:
                    ali_module = get_aliexpress_module()
                    if ali_module:
                        # Buscar productos
                        ali_products = ali_module.search_products(keyword, max_results=50)
                        ali_hotproducts = ali_module.get_hotproducts(keyword, max_results=20)

                        # Calcular métricas
                        ali_metrics = ali_module.calculate_metrics(keyword, ali_products)

                        # Renderizar panel
                        render_aliexpress_panel(keyword, ali_products, ali_hotproducts, ali_metrics)

                        # Comparativa con Google Trends
                        current_index = growth_data.get("current_value", 0)
                        render_aliexpress_comparison(keyword, current_index, ali_metrics)
                except Exception as e:
                    st.warning(f"No se pudo obtener datos de AliExpress: {sanitize_html(str(e))}")
    else:
        with st.expander("🛒 AliExpress (no configurado)", expanded=False):
            st.info("""
            **AliExpress no está configurado.**

            Para activar datos de AliExpress, añade estas claves en `secrets.toml`:
            ```
            ALIEXPRESS_KEY = "tu_app_key"
            ALIEXPRESS_SECRET = "tu_app_secret"
            ```

            Obtén tus credenciales en [AliExpress Open Platform](https://portals.aliexpress.com/)
            """)

    st.markdown("---")

    # Fila 5: Keywords y Preguntas
    col_keywords, col_questions = st.columns([2, 1])

    with col_keywords:
        render_keyword_table(paa_data)

    with col_questions:
        render_questions_panel(questions)

    st.markdown("---")

    # Fila 6: Análisis IA
    if ai_analyzer.get_available_providers():
        st.markdown("### 🤖 Análisis IA")

        try:
            with st.spinner(f"Generando análisis con {st.session_state.ai_provider}..."):
                # Preparar datos para el análisis
                analysis_data = {
                    "keyword": keyword,
                    "current_value": growth_data.get("current_value", 0),
                    "growth_rate": growth_data.get("growth_rate", 0),
                    "trend_score": trend_score.get("score", 0),
                    "potential_score": potential_score.get("score", 0),
                    "is_seasonal": seasonality_data.get("is_seasonal", False),
                    "rising_queries": related_data.get("queries", {}).get("rising", [])[:5],
                    "questions": [q.get("question", "") for q in questions[:5] if isinstance(q, dict)]
                }

                ai_result = ai_analyzer.analyze(
                    trend_data=analysis_data,
                    provider=st.session_state.ai_provider
                )

            if ai_result.get("success"):
                # Análisis principal - sanitizar contenido de IA
                analysis_text = sanitize_html(ai_result.get("analysis", "No se pudo generar el análisis"))
                provider_name = sanitize_html(ai_result.get("provider", "IA"))

                st.markdown(
                    f'''
                    <div style="background: linear-gradient(135deg, #EDE9FE 0%, #FFFFFF 100%);
                    border-radius: 12px; padding: 24px; border-left: 4px solid #7C3AED;
                    margin-bottom: 16px;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                            <span style="font-size: 1.25rem;">🧠</span>
                            <span style="font-weight: 600; color: #5B21B6;">
                                Análisis ({provider_name})
                            </span>
                        </div>
                        <div style="color: #374151; line-height: 1.6;">
                            {analysis_text}
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

                # Ideas de blog
                blog_ideas = ai_result.get("blog_ideas", [])
                if blog_ideas:
                    st.markdown("#### 📝 Ideas para el blog")

                    for i, idea in enumerate(blog_ideas[:5]):
                        if not isinstance(idea, dict):
                            continue
                        titulo = sanitize_html(idea.get('titulo', f'Idea {i+1}'))
                        with st.expander(f"💡 {titulo}"):
                            enfoque = sanitize_html(idea.get('enfoque', 'N/A'))
                            st.markdown(f"**Enfoque:** {enfoque}")
                            keywords = idea.get('keywords_objetivo', [])
                            if keywords and isinstance(keywords, list):
                                keywords_safe = [sanitize_html(str(k)) for k in keywords[:10]]
                                st.markdown(f"**Keywords:** {', '.join(keywords_safe)}")
            else:
                error_msg = sanitize_html(ai_result.get('error', 'Error desconocido'))
                st.warning(f"No se pudo generar el análisis: {error_msg}")
        except Exception as e:
            st.warning(f"Error en análisis IA: {sanitize_html(str(e))}")

    st.markdown("---")

    # Fila 7: Noticias relacionadas
    st.markdown("### 📰 Noticias Relacionadas")

    try:
        with st.spinner("Buscando noticias..."):
            news_data = news_module.search_news(
                query=keyword,
                country=st.session_state.selected_country
            )

        if news_data.get("success") and news_data.get("news"):
            # Analizar sentimiento
            sentiment = news_module.analyze_news_sentiment(news_data.get("news", []))

            render_news_panel(
                news=news_data.get("news", []),
                title=f"📰 Noticias sobre {keyword_display}",
                max_display=6,
                show_sentiment=True,
                sentiment_data=sentiment
            )
        else:
            st.info(f"No se encontraron noticias recientes sobre '{keyword_display}'")
    except Exception as e:
        st.info(f"No se pudieron cargar las noticias")

    st.markdown("---")

    # Fila 8: Comparativa por países
    st.markdown("### 🌍 Comparativa por países")

    compare_countries = st.checkbox("Comparar con otros países", value=False)

    if compare_countries:
        try:
            with st.spinner("Obteniendo datos por país..."):
                country_data = trends_module.get_multi_country_data(
                    keyword=keyword,
                    countries=["ES", "PT", "FR", "IT", "DE"],
                    timeframe=st.session_state.selected_timeframe
                )

            render_geo_comparison(
                country_data=country_data.get("countries", {}),
                keyword=keyword
            )

            # Gráfico comparativo
            render_comparison_chart(
                data_by_country=country_data.get("countries", {}),
                keyword=keyword
            )
        except Exception as e:
            st.warning("No se pudieron cargar los datos de comparativa por países")

    st.markdown("---")

    # Fila 9: Exportar a PDF
    st.markdown("### 📄 Exportar Informe")

    col_pdf1, col_pdf2, col_pdf3 = st.columns([1, 2, 1])

    with col_pdf2:
        if st.button("📥 Descargar Informe PDF", type="primary", use_container_width=True):
            with st.spinner("Generando informe PDF..."):
                try:
                    # Preparar datos para el PDF
                    pdf_data = {
                        "trend_score": trend_score.get("score", 0),
                        "potential_score": potential_score.get("score", 0),
                        "growth_rate": growth_data.get("growth_rate", 0),
                        "current_value": growth_data.get("current_value", 0),
                        "trend_values": [p.get("value", 0) for p in timeline_data] if timeline_data else [],
                        "trend_dates": [p.get("date", "") for p in timeline_data] if timeline_data else [],
                        "growth_data": growth_data,
                        "seasonality_data": seasonality_data,
                        "rising_queries": related_data.get("queries", {}).get("rising", []),
                        "top_queries": related_data.get("queries", {}).get("top", []),
                        "products": [],  # Se podría añadir productos analizados
                        "ai_recommendation": ""
                    }

                    # Añadir datos de Market Intelligence si existen
                    if market_analysis or product_intelligence:
                        intel_data = get_intelligence_for_pdf(market_analysis, product_intelligence)
                        pdf_data["market_intelligence"] = intel_data.get("market_intelligence", {})
                        pdf_data["sentiment_data"] = intel_data.get("sentiment_data", {})

                    # Generar PDF
                    pdf_bytes = generate_trend_report(keyword, pdf_data)

                    # Botón de descarga
                    st.download_button(
                        label="💾 Guardar PDF",
                        data=pdf_bytes,
                        file_name=f"trend_report_{keyword.replace(' ', '_')}_{st.session_state.selected_country}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )

                    st.success("✅ Informe generado correctamente")

                except Exception as e:
                    st.error(f"Error generando PDF: {sanitize_html(str(e))}")

        st.caption("El informe incluye: tendencias, scores, búsquedas relacionadas, estacionalidad e inteligencia de mercado (si Perplexity está configurado).")


if __name__ == "__main__":
    main()

