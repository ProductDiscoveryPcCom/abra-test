"""
YouTube Panel Component
Visualiza datos de videos y métricas de YouTube
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import html as html_module
from typing import List, Dict, Optional
import pandas as pd


def render_youtube_panel(
    keyword: str,
    videos_by_type: Dict[str, list],
    metrics: any
) -> None:
    """
    Renderiza el panel completo de YouTube
    
    Args:
        keyword: Keyword buscado
        videos_by_type: Dict con videos por tipo (reviews, unboxings, etc)
        metrics: Métricas calculadas
    """
    st.markdown("### 📺 YouTube Intelligence")
    st.caption(f"Análisis de contenido para: **{html_module.escape(keyword)}**")
    
    all_videos = []
    for v_list in videos_by_type.values():
        all_videos.extend(v_list)
    
    if not all_videos:
        st.info("No se encontraron videos en YouTube para este término.")
        return
    
    # Métricas principales
    _render_metrics_summary(metrics)
    
    st.markdown("---")
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs([
        "⭐ Reviews",
        "📦 Unboxings",
        "⚔️ Comparativas",
        "📊 Análisis"
    ])
    
    with tab1:
        _render_video_grid(videos_by_type.get("reviews", []), "Reviews")
    
    with tab2:
        _render_video_grid(videos_by_type.get("unboxings", []), "Unboxings")
    
    with tab3:
        _render_video_grid(videos_by_type.get("comparisons", []), "Comparativas")
    
    with tab4:
        _render_youtube_analysis(videos_by_type, metrics)


def render_youtube_mini(keyword: str, metrics: any) -> None:
    """
    Versión compacta para sidebar o resumen
    
    Args:
        keyword: Keyword buscado
        metrics: Métricas calculadas
    """
    if not metrics or metrics.total_videos == 0:
        return
    
    st.markdown("#### 📺 YouTube")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Videos", f"{metrics.total_videos}")
        st.metric("Vistas totales", _format_number(metrics.total_views))
    
    with col2:
        st.metric("Recientes (30d)", f"{metrics.recent_videos_30d}")
        st.metric("Content Score", f"{metrics.content_score}/100")
    
    # Indicadores de contenido
    badges = []
    if metrics.has_reviews:
        badges.append("✅ Reviews")
    if metrics.has_unboxings:
        badges.append("📦 Unboxings")
    if metrics.has_comparisons:
        badges.append("⚔️ VS")
    
    if badges:
        st.caption(" · ".join(badges))


def _render_metrics_summary(metrics: any) -> None:
    """Renderiza resumen de métricas"""
    if not metrics:
        return
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Videos encontrados",
            f"{metrics.total_videos}",
            help="Total de videos únicos encontrados"
        )
    
    with col2:
        st.metric(
            "Vistas totales",
            _format_number(metrics.total_views),
            help="Suma de vistas de todos los videos"
        )
    
    with col3:
        st.metric(
            "Media de vistas",
            _format_number(metrics.avg_views),
            help="Vistas promedio por video"
        )
    
    with col4:
        st.metric(
            "Videos recientes",
            f"{metrics.recent_videos_30d}",
            delta=f"+{metrics.recent_videos_7d} esta semana" if metrics.recent_videos_7d > 0 else None,
            help="Videos subidos en los últimos 30 días"
        )
    
    with col5:
        # Content Score con color
        score = metrics.content_score
        if score >= 70:
            st.success(f"🎯 Score: {score}/100")
        elif score >= 40:
            st.warning(f"📊 Score: {score}/100")
        else:
            st.info(f"📊 Score: {score}/100")
    
    # Indicadores de tipo de contenido
    content_types = []
    if metrics.has_reviews:
        content_types.append("✅ Tiene reviews")
    if metrics.has_unboxings:
        content_types.append("📦 Tiene unboxings")
    if metrics.has_comparisons:
        content_types.append("⚔️ Tiene comparativas")
    
    if content_types:
        st.caption(" · ".join(content_types))


def _render_video_grid(videos: list, title: str) -> None:
    """Renderiza grid de videos"""
    if not videos:
        st.info(f"No se encontraron {title.lower()}")
        return
    
    st.markdown(f"#### {title} ({len(videos)} videos)")
    
    # Grid de 2 columnas
    for i in range(0, min(len(videos), 10), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(videos):
                break
            
            video = videos[idx]
            
            with col:
                _render_video_card(video)


def _render_video_card(video: any) -> None:
    """Renderiza tarjeta de video individual"""
    with st.container():
        # Thumbnail
        if video.thumbnail:
            st.image(video.thumbnail, width="stretch")
        
        # Título (con link)
        title = html_module.escape(video.title[:60] + "..." if len(video.title) > 60 else video.title)
        if video.link:
            st.markdown(f"**[{title}]({video.link})**")
        else:
            st.markdown(f"**{title}**")
        
        # Métricas
        col1, col2 = st.columns(2)
        with col1:
            st.caption(f"👁️ {video.views_formatted} vistas")
        with col2:
            if video.duration:
                st.caption(f"⏱️ {video.duration}")
        
        # Canal y fecha
        channel = html_module.escape(video.channel[:25]) if video.channel else "Unknown"
        st.caption(f"📺 {channel}")
        
        if video.published:
            st.caption(f"📅 {video.published}")
        
        st.markdown("---")


def _render_youtube_analysis(videos_by_type: dict, metrics: any) -> None:
    """Análisis detallado de YouTube"""
    if not metrics:
        st.info("No hay datos suficientes para análisis")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top canales
        st.markdown("#### 🎬 Top Canales")
        
        if metrics.top_channels:
            for i, channel in enumerate(metrics.top_channels[:5], 1):
                st.markdown(f"{i}. **{html_module.escape(channel)}**")
        else:
            st.info("No hay datos de canales")
    
    with col2:
        # Distribución por tipo
        st.markdown("#### 📊 Distribución de Contenido")
        
        type_counts = {
            "Reviews": len(videos_by_type.get("reviews", [])),
            "Unboxings": len(videos_by_type.get("unboxings", [])),
            "Comparativas": len(videos_by_type.get("comparisons", [])),
            "General": len(videos_by_type.get("general", []))
        }
        
        df = pd.DataFrame([
            {"Tipo": k, "Videos": v}
            for k, v in type_counts.items()
            if v > 0
        ])
        
        if not df.empty:
            fig = px.pie(
                df,
                values="Videos",
                names="Tipo",
                color_discrete_sequence=px.colors.sequential.Purples
            )
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, width="stretch")
    
    # Gráfico de vistas
    st.markdown("#### 👁️ Videos por Vistas")
    
    all_videos = []
    for v_list in videos_by_type.values():
        all_videos.extend(v_list)
    
    # Deduplicar
    seen = set()
    unique_videos = []
    for v in all_videos:
        if v.video_id not in seen:
            seen.add(v.video_id)
            unique_videos.append(v)
    
    # Top 10 por vistas
    top_videos = sorted(unique_videos, key=lambda x: x.views, reverse=True)[:10]
    
    if top_videos:
        df_views = pd.DataFrame([
            {
                "Video": v.title[:40] + "..." if len(v.title) > 40 else v.title,
                "Vistas": v.views,
                "Canal": v.channel[:20] if v.channel else "Unknown"
            }
            for v in top_videos
        ])
        
        fig = px.bar(
            df_views,
            x="Vistas",
            y="Video",
            orientation="h",
            color="Canal",
            title="Top 10 videos por vistas"
        )
        fig.update_layout(
            height=400,
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        st.plotly_chart(fig, width="stretch")


def render_youtube_trends_comparison(
    keyword: str,
    trends_score: int,
    youtube_metrics: any
) -> None:
    """
    Compara datos de Google Trends con YouTube
    
    Args:
        keyword: Keyword buscado
        trends_score: Índice de Google Trends
        youtube_metrics: Métricas de YouTube
    """
    st.markdown("### 🔄 Comparativa: Búsquedas vs Contenido")
    
    if not youtube_metrics or youtube_metrics.total_videos == 0:
        st.info("No hay datos de YouTube para comparar")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 Google Trends")
        st.metric("Índice de tendencia", trends_score)
        
        if trends_score < 30:
            st.warning("Bajo volumen de búsquedas")
        elif trends_score < 70:
            st.info("Volumen moderado")
        else:
            st.success("Alto volumen de búsquedas")
    
    with col2:
        st.markdown("#### 📺 YouTube")
        st.metric("Videos encontrados", youtube_metrics.total_videos)
        st.metric("Content Score", f"{youtube_metrics.content_score}/100")
        
        if youtube_metrics.content_score >= 70:
            st.success("Alto contenido en YouTube")
        elif youtube_metrics.content_score >= 40:
            st.info("Contenido moderado")
        else:
            st.warning("Poco contenido")
    
    st.markdown("---")
    
    # Análisis de oportunidad
    _analyze_opportunity(trends_score, youtube_metrics)


def _analyze_opportunity(trends_score: int, youtube_metrics: any) -> None:
    """Analiza oportunidad basada en discrepancia"""
    
    yt_score = youtube_metrics.content_score
    
    # Matriz de decisión
    if trends_score < 30 and yt_score >= 60:
        st.success("""
        🎯 **OPORTUNIDAD: Nicho de creadores**
        
        - Alto contenido en YouTube pero pocas búsquedas en Google
        - Los creadores de contenido ya hablan del producto
        - Puede indicar un producto técnico/especializado con audiencia fiel
        - **Acción**: Posicionar antes de que las búsquedas suban
        """)
    
    elif trends_score >= 60 and yt_score < 30:
        st.warning("""
        ⚠️ **ALERTA: Gap de contenido**
        
        - Altas búsquedas pero poco contenido en YouTube
        - La gente busca información pero no hay videos
        - Puede ser oportunidad para crear contenido propio
        - **Riesgo**: Puede ser producto nuevo sin stock disponible
        """)
    
    elif trends_score >= 60 and yt_score >= 60:
        st.info("""
        📈 **TENDENCIA ESTABLECIDA**
        
        - Alto interés tanto en búsquedas como en contenido
        - Producto/marca ya consolidada
        - Competencia alta
        - **Acción**: Asegurar stock y precios competitivos
        """)
    
    elif trends_score < 30 and yt_score < 30:
        st.warning("""
        📉 **BAJA TRACCIÓN**
        
        - Poco interés en búsquedas y poco contenido
        - Puede ser muy nicho o no tener mercado en España
        - **Acción**: Investigar en otros mercados (US, UK)
        """)
    
    else:
        # Casos intermedios
        if youtube_metrics.recent_videos_30d >= 5:
            st.info("""
            📊 **TENDENCIA EMERGENTE**
            
            - Actividad reciente de creadores
            - Posible producto en crecimiento
            - Monitorizar evolución
            """)
        else:
            st.info("📊 Datos dentro de rangos normales. Sin oportunidades claras detectadas.")


def _format_number(num: int) -> str:
    """Formatea número de forma legible"""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)
