"""
Seasonality Panel Component
Panel de estacionalidad con gráfico de barras mensual
"""

import plotly.graph_objects as go
import streamlit as st


MONTH_NAMES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
}


def render_seasonality_panel(
    seasonality_data: dict,
    ai_explanation: str = None,
    height: int = 200
) -> None:
    """
    Renderiza el panel de estacionalidad con gráfico y explicación

    Args:
        seasonality_data: Dict con monthly_pattern, is_seasonal, etc.
        ai_explanation: Explicación generada por IA (opcional)
    """
    is_seasonal = seasonality_data.get("is_seasonal", False)
    monthly_pattern = seasonality_data.get("monthly_pattern", {})
    seasonality_score = seasonality_data.get("seasonality_score", 0)

    # Header con badge
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📅 Estacionalidad")

    with col2:
        if is_seasonal:
            st.success("🔥 Altamente estacional")
        else:
            st.info("📊 Poco estacional")

    if not monthly_pattern:
        st.info("No hay suficientes datos para analizar estacionalidad")
        return

    # Preparar datos para el gráfico
    months = list(range(1, 13))
    values = [monthly_pattern.get(m, 0) for m in months]

    # Colores: verde para positivo, rojo para negativo
    colors = ['#10B981' if v >= 0 else '#FCA5A5' for v in values]

    # Crear gráfico
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=[MONTH_NAMES[m] for m in months],
        y=values,
        marker_color=colors,
        hovertemplate='<b>%{x}</b><br>%{y:+.0%} vs media<extra></extra>'
    ))

    # Línea de referencia en 0
    fig.add_hline(y=0, line_color='#94A3B8', line_width=1)

    fig.update_layout(
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=None,
            tickformat='+.0%',
            zeroline=False
        ),
        margin=dict(l=40, r=20, t=20, b=40),
        height=height,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig, width="stretch")

    # Explicación IA
    if ai_explanation:
        st.markdown(
            f'<div style="background-color: #F3F4F6; padding: 12px 16px; '
            f'border-radius: 8px; font-size: 0.875rem; color: #4B5563;">'
            f'💡 {ai_explanation}</div>',
            unsafe_allow_html=True
        )

    # Mostrar meses pico y valle
    if monthly_pattern:
        peak_month = max(monthly_pattern, key=monthly_pattern.get)
        low_month = min(monthly_pattern, key=monthly_pattern.get)

        col_peak, col_low = st.columns(2)

        with col_peak:
            peak_value = monthly_pattern[peak_month]
            st.markdown(
                f'<div style="text-align: center;">'
                f'<span style="color: #10B981; font-size: 1.5rem;">▲</span><br>'
                f'<span style="font-weight: 600;">Pico: {MONTH_NAMES[peak_month]}</span><br>'
                f'<span style="color: #10B981; font-size: 0.875rem;">{peak_value:+.0%}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_low:
            low_value = monthly_pattern[low_month]
            st.markdown(
                f'<div style="text-align: center;">'
                f'<span style="color: #EF4444; font-size: 1.5rem;">▼</span><br>'
                f'<span style="font-weight: 600;">Valle: {MONTH_NAMES[low_month]}</span><br>'
                f'<span style="color: #EF4444; font-size: 0.875rem;">{low_value:+.0%}</span>'
                f'</div>',
                unsafe_allow_html=True
            )


def render_seasonality_badge(is_seasonal: bool) -> str:
    """Retorna HTML del badge de estacionalidad"""
    if is_seasonal:
        return (
            '<span style="background-color: #FEF3C7; color: #D97706; '
            'padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; '
            'font-weight: 500;">Estacional</span>'
        )
    else:
        return (
            '<span style="background-color: #D1FAE5; color: #059669; '
            'padding: 2px 8px; border-radius: 9999px; font-size: 0.75rem; '
            'font-weight: 500;">Estable</span>'
        )

