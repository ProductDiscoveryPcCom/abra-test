"""
YouTube Panel - Product Discovery Focused
Análisis orientado a detectar oportunidades de producto:
- Productos mencionados dinámicamente
- Alternativas económicas
- Señales de intención de compra
- Hype y timing
- Cobertura de mercados objetivo
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Any, Dict, List
import pandas as pd

from utils.helpers import format_number, sanitize_html


def render_youtube_deep_dive(
    keyword: str,
    deep_dive: Any,
    metrics: Any = None
) -> None:
    """
    Renderiza el panel de YouTube orientado a Product Discovery
    """
    if not deep_dive or deep_dive.total_videos_analyzed == 0:
        st.info("No se encontraron videos en YouTube para este término.")
        return
    
    # Header con métricas clave
    _render_header_metrics(deep_dive)
    
    st.markdown("---")
    
    # Tabs orientados a decisión de producto
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Oportunidad",
        "📦 Productos",
        "🛒 Intención Compra",
        "🌍 Mercados",
        "📹 Videos"
    ])
    
    with tab1:
        _render_opportunity_tab(deep_dive)
    
    with tab2:
        _render_products_tab(deep_dive)
    
    with tab3:
        _render_buying_intent_tab(deep_dive)
    
    with tab4:
        _render_markets_tab(deep_dive)
    
    with tab5:
        _render_videos_tab(deep_dive)


def _render_header_metrics(deep_dive: Any) -> None:
    """Métricas principales con enfoque en oportunidad"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        # Product Opportunity Score
        score = deep_dive.product_opportunity_score
        if score >= 70:
            st.success(f"🎯 **{score}**/100")
            st.caption("Oportunidad ALTA")
        elif score >= 40:
            st.warning(f"📊 **{score}**/100")
            st.caption("Oportunidad MEDIA")
        else:
            st.info(f"📉 **{score}**/100")
            st.caption("Oportunidad BAJA")
    
    with col2:
        st.metric("Videos", f"{deep_dive.total_videos_analyzed}")
    
    with col3:
        st.metric("Vistas totales", format_number(deep_dive.total_views))
    
    with col4:
        # Hype
        if deep_dive.hype:
            hype_icons = {
                "exploding": "🚀",
                "hot": "🔥",
                "warm": "🌡️",
                "cooling": "❄️",
                "cold": "🧊"
            }
            icon = hype_icons.get(deep_dive.hype.hype_trend, "❓")
            st.metric(f"{icon} Hype", f"{deep_dive.hype.hype_score}/100")
        else:
            st.metric("Hype", "N/A")
    
    with col5:
        # Intención de compra
        if deep_dive.buying_intent:
            intent = deep_dive.buying_intent.total_signals
            if intent >= 5:
                st.success(f"🛒 {intent} señales")
            elif intent >= 2:
                st.warning(f"🛒 {intent} señales")
            else:
                st.info(f"🛒 {intent} señales")
        else:
            st.info("🛒 0 señales")


def _render_opportunity_tab(deep_dive: Any) -> None:
    """Tab de análisis de oportunidad"""
    st.markdown("### 🎯 Análisis de Oportunidad de Producto")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Hype Metrics
        st.markdown("#### 📈 Hype del Producto")
        
        if deep_dive.hype:
            hype = deep_dive.hype
            
            # Gauge de hype
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=hype.hype_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Hype Score"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': "#7C3AED"},
                    'steps': [
                        {'range': [0, 30], 'color': "#E5E7EB"},
                        {'range': [30, 60], 'color': "#FEF3C7"},
                        {'range': [60, 100], 'color': "#D1FAE5"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 70
                    }
                }
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
            # Detalles de hype
            st.markdown(f"""
            - **Videos/semana:** {hype.videos_per_week:.1f}
            - **Semanas desde 1er video:** {hype.weeks_since_first}
            - **Tendencia:** {hype.hype_trend.upper()}
            """)
            
            # Interpretación
            if hype.hype_trend == "exploding":
                st.success("🚀 **PRODUCTO EXPLOTANDO** - Máxima prioridad de análisis")
            elif hype.hype_trend == "hot":
                st.warning("🔥 **PRODUCTO CALIENTE** - Alta actividad de contenido")
            elif hype.hype_trend == "warm":
                st.info("🌡️ **PRODUCTO TIBIO** - Actividad moderada")
            else:
                st.caption("❄️ Producto con baja actividad reciente")
        else:
            st.info("No hay datos suficientes para calcular hype")
    
    with col2:
        # Timeline
        st.markdown("#### 📅 Timeline de Contenido")
        
        if deep_dive.timeline:
            df = pd.DataFrame([
                {"Mes": month, "Videos": count}
                for month, count in sorted(deep_dive.timeline.items())
            ])
            
            fig = px.area(df, x="Mes", y="Videos")
            fig.update_traces(fill='tozeroy', line_color='#7C3AED')
            fig.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Tendencia
            if deep_dive.growth_trend == "growing":
                st.success("📈 Contenido en CRECIMIENTO")
            elif deep_dive.growth_trend == "declining":
                st.warning("📉 Contenido en DECLIVE")
            else:
                st.info("📊 Contenido ESTABLE")
        else:
            st.info("No hay datos de timeline")
    
    # Resumen de oportunidad
    st.markdown("---")
    st.markdown("#### 💡 Resumen de Oportunidad")
    
    _render_opportunity_summary(deep_dive)


def _render_opportunity_summary(deep_dive: Any) -> None:
    """Genera un resumen accionable"""
    signals = []
    
    # Señales positivas
    if deep_dive.hype and deep_dive.hype.hype_score >= 60:
        signals.append(("✅", "Alto hype - producto con tracción"))
    
    if deep_dive.buying_intent and deep_dive.buying_intent.where_to_buy >= 2:
        signals.append(("✅", f"Demanda activa - {deep_dive.buying_intent.where_to_buy} videos preguntan dónde comprar"))
    
    if deep_dive.buying_intent and deep_dive.buying_intent.europe_mentions >= 1:
        signals.append(("✅", "Menciones de Europa/España - mercado relevante"))
    
    if deep_dive.budget_alternatives:
        signals.append(("✅", f"Nicho activo - {len(deep_dive.budget_alternatives)} alternativas budget detectadas"))
    
    # Señales de mercado
    target_langs = ["es", "pt", "fr", "it", "de"]
    covered = sum(1 for lang in deep_dive.languages if lang.language in target_langs)
    if covered >= 3:
        signals.append(("✅", f"Cobertura multi-mercado - {covered} idiomas objetivo"))
    elif covered >= 1:
        signals.append(("⚠️", f"Cobertura limitada - solo {covered} idioma(s) objetivo"))
    else:
        signals.append(("❌", "Sin cobertura de mercados objetivo"))
    
    # Señales negativas
    if deep_dive.content_freshness in ["aging", "stale"]:
        signals.append(("⚠️", "Contenido envejeciendo - puede ser producto en declive"))
    
    if not deep_dive.buying_intent or deep_dive.buying_intent.total_signals == 0:
        signals.append(("⚠️", "Sin señales de intención de compra"))
    
    # Renderizar
    for icon, text in signals:
        st.markdown(f"{icon} {text}")


def _render_products_tab(deep_dive: Any) -> None:
    """Tab de productos detectados"""
    st.markdown("### 📦 Productos Mencionados")
    st.caption("Detectados dinámicamente de títulos y descripciones (no lista predefinida)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 Productos en Videos")
        
        if deep_dive.products_mentioned:
            for i, product in enumerate(deep_dive.products_mentioned[:10], 1):
                views_fmt = format_number(product.total_views)
                
                st.markdown(f"""
                <div style="padding: 10px; margin: 5px 0; background: #F3F4F6; 
                     border-radius: 8px; border-left: 3px solid #7C3AED;">
                    <strong>{i}. {sanitize_html(product.name)}</strong><br>
                    <small>📹 {product.mention_count} videos · 👁️ {views_fmt} vistas</small>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No se detectaron productos específicos")
    
    with col2:
        st.markdown("#### 💰 Alternativas Económicas")
        st.caption("Mencionados como 'budget', 'affordable', 'best value'...")
        
        if deep_dive.budget_alternatives:
            for product in deep_dive.budget_alternatives[:8]:
                views_fmt = format_number(product.total_views)
                
                st.markdown(f"""
                <div style="padding: 10px; margin: 5px 0; background: #D1FAE5; 
                     border-radius: 8px; border-left: 3px solid #10B981;">
                    <strong>💵 {sanitize_html(product.name)}</strong><br>
                    <small>📹 {product.mention_count} videos · 👁️ {views_fmt} vistas</small>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.success(f"""
            **{len(deep_dive.budget_alternatives)} alternativas budget detectadas**
            
            Esto indica un nicho activo de opciones económicas.
            Oportunidad para posicionar productos value-for-money.
            """)
        else:
            st.info("No se detectaron alternativas económicas")


def _render_buying_intent_tab(deep_dive: Any) -> None:
    """Tab de intención de compra"""
    st.markdown("### 🛒 Señales de Intención de Compra")
    
    if not deep_dive.buying_intent:
        st.info("No hay datos de intención de compra")
        return
    
    intent = deep_dive.buying_intent
    
    # Métricas de intención
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        color = "#10B981" if intent.where_to_buy >= 2 else "#6B7280"
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #F3F4F6; border-radius: 8px;">
            <div style="font-size: 2rem;">🏪</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{intent.where_to_buy}</div>
            <div style="font-size: 0.8rem;">Dónde comprar</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color = "#10B981" if intent.price_mentions >= 3 else "#6B7280"
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #F3F4F6; border-radius: 8px;">
            <div style="font-size: 2rem;">💰</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{intent.price_mentions}</div>
            <div style="font-size: 0.8rem;">Menciones precio</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        color = "#10B981" if intent.availability >= 1 else "#6B7280"
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #F3F4F6; border-radius: 8px;">
            <div style="font-size: 2rem;">📦</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{intent.availability}</div>
            <div style="font-size: 0.8rem;">Disponibilidad</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        color = "#10B981" if intent.europe_mentions >= 1 else "#6B7280"
        st.markdown(f"""
        <div style="text-align: center; padding: 15px; background: #F3F4F6; border-radius: 8px;">
            <div style="font-size: 2rem;">🇪🇺</div>
            <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{intent.europe_mentions}</div>
            <div style="font-size: 0.8rem;">Europa/España</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Ejemplos encontrados
    if intent.sample_queries:
        st.markdown("#### 💬 Ejemplos Detectados")
        for query in intent.sample_queries[:5]:
            st.markdown(f"- *{sanitize_html(query)}*")
    
    # Interpretación
    st.markdown("---")
    st.markdown("#### 💡 Interpretación")
    
    total = intent.total_signals
    if total >= 5:
        st.success(f"""
        **ALTA INTENCIÓN DE COMPRA** ({total} señales)
        
        Los usuarios están activamente buscando dónde comprar este producto.
        Señal clara de demanda insatisfecha o en crecimiento.
        """)
    elif total >= 2:
        st.warning(f"""
        **INTENCIÓN DE COMPRA MODERADA** ({total} señales)
        
        Hay interés en adquirir el producto pero no es masivo.
        Puede ser un nicho específico o producto emergente.
        """)
    else:
        st.info(f"""
        **BAJA INTENCIÓN DE COMPRA** ({total} señales)
        
        Poco interés explícito en comprar. Puede ser:
        - Producto muy establecido (ya saben dónde comprarlo)
        - Producto muy nicho
        - No hay demanda real
        """)


def _render_markets_tab(deep_dive: Any) -> None:
    """Tab de mercados (idiomas conectados a países objetivo)"""
    st.markdown("### 🌍 Cobertura de Mercados Objetivo")
    st.caption("Mercados PCComponentes: España 🇪🇸 · Portugal 🇵🇹 · Francia 🇫🇷 · Italia 🇮🇹 · Alemania 🇩🇪")
    
    if not deep_dive.languages:
        st.info("No hay datos de idiomas")
        return
    
    # Tabla de mercados
    market_flags = {
        "ES": "🇪🇸", "PT": "🇵🇹", "FR": "🇫🇷", 
        "IT": "🇮🇹", "DE": "🇩🇪", "GLOBAL": "🌐", "OTHER": "🏳️"
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Gráfico de barras
        df = pd.DataFrame([
            {
                "Mercado": f"{market_flags.get(lang.target_market, '🏳️')} {lang.language_name}",
                "Videos": lang.video_count,
                "Vistas": lang.total_views
            }
            for lang in deep_dive.languages
        ])
        
        fig = px.bar(
            df, x="Mercado", y="Videos",
            color="Vistas",
            color_continuous_scale="Purples"
        )
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Detalle por Mercado")
        
        for lang in deep_dive.languages:
            flag = market_flags.get(lang.target_market, "🏳️")
            opp_color = {
                "dominant": "#3B82F6",    # Azul - domina el contenido
                "significant": "#10B981", # Verde - buena presencia
                "moderate": "#F59E0B",    # Naranja - presencia moderada
                "emerging": "#8B5CF6",    # Púrpura - emergente
                "minimal": "#6B7280"      # Gris - apenas hay contenido
            }.get(lang.market_opportunity, "#6B7280")
            
            opp_text = {
                "dominant": "Dominante",
                "significant": "Significativo",
                "moderate": "Moderado",
                "emerging": "Emergente",
                "minimal": "Mínimo"
            }.get(lang.market_opportunity, "?")
            
            st.markdown(f"""
            **{flag} {lang.language_name}**  
            {lang.video_count} videos ({lang.percentage:.0f}%)  
            <span style="color: {opp_color}; font-weight: bold;">{opp_text}</span>
            """, unsafe_allow_html=True)
            st.markdown("---")
    
    # Insight
    st.markdown("#### 💡 Insight de Mercado")
    
    target_markets = ["es", "pt", "fr", "it", "de"]
    covered = [lang for lang in deep_dive.languages if lang.language in target_markets]
    
    if len(covered) >= 3:
        st.success(f"""
        **Excelente cobertura multi-mercado** ({len(covered)} mercados objetivo)
        
        El producto tiene contenido en varios idiomas europeos.
        Buena señal para expansión en mercados PCComponentes.
        """)
    elif len(covered) >= 1:
        covered_names = ", ".join([lang.language_name for lang in covered])
        st.warning(f"""
        **Cobertura limitada** - Solo: {covered_names}
        
        Oportunidad para ser early mover en mercados no cubiertos.
        """)
    else:
        st.info("""
        **Sin cobertura de mercados objetivo**
        
        El contenido está principalmente en inglés/otros.
        Puede ser oportunidad o señal de que no hay demanda local.
        """)


def _render_videos_tab(deep_dive: Any) -> None:
    """Tab de videos"""
    if not deep_dive.videos_by_type:
        st.info("No hay videos")
        return
    
    # Subtabs por tipo
    video_tabs = st.tabs(["⭐ Reviews", "📦 Unboxings", "⚔️ VS", "📺 General"])
    categories = ["reviews", "unboxings", "comparisons", "general"]
    
    for tab, category in zip(video_tabs, categories):
        with tab:
            videos = deep_dive.videos_by_type.get(category, [])
            
            if not videos:
                st.info(f"No hay {category}")
                continue
            
            st.caption(f"{len(videos)} videos")
            
            # Grid 2 columnas
            for i in range(0, min(len(videos), 8), 2):
                cols = st.columns(2)
                
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx >= len(videos):
                        break
                    
                    video = videos[idx]
                    with col:
                        _render_video_card(video)


def _render_video_card(video: Any) -> None:
    """Renderiza tarjeta de video"""
    with st.container():
        if video.thumbnail:
            st.image(video.thumbnail, use_container_width=True)
        
        title = sanitize_html(video.title[:55] + "..." if len(video.title) > 55 else video.title)
        if video.link:
            st.markdown(f"**[{title}]({video.link})**")
        else:
            st.markdown(f"**{title}**")
        
        # Métricas
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"👁️ {video.views_formatted}")
        with col2:
            lang_flag = {
                "es": "🇪🇸", "en": "🇬🇧", "pt": "🇵🇹",
                "fr": "🇫🇷", "de": "🇩🇪", "it": "🇮🇹"
            }.get(getattr(video, 'language', ''), "🌐")
            st.caption(lang_flag)
        
        channel = sanitize_html(video.channel[:25]) if video.channel else "Unknown"
        st.caption(f"📺 {channel}")
        st.markdown("---")


# =============================================================================
# Funciones de compatibilidad
# =============================================================================

def render_youtube_panel(keyword: str, videos_by_type: Dict, metrics: Any) -> None:
    """Versión legacy para compatibilidad"""
    st.markdown("### 📺 YouTube")
    
    all_videos = []
    for v_list in videos_by_type.values():
        if v_list:
            all_videos.extend(v_list)
    
    if not all_videos:
        st.info("No se encontraron videos")
        return
    
    if metrics:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Videos", metrics.total_videos)
        with col2:
            st.metric("Vistas", format_number(metrics.total_views))
        with col3:
            st.metric("Score", f"{metrics.content_score}/100")


def render_youtube_mini(keyword: str, metrics: Any) -> None:
    """Versión compacta"""
    if not metrics or metrics.total_videos == 0:
        return
    
    st.markdown("#### 📺 YouTube")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Videos", metrics.total_videos)
    with col2:
        st.metric("Score", f"{metrics.content_score}/100")


def render_youtube_trends_comparison(keyword: str, trends_score: int, metrics: Any) -> None:
    """Comparativa con Trends"""
    pass
