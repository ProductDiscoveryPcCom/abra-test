"""
Social Media Panel Component
Panel unificado para YouTube + TikTok + Social Score
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import html as html_module
from typing import Optional, Dict, Any
import pandas as pd


def render_social_media_section(
    keyword: str,
    youtube_data: Optional[Dict] = None,
    youtube_metrics: Optional[Any] = None,
    tiktok_data: Optional[Dict] = None,
    tiktok_metrics: Optional[Any] = None,
    social_metrics: Optional[Any] = None,
    trends_score: int = 0
) -> None:
    """
    Renderiza sección completa de Social Media Intelligence
    
    Args:
        keyword: Keyword buscado
        youtube_data: Dict con videos de YouTube por tipo
        youtube_metrics: Métricas de YouTube
        tiktok_data: Dict con datos de TikTok
        tiktok_metrics: Métricas de TikTok
        social_metrics: Métricas combinadas
        trends_score: Score de Google Trends
    """
    st.markdown("### 📱 Social Media Intelligence")
    
    # Verificar datos de forma segura
    has_youtube = False
    has_tiktok = False
    
    try:
        has_youtube = youtube_metrics is not None and getattr(youtube_metrics, 'total_videos', 0) > 0
    except Exception:
        pass
    
    try:
        has_tiktok = tiktok_metrics is not None and getattr(tiktok_metrics, 'total_videos', 0) > 0
    except Exception:
        pass
    
    if not has_youtube and not has_tiktok:
        st.info("No se encontraron datos de redes sociales para este término.")
        return
    
    # Métricas principales
    _render_social_summary(youtube_metrics, tiktok_metrics, social_metrics)
    
    st.markdown("---")
    
    # Oportunidad detectada
    if social_metrics and social_metrics.opportunity_type:
        _render_opportunity_alert(social_metrics)
        st.markdown("---")
    
    # Tabs por plataforma
    tabs = []
    tab_names = []
    
    if has_youtube:
        tab_names.append("📺 YouTube")
    if has_tiktok:
        tab_names.append("🎵 TikTok")
    tab_names.append("📊 Comparativa")
    
    tabs = st.tabs(tab_names)
    tab_idx = 0
    
    if has_youtube:
        with tabs[tab_idx]:
            _render_youtube_tab(youtube_data, youtube_metrics)
        tab_idx += 1
    
    if has_tiktok:
        with tabs[tab_idx]:
            _render_tiktok_tab(tiktok_data, tiktok_metrics)
        tab_idx += 1
    
    with tabs[tab_idx]:
        _render_comparison_tab(
            trends_score=trends_score,
            youtube_metrics=youtube_metrics,
            tiktok_metrics=tiktok_metrics,
            social_metrics=social_metrics
        )


def render_social_media_mini(
    youtube_metrics: Optional[Any] = None,
    tiktok_metrics: Optional[Any] = None,
    social_metrics: Optional[Any] = None
) -> None:
    """
    Versión compacta para sidebar
    """
    st.markdown("#### 📱 Social Media")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if youtube_metrics and youtube_metrics.total_videos > 0:
            st.metric("📺 YouTube", f"{youtube_metrics.total_videos} videos")
        else:
            st.metric("📺 YouTube", "N/A")
    
    with col2:
        if tiktok_metrics and tiktok_metrics.total_videos > 0:
            st.metric("🎵 TikTok", f"{tiktok_metrics.tiktok_views_formatted} views")
        else:
            st.metric("🎵 TikTok", "N/A")
    
    if social_metrics:
        score = social_metrics.social_score
        if score >= 70:
            st.success(f"🎯 Social Score: {score}/100")
        elif score >= 40:
            st.warning(f"📊 Social Score: {score}/100")
        else:
            st.info(f"📊 Social Score: {score}/100")


def _render_social_summary(
    youtube_metrics: Optional[Any],
    tiktok_metrics: Optional[Any],
    social_metrics: Optional[Any]
) -> None:
    """Renderiza resumen de métricas sociales"""
    
    cols = st.columns(5)
    
    with cols[0]:
        if youtube_metrics:
            st.metric(
                "📺 Videos YouTube",
                f"{youtube_metrics.total_videos}",
                delta=f"+{youtube_metrics.recent_videos_30d} (30d)" if youtube_metrics.recent_videos_30d > 0 else None
            )
        else:
            st.metric("📺 Videos YouTube", "N/A")
    
    with cols[1]:
        if youtube_metrics:
            st.metric(
                "👁️ Vistas YouTube",
                _format_number(youtube_metrics.total_views)
            )
        else:
            st.metric("👁️ Vistas YouTube", "N/A")
    
    with cols[2]:
        if tiktok_metrics:
            st.metric(
                "🎵 Views TikTok",
                _format_number(tiktok_metrics.hashtag_views)
            )
        else:
            st.metric("🎵 Views TikTok", "No config.")
    
    with cols[3]:
        if tiktok_metrics:
            st.metric(
                "📹 Videos TikTok",
                f"{tiktok_metrics.total_videos}"
            )
        else:
            st.metric("📹 Videos TikTok", "N/A")
    
    with cols[4]:
        if social_metrics:
            score = social_metrics.social_score
            if score >= 70:
                st.success(f"🎯 **{score}**/100")
            elif score >= 40:
                st.warning(f"📊 **{score}**/100")
            else:
                st.info(f"📊 **{score}**/100")
            st.caption("Social Score")
        else:
            st.metric("Social Score", "N/A")


def _render_opportunity_alert(social_metrics: Any) -> None:
    """Renderiza alerta de oportunidad detectada"""
    
    opp_type = social_metrics.opportunity_type
    description = social_metrics.opportunity_description
    
    if opp_type == "early_opportunity":
        st.success(description)
    elif opp_type == "content_gap":
        st.warning(description)
    elif opp_type == "established":
        st.info(description)
    elif opp_type == "emerging":
        st.info(description)
    elif opp_type == "low_traction":
        st.warning(description)
    else:
        st.info(description)


def _render_youtube_tab(
    youtube_data: Optional[Dict],
    youtube_metrics: Optional[Any]
) -> None:
    """Renderiza contenido de tab de YouTube"""
    
    if not youtube_data:
        st.info("No hay datos de YouTube")
        return
    
    # Indicadores de contenido
    indicators = []
    if youtube_metrics:
        if youtube_metrics.has_reviews:
            indicators.append("✅ Reviews")
        if youtube_metrics.has_unboxings:
            indicators.append("📦 Unboxings")
        if youtube_metrics.has_comparisons:
            indicators.append("⚔️ Comparativas")
    
    if indicators:
        st.caption(" · ".join(indicators))
    
    # Sub-tabs por tipo de contenido
    sub_tabs = st.tabs(["⭐ Reviews", "📦 Unboxings", "⚔️ VS", "🎬 General"])
    
    with sub_tabs[0]:
        _render_video_list(youtube_data.get("reviews", []), "reviews")
    
    with sub_tabs[1]:
        _render_video_list(youtube_data.get("unboxings", []), "unboxings")
    
    with sub_tabs[2]:
        _render_video_list(youtube_data.get("comparisons", []), "comparisons")
    
    with sub_tabs[3]:
        _render_video_list(youtube_data.get("general", []), "general")
    
    # Top canales
    if youtube_metrics and youtube_metrics.top_channels:
        st.markdown("#### 🎬 Top Canales")
        for i, channel in enumerate(youtube_metrics.top_channels[:5], 1):
            st.markdown(f"{i}. **{html_module.escape(channel)}**")


def _render_video_list(videos: list, key_prefix: str) -> None:
    """Renderiza lista de videos"""
    if not videos:
        st.info("No se encontraron videos de este tipo")
        return
    
    for i, video in enumerate(videos[:8]):
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                if hasattr(video, 'thumbnail') and video.thumbnail:
                    st.image(video.thumbnail, width="stretch")
            
            with col2:
                title = html_module.escape(video.title[:60] + "..." if len(video.title) > 60 else video.title)
                if hasattr(video, 'link') and video.link:
                    st.markdown(f"**[{title}]({video.link})**")
                else:
                    st.markdown(f"**{title}**")
                
                views_str = video.views_formatted if hasattr(video, 'views_formatted') else str(video.views)
                channel = html_module.escape(video.channel[:30]) if hasattr(video, 'channel') and video.channel else ""
                
                st.caption(f"👁️ {views_str} · 📺 {channel}")
                
                if hasattr(video, 'published') and video.published:
                    st.caption(f"📅 {video.published}")
        
        st.markdown("---")


def _render_tiktok_tab(
    tiktok_data: Optional[Dict],
    tiktok_metrics: Optional[Any]
) -> None:
    """Renderiza contenido de tab de TikTok"""
    
    if not tiktok_data:
        st.info("""
        🎵 **TikTok no está configurado**
        
        Para activar datos de TikTok, añade las credenciales de API en `secrets.toml`:
        ```
        TIKTOK_API_KEY = "tu_api_key"
        TIKTOK_API_SECRET = "tu_api_secret"
        ```
        """)
        return
    
    # TODO: Implementar cuando se tenga API de TikTok
    st.info("Datos de TikTok pendientes de implementar")


def _render_comparison_tab(
    trends_score: int,
    youtube_metrics: Optional[Any],
    tiktok_metrics: Optional[Any],
    social_metrics: Optional[Any]
) -> None:
    """Renderiza comparativa entre plataformas"""
    
    st.markdown("#### 📊 Comparativa de Señales")
    
    # Datos para el gráfico
    data = []
    
    data.append({
        "Fuente": "Google Trends",
        "Score": trends_score,
        "Tipo": "Búsquedas"
    })
    
    if youtube_metrics:
        data.append({
            "Fuente": "YouTube",
            "Score": youtube_metrics.content_score,
            "Tipo": "Contenido"
        })
    
    if tiktok_metrics:
        data.append({
            "Fuente": "TikTok",
            "Score": tiktok_metrics.viral_score,
            "Tipo": "Viralidad"
        })
    
    if social_metrics:
        data.append({
            "Fuente": "Social Score",
            "Score": social_metrics.social_score,
            "Tipo": "Combinado"
        })
    
    if len(data) > 1:
        df = pd.DataFrame(data)
        
        fig = px.bar(
            df,
            x="Fuente",
            y="Score",
            color="Tipo",
            title="Comparativa de Scores por Fuente",
            color_discrete_map={
                "Búsquedas": "#7C3AED",
                "Contenido": "#EF4444",
                "Viralidad": "#10B981",
                "Combinado": "#F59E0B"
            }
        )
        fig.update_layout(height=350, showlegend=True)
        fig.add_hline(y=50, line_dash="dash", line_color="gray", opacity=0.5)
        
        st.plotly_chart(fig, width="stretch")
    
    # Matriz de decisión visual
    st.markdown("#### 🎯 Matriz de Oportunidad")
    
    yt_score = youtube_metrics.content_score if youtube_metrics else 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Cuadrante
        fig = go.Figure()
        
        # Punto actual
        fig.add_trace(go.Scatter(
            x=[trends_score],
            y=[yt_score],
            mode='markers+text',
            marker=dict(size=20, color='#7C3AED'),
            text=['Posición actual'],
            textposition='top center'
        ))
        
        # Cuadrantes
        fig.add_shape(type="rect", x0=0, y0=50, x1=50, y1=100,
                     fillcolor="rgba(16, 185, 129, 0.2)", line_width=0)
        fig.add_shape(type="rect", x0=50, y0=50, x1=100, y1=100,
                     fillcolor="rgba(245, 158, 11, 0.2)", line_width=0)
        fig.add_shape(type="rect", x0=0, y0=0, x1=50, y1=50,
                     fillcolor="rgba(239, 68, 68, 0.2)", line_width=0)
        fig.add_shape(type="rect", x0=50, y0=0, x1=100, y1=50,
                     fillcolor="rgba(59, 130, 246, 0.2)", line_width=0)
        
        # Etiquetas de cuadrantes
        fig.add_annotation(x=25, y=75, text="🚀 OPORTUNIDAD", showarrow=False, font=dict(size=12))
        fig.add_annotation(x=75, y=75, text="📈 ESTABLECIDO", showarrow=False, font=dict(size=12))
        fig.add_annotation(x=25, y=25, text="📉 BAJA TRACCIÓN", showarrow=False, font=dict(size=12))
        fig.add_annotation(x=75, y=25, text="📝 GAP CONTENIDO", showarrow=False, font=dict(size=12))
        
        fig.update_layout(
            xaxis=dict(title="Google Trends Score", range=[0, 100]),
            yaxis=dict(title="Social Score (YouTube)", range=[0, 100]),
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, width="stretch")
    
    with col2:
        st.markdown("""
        **Interpretación de cuadrantes:**
        
        🟢 **OPORTUNIDAD** (arriba-izquierda)
        - Alto contenido social, bajas búsquedas
        - Los creadores ya hablan del producto
        - Oportunidad de posicionarse antes del boom
        
        🟡 **ESTABLECIDO** (arriba-derecha)
        - Alto en búsquedas y contenido
        - Producto consolidado, alta competencia
        - Competir en precio y disponibilidad
        
        🔴 **BAJA TRACCIÓN** (abajo-izquierda)
        - Bajo en búsquedas y contenido
        - Poco interés general
        - Investigar otros mercados
        
        🔵 **GAP DE CONTENIDO** (abajo-derecha)
        - Altas búsquedas, poco contenido
        - Oportunidad de crear contenido
        - Puede ser producto muy nuevo
        """)


def _format_number(num: int) -> str:
    """Formatea número de forma legible"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)
