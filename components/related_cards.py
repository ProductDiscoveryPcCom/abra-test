"""
Related Cards Component
Cards para queries relacionadas, topics y tendencias con sparklines
"""

import streamlit as st
import plotly.graph_objects as go
from typing import List, Optional


def render_related_queries(
    queries: dict,
    show_type: str = "rising",
    country: str = "ES"
) -> None:
    """
    Renderiza la sección de Related Queries

    Args:
        queries: Dict con 'rising' y 'top' lists
        show_type: 'rising' o 'top'
        country: Código de país (ES, PT, FR, etc.)
    """
    country_names = {"ES": "España", "PT": "Portugal", "FR": "Francia", "IT": "Italia", "DE": "Alemania"}
    country_name = country_names.get(country, country)

    st.markdown(f"#### 🔍 Búsquedas relacionadas ({country_name})")

    # Info sobre Breakout
    with st.expander("ℹ️ ¿Qué significan los indicadores?"):
        st.markdown("""
        - **🚀 Breakout**: Crecimiento explosivo (+5000% o más). Indica una tendencia emergente muy fuerte.
        - **↗ +X%**: Porcentaje de crecimiento respecto al periodo anterior.
        - **📊 Top**: Las búsquedas más populares en volumen absoluto (no necesariamente en crecimiento).
        """)

    # Tabs para Rising/Top
    tab1, tab2 = st.tabs(["📈 En aumento", "🏆 Más buscados"])

    with tab1:
        _render_query_list(queries.get("rising", []), is_rising=True)

    with tab2:
        _render_query_list(queries.get("top", []), is_rising=False)


def render_related_topics(
    topics: dict,
    show_type: str = "rising"
) -> None:
    """
    Renderiza la sección de Related Topics

    Args:
        topics: Dict con 'rising' y 'top' lists
    """
    st.markdown("#### 📑 Related Topics")

    tab1, tab2 = st.tabs(["📈 Rising", "🏆 Top"])

    with tab1:
        _render_topic_list(topics.get("rising", []), is_rising=True)

    with tab2:
        _render_topic_list(topics.get("top", []), is_rising=False)


def _render_query_list(queries: list, is_rising: bool = True) -> None:
    """Renderiza lista de queries"""
    if not queries:
        st.info("No hay datos disponibles")
        return

    for i, query in enumerate(queries[:15]):  # Mostrar hasta 15
        query_text = query.get("query", "")

        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"{i+1}. **{query_text}**")

        with col2:
            if is_rising:
                extracted = query.get("extracted_value", 0)
                if extracted == "Breakout" or (isinstance(extracted, int) and extracted > 5000):
                    st.markdown("🚀 **Breakout**")
                elif isinstance(extracted, int) and extracted > 0:
                    st.success(f"↗ +{extracted}%")
                elif isinstance(extracted, int) and extracted < 0:
                    st.error(f"↘ {extracted}%")
                else:
                    st.info("↗ Rising")
            else:
                value = query.get("value", 0)
                st.caption(f"📊 {value}")


def _render_topic_list(topics: list, is_rising: bool = True) -> None:
    """Renderiza lista de topics"""
    if not topics:
        st.info("No hay datos disponibles")
        return

    for i, topic in enumerate(topics[:15]):  # Mostrar hasta 15
        topic_info = topic.get("topic", {})
        title = topic_info.get("title", "Unknown")
        topic_type = topic_info.get("type", "")

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.markdown(f"{i+1}. **{title}**")

        with col2:
            if topic_type:
                st.caption(f"📌 {topic_type}")

        with col3:
            if is_rising:
                extracted = topic.get("extracted_value", 0)
                if extracted == "Breakout" or (isinstance(extracted, int) and extracted > 5000):
                    st.markdown("🚀 **Breakout**")
                elif isinstance(extracted, int) and extracted > 0:
                    st.success(f"↗ +{extracted}%")
                elif isinstance(extracted, int) and extracted < 0:
                    st.error(f"↘ {extracted}%")
                else:
                    st.info("↗ Rising")
            else:
                value = topic.get("value", 0)
                st.caption(f"📊 {value}")


def render_trend_cards(
    trends: list,
    title: str = "Tendencias Relacionadas"
) -> None:
    """
    Renderiza cards de tendencias con mini sparklines

    Args:
        trends: Lista de tendencias con name y values
    """
    st.markdown(f"#### 📊 {title}")

    if not trends:
        st.info("No hay tendencias relacionadas disponibles")
        return

    # Mostrar en grid de 4 columnas
    cols = st.columns(4)

    for i, trend in enumerate(trends[:8]):
        with cols[i % 4]:
            _render_single_trend_card(trend)

    if len(trends) > 8:
        st.markdown(
            f'<a href="#" style="color: #7C3AED; text-decoration: none; font-size: 0.875rem;">'
            f'Ver todas las {len(trends)} tendencias relacionadas →</a>',
            unsafe_allow_html=True
        )


def _render_single_trend_card(trend: dict) -> None:
    """Renderiza una card individual de tendencia"""
    name = trend.get("name", trend.get("query", "Unknown"))
    values = trend.get("values", [])

    # Determinar tendencia
    if values and len(values) >= 2:
        if values[-1] > values[0]:
            trend_icon = "📈"
            trend_color = "#10B981"
        elif values[-1] < values[0]:
            trend_icon = "📉"
            trend_color = "#EF4444"
        else:
            trend_icon = "➡️"
            trend_color = "#6B7280"
    else:
        trend_icon = "📊"
        trend_color = "#6B7280"
        values = [50, 52, 48, 55, 60, 58, 62]  # Datos dummy

    # Crear mini sparkline
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=trend_color, width=2),
        fill='tozeroy',
        fillcolor=f'{trend_color}15',
        hoverinfo='skip'
    ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        height=40,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    # Card
    st.markdown(
        f'''
        <div style="background: white; border: 1px solid #E5E7EB; border-radius: 8px;
        padding: 12px; margin-bottom: 12px; transition: all 0.2s;"
        onmouseover="this.style.borderColor='#F5C518'; this.style.boxShadow='0 4px 6px rgba(0,0,0,0.1)';"
        onmouseout="this.style.borderColor='#E5E7EB'; this.style.boxShadow='none';">
            <div style="font-size: 0.875rem; font-weight: 500; color: #1A1A2E;
            margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                {name}
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.plotly_chart(fig, width="stretch", key=f"spark_{name[:20]}")


def render_competitor_brands(brands: list) -> None:
    """
    Renderiza cards de marcas competidoras identificadas
    """
    if not brands:
        return

    st.markdown("#### 🏷️ Marcas Relacionadas")

    cols = st.columns(min(4, len(brands)))

    for i, brand in enumerate(brands[:4]):
        with cols[i]:
            name = brand.get("name", "")
            brand_type = brand.get("type", "")
            growth = brand.get("growth", "")

            st.markdown(
                f'''
                <div style="background: linear-gradient(135deg, rgba(245,197,24,0.06), rgba(124,58,237,0.06));
                border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; text-align: center;">
                    <div style="font-size: 1rem; font-weight: 600; color: #1A1A2E;
                    margin-bottom: 4px;">{name}</div>
                    <div style="font-size: 0.75rem; color: #6B7280; margin-bottom: 8px;">
                        {brand_type}
                    </div>
                    <div style="font-size: 0.8rem; color: #10B981; font-weight: 500;">
                        {growth}
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )

