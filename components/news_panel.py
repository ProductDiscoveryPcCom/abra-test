"""
News Panel Component
Panel de noticias relacionadas con la marca/tendencia
"""

import streamlit as st
from typing import List, Optional


def render_news_panel(
    news: list,
    title: str = "📰 Noticias Relacionadas",
    max_display: int = 6,
    show_sentiment: bool = True,
    sentiment_data: dict = None
) -> None:
    """
    Renderiza panel de noticias con cards visuales
    
    Args:
        news: Lista de noticias con title, link, source, date, thumbnail, snippet
        title: Título del panel
        max_display: Número máximo de noticias a mostrar
        show_sentiment: Mostrar análisis de sentimiento
        sentiment_data: Datos de sentimiento precalculados
    """
    total = len(news) if news else 0
    st.markdown(f"#### {title} ({total})")
    
    if not news:
        st.info("No se encontraron noticias recientes")
        return
    
    # Mostrar análisis de sentimiento si está disponible
    if show_sentiment and sentiment_data:
        _render_sentiment_bar(sentiment_data)
        st.markdown("")
    
    # Mostrar noticias en grid de 2 columnas
    cols = st.columns(2)
    
    for i, item in enumerate(news[:max_display]):
        with cols[i % 2]:
            _render_news_card(item)
    
    # Mostrar más si hay
    if total > max_display:
        with st.expander(f"Ver {total - max_display} noticias más"):
            for item in news[max_display:max_display + 10]:
                _render_news_item_compact(item)


def _render_news_card(item: dict) -> None:
    """Renderiza una card de noticia con imagen"""
    import html as html_module
    
    title = html_module.escape(str(item.get("title", "")))
    link = item.get("link", "#")
    source = html_module.escape(str(item.get("source", "")))
    date = html_module.escape(str(item.get("date", "")))
    thumbnail = item.get("thumbnail", "")
    
    # Truncar título si es muy largo
    if len(title) > 100:
        title = title[:97] + "..."
    
    # Validar URL del thumbnail
    if thumbnail and not thumbnail.startswith(('http://', 'https://')):
        thumbnail = ""
    
    # Card con contenedor Streamlit nativo + HTML mínimo
    with st.container():
        if thumbnail:
            st.image(thumbnail, width="stretch")
        
        st.markdown(f"**[{title}]({link})**")
        st.caption(f"📰 {source} · {date}")


def _render_news_item_compact(item: dict) -> None:
    """Renderiza noticia en formato compacto (sin imagen)"""
    import html as html_module
    
    title = html_module.escape(str(item.get("title", "")))
    link = item.get("link", "#")
    source = html_module.escape(str(item.get("source", "")))
    date = html_module.escape(str(item.get("date", "")))
    
    st.markdown(f"- [{title}]({link})")
    st.caption(f"   {source} · {date}")


def _render_sentiment_bar(sentiment_data: dict) -> None:
    """Renderiza barra de sentimiento de noticias"""
    positive_pct = sentiment_data.get("positive_pct", 0)
    negative_pct = sentiment_data.get("negative_pct", 0)
    neutral_pct = sentiment_data.get("neutral_pct", 0)
    sentiment_score = sentiment_data.get("sentiment_score", 0)
    
    # Determinar color e icono del score
    if sentiment_score > 20:
        score_color = "#10B981"
        score_icon = "😊"
        score_label = "Positivo"
    elif sentiment_score < -20:
        score_color = "#EF4444"
        score_icon = "😟"
        score_label = "Negativo"
    else:
        score_color = "#6B7280"
        score_icon = "😐"
        score_label = "Neutral"
    
    st.markdown(
        f'''
        <div style="background: #F9FAFB; border-radius: 8px; padding: 12px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.85rem; font-weight: 500; color: #374151;">
                    Sentimiento en noticias
                </span>
                <span style="font-size: 1rem; color: {score_color}; font-weight: 600;">
                    {score_icon} {score_label}
                </span>
            </div>
            <div style="height: 8px; background: #E5E7EB; border-radius: 4px; overflow: hidden; display: flex;">
                <div style="width: {positive_pct}%; background: #10B981;"></div>
                <div style="width: {neutral_pct}%; background: #9CA3AF;"></div>
                <div style="width: {negative_pct}%; background: #EF4444;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 6px; font-size: 0.7rem; color: #6B7280;">
                <span>🟢 {positive_pct:.0f}% positivo</span>
                <span>⚪ {neutral_pct:.0f}% neutral</span>
                <span>🔴 {negative_pct:.0f}% negativo</span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )


def render_news_comparison(
    brand_data: dict,
    title: str = "📊 Cobertura vs Competidores"
) -> None:
    """
    Renderiza comparativa de cobertura de noticias entre marca y competidores
    
    Args:
        brand_data: Dict de get_brand_mentions() con brand_news y competitors
    """
    brand = brand_data.get("brand", "Marca")
    brand_count = brand_data.get("brand_count", 0)
    competitors = brand_data.get("competitors", {})
    
    st.markdown(f"#### {title}")
    
    # Preparar datos
    all_counts = {brand: brand_count}
    for comp_name, comp_data in competitors.items():
        all_counts[comp_name] = comp_data.get("count", 0)
    
    max_count = max(all_counts.values()) if all_counts.values() else 1
    
    # Renderizar barras
    for name, count in sorted(all_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / max_count) * 100
        
        # Color diferente para la marca principal
        if name == brand:
            color = "#F5C518"
            badge = "🎯"
        else:
            color = "#7C3AED"
            badge = ""
        
        st.markdown(
            f'''
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span style="font-weight: 500; color: #1A1A2E;">{badge} {name}</span>
                    <span style="color: #6B7280; font-size: 0.85rem;">{count} noticias</span>
                </div>
                <div style="height: 10px; background: #F3F4F6; border-radius: 5px; overflow: hidden;">
                    <div style="height: 100%; width: {pct}%; background: {color}; border-radius: 5px;"></div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )


def render_tech_news_section(
    news_module,
    country: str = "ES"
) -> None:
    """
    Renderiza sección de noticias de tecnología destacadas
    
    Args:
        news_module: Instancia de GoogleNewsModule
        country: Código de país
    """
    import html as html_module
    
    st.markdown("#### 🔥 Noticias Tech Destacadas")
    
    result = news_module.get_topic_news("technology", country)
    
    if not result.get("success"):
        st.warning("No se pudieron cargar las noticias de tecnología")
        return
    
    news = result.get("news", [])[:4]
    
    cols = st.columns(4)
    for i, item in enumerate(news):
        with cols[i]:
            title = html_module.escape(str(item.get("title", "")))
            link = item.get("link", "#")
            source = html_module.escape(str(item.get("source", "")))
            
            # Truncar
            if len(title) > 60:
                title = title[:57] + "..."
            
            st.markdown(f"**[{title}]({link})**")
            st.caption(f"🔗 {source}")
