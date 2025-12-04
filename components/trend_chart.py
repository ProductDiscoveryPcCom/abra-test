"""
Trend Chart Component
Gráfico principal de tendencia temporal con trayectoria
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import re
from typing import List, Tuple, Optional


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Mapeo de meses (inglés + español)
MONTH_MAP = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    'january': 1, 'february': 2, 'march': 3, 'april': 4, 'june': 6,
    'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'ene': 1, 'abr': 4, 'ago': 8, 'dic': 12,
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

DATE_FORMATS = [
    "%b %d, %Y",      # Nov 3, 2024
    "%B %d, %Y",      # November 3, 2024
    "%b %Y",          # Nov 2024
    "%B %Y",          # November 2024
    "%Y-%m-%d",       # 2024-11-03
    "%d/%m/%Y",       # 03/11/2024
    "%m/%d/%Y",       # 11/03/2024
    "%d %b %Y",       # 03 Nov 2024
    "%d %B %Y",       # 03 November 2024
    "%d-%m-%Y",       # 03-11-2024
    "%Y/%m/%d",       # 2024/11/03
    "%b. %d, %Y",     # Nov. 3, 2024
    "%d de %b de %Y", # 3 de Nov de 2024
]


def parse_date_string(date_str: str, fallback_date: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parsea un string de fecha en múltiples formatos.
    
    Args:
        date_str: String de fecha a parsear
        fallback_date: Fecha a usar si no se puede parsear
        
    Returns:
        datetime o None si no se pudo parsear
    """
    if not date_str:
        return fallback_date
    
    # Limpiar rangos de fecha (tomar inicio)
    for sep in [" – ", " - ", " to ", " — "]:
        if sep in date_str:
            date_str = date_str.split(sep)[0]
            break
    
    date_str = date_str.strip()
    
    # Intentar formatos conocidos
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Fallback: regex para "Mes Año"
    match = re.search(r'(\w+)[,\s]+(\d{4})', date_str.lower())
    if match:
        month_str, year = match.groups()
        month_num = MONTH_MAP.get(month_str[:3])
        if month_num:
            return datetime(int(year), month_num, 1)
    
    # Fallback: regex numérico
    match = re.search(r'(\d{4})[-/](\d{1,2})', date_str)
    if match:
        year, month = match.groups()
        return datetime(int(year), int(month), 1)
    
    return fallback_date


def extract_timeline_values(timeline_data: list) -> Tuple[List[datetime], List[float]]:
    """
    Extrae fechas y valores de timeline_data.
    
    Args:
        timeline_data: Lista de puntos de Google Trends
        
    Returns:
        Tuple (dates, values)
    """
    dates = []
    values = []
    now = datetime.now()
    
    for i, point in enumerate(timeline_data):
        # Extraer valor
        val = 0
        if "values" in point and len(point["values"]) > 0:
            raw_val = point["values"][0].get("extracted_value", 0)
            try:
                val = float(raw_val) if raw_val else 0
            except (ValueError, TypeError):
                val = 0
        
        # Extraer fecha
        date_str = point.get("date", "")
        weeks_back = len(timeline_data) - i - 1
        fallback = now - pd.Timedelta(weeks=weeks_back)
        
        date = parse_date_string(date_str, fallback)
        
        dates.append(date)
        values.append(val)
    
    return dates, values


def format_volume_number(v: float) -> str:
    """Formatea un número de volumen para display"""
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(int(v))


# =============================================================================
# MAIN COMPONENT
# =============================================================================

def render_trend_chart(
    timeline_data: list,
    keyword: str,
    show_trajectory: bool = True,
    show_seasonality: bool = False,
    height: int = 400,
    api_key: str = None,
    geo: str = "ES",
    show_volume_estimate: bool = True,
    show_predictions: bool = False
) -> None:
    """
    Renderiza el gráfico principal de tendencia con volúmenes estimados.

    Args:
        timeline_data: Lista de datos de Google Trends
        keyword: Palabra clave buscada
        show_trajectory: Mostrar línea de tendencia suavizada
        show_seasonality: Mostrar/ocultar efecto estacional
        height: Altura del gráfico en pixels
        api_key: API key de SerpAPI para estimar volúmenes
        geo: Código de país
        show_volume_estimate: Mostrar volúmenes estimados en lugar de índice
        show_predictions: Mostrar predicciones futuras
    """
    if not timeline_data:
        st.warning("No hay datos para mostrar")
        return

    # Extraer datos usando helper
    dates, values = extract_timeline_values(timeline_data)

    if not values or all(v == 0 for v in values):
        st.warning("No se pudieron procesar los datos")
        return

    df = pd.DataFrame({"date": dates, "value": values})
    df = df.sort_values("date")

    # Estimar volúmenes si tenemos API key
    volume_data = None
    if show_volume_estimate and api_key:
        try:
            from modules.search_volume import SearchVolumeEstimator
            estimator = SearchVolumeEstimator(api_key)

            current_index = int(df["value"].iloc[-1])
            volume_estimate = estimator.estimate_volume(keyword, current_index, geo)

            if current_index > 0:
                scale_factor = volume_estimate["estimated_volume"] / current_index
            else:
                scale_factor = volume_estimate["estimated_volume"] / 50

            df["volume"] = (df["value"] * scale_factor).astype(int)
            volume_data = {
                "current": volume_estimate,
                "scale_factor": scale_factor
            }
        except Exception:
            st.caption("⚠️ Usando índice de tendencia (0-100)")
            volume_data = None

    # Configurar columnas según datos disponibles
    if volume_data and "volume" in df.columns:
        y_col = "volume"
        y_label = "Búsquedas/mes (est.)"
        hover_label = "Búsquedas"
        format_fn = format_volume_number
    else:
        y_col = "value"
        y_label = "Índice Google Trends"
        hover_label = "Índice"
        format_fn = lambda v: f"{v:.0f}"

    # Calcular métricas
    current_value = df[y_col].iloc[-1]
    avg_value = df[y_col].mean()
    max_value = df[y_col].max()

    # Calcular crecimiento
    if len(df) >= 6:
        recent_avg = df[y_col].tail(3).mean()
        previous_avg = df[y_col].head(len(df) - 3).mean()
        if previous_avg > 0:
            growth = ((recent_avg - previous_avg) / previous_avg) * 100
        else:
            growth = 0
    else:
        growth = 0

    # Crear figura
    fig = go.Figure()

    # Preparar texto de hover
    hover_texts = [f"<b>{d.strftime('%b %Y')}</b><br>{hover_label}: {format_fn(v)}"
                   for d, v in zip(df["date"], df[y_col])]

    # Área con gradiente
    fig.add_trace(go.Scatter(
        x=df["date"],
        y=df[y_col],
        mode='lines',
        name=y_label,
        line=dict(color='#7C3AED', width=2),
        fill='tozeroy',
        fillcolor='rgba(124, 58, 237, 0.1)',
        hovertext=hover_texts,
        hoverinfo='text'
    ))

    # Línea de trayectoria (media móvil)
    if show_trajectory and len(df) >= 6:
        window = min(6, len(df) // 3)
        df["trajectory"] = df[y_col].rolling(window=window, center=True).mean()

        fig.add_trace(go.Scatter(
            x=df["date"],
            y=df["trajectory"],
            mode='lines',
            name='Trayectoria',
            line=dict(color='#1A1A2E', width=3, dash='solid'),
            hovertemplate='<b>%{x|%b %Y}</b><br>Trayectoria: %{y:,.0f}<extra></extra>'
        ))

    # Línea de promedio
    fig.add_hline(
        y=avg_value,
        line_dash="dash",
        line_color="#94A3B8",
        annotation_text=f"Media: {format_fn(avg_value)}",
        annotation_position="right"
    )

    # Layout con rangeslider para zoom
    fig.update_layout(
        title=None,
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=None,
            tickformat='%b %Y',
            rangeslider=dict(
                visible=True,
                thickness=0.05,
                bgcolor='rgba(124, 58, 237, 0.1)'
            ),
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=3, label="3M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="1A", step="year", stepmode="backward"),
                    dict(step="all", label="Todo")
                ],
                bgcolor='white',
                activecolor='#7C3AED',
                font=dict(size=11)
            )
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=y_label if volume_data else None,
            range=[0, max_value * 1.1],
            tickformat=',.0f' if volume_data else None
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=60 if volume_data else 40, r=40, t=40, b=40),
        height=height,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    # Métricas en header
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if volume_data:
            st.metric(
                label="Búsquedas/mes (EST)",
                value=format_fn(current_value),
                help="⚠️ ESTIMACIÓN basada en heurísticas, NO datos reales de Google"
            )
        else:
            st.metric(
                label="Índice actual",
                value=f"{current_value:.0f}",
                help="Índice Google Trends (0-100)"
            )

    with col2:
        delta_color = "normal" if growth >= 0 else "inverse"
        st.metric(
            label="Crecimiento",
            value=f"{growth:+.1f}%",
            delta=f"vs período anterior",
            delta_color=delta_color
        )

    with col3:
        st.metric(
            label="Promedio",
            value=format_fn(avg_value)
        )

    with col4:
        peak = df[y_col].max()
        st.metric(
            label="Pico máximo",
            value=format_fn(peak)
        )

    # Indicador de estimación y rango de fechas
    date_range_str = ""
    if len(df) > 0:
        date_start = df["date"].min().strftime("%b %Y")
        date_end = df["date"].max().strftime("%b %Y")
        date_range_str = f"📅 Datos: {date_start} → {date_end}"

    if volume_data:
        confidence = volume_data["current"].get("confidence_label", "Media")
        st.caption(f"⚠️ **Volumen ESTIMADO** (no son datos reales de Google) · Confianza: {confidence}")
        st.caption(f"💡 Para volúmenes reales usa Google Ads Keyword Planner. {date_range_str}")
    else:
        st.caption(f"📊 **Índice Google Trends** (0-100) · Dato real de Google. {date_range_str}")
        st.caption("💡 El índice 100 = máximo del período. Usa los botones de zoom (1M, 3M, 6M, 1A) para navegar.")

    # Controles
    col_traj, col_export = st.columns([3, 1])

    with col_traj:
        show_traj = st.checkbox("Mostrar trayectoria", value=show_trajectory, key=f"traj_{keyword}")

    with col_export:
        # Preparar CSV para descarga
        csv_data = df[["date", "value"]].to_csv(index=False)
        st.download_button(
            label="📥 Exportar",
            data=csv_data,
            file_name=f"trend_{keyword}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    # Mostrar gráfico
    st.plotly_chart(fig, width="stretch")


def render_mini_sparkline(
    values: list,
    color: str = "#7C3AED",
    height: int = 40,
    width: int = 120
) -> go.Figure:
    """
    Crea un mini sparkline para usar en cards

    Returns:
        Figura de Plotly
    """
    if not values or len(values) < 2:
        return None

    fig = go.Figure()

    # Determinar color basado en tendencia
    if values[-1] > values[0]:
        line_color = "#10B981"  # Verde - subiendo
    elif values[-1] < values[0]:
        line_color = "#EF4444"  # Rojo - bajando
    else:
        line_color = color

    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        line=dict(color=line_color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba({int(line_color[1:3], 16)}, {int(line_color[3:5], 16)}, {int(line_color[5:7], 16)}, 0.1)',
        hoverinfo='skip'
    ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=0, b=0),
        height=height,
        width=width,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    return fig


def render_comparison_chart(
    data_by_country: dict,
    keyword: str,
    height: int = 400
) -> None:
    """
    Renderiza comparativa de tendencias por país

    Args:
        data_by_country: Dict con país -> timeline_data
    """
    import re

    if not data_by_country:
        st.warning("No hay datos para comparar")
        return

    colors = {
        "ES": "#F5C518",  # Amarillo - España
        "PT": "#10B981",  # Verde - Portugal
        "FR": "#3B82F6",  # Azul - Francia
        "IT": "#EF4444",  # Rojo - Italia
        "DE": "#8B5CF6"   # Púrpura - Alemania
    }

    country_names = {
        "ES": "España",
        "PT": "Portugal",
        "FR": "Francia",
        "IT": "Italia",
        "DE": "Alemania"
    }

    fig = go.Figure()
    has_data = False

    for country, data in data_by_country.items():
        if not data.get("success") or not data.get("timeline_data"):
            continue

        timeline = data["timeline_data"]

        dates = []
        values = []

        for point in timeline:
            if "date" in point and "values" in point and len(point["values"]) > 0:
                date_str = point["date"]

                # Limpiar rangos
                if " – " in date_str:
                    date_str = date_str.split(" – ")[0]
                if " - " in date_str:
                    date_str = date_str.split(" - ")[0]
                date_str = date_str.strip()

                date = None

                # Intentar múltiples formatos
                formats_to_try = [
                    "%b %d, %Y", "%B %d, %Y", "%b %Y", "%B %Y",
                    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y"
                ]

                for fmt in formats_to_try:
                    try:
                        date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue

                # Fallback con regex
                if date is None:
                    month_map = {
                        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                    }
                    match = re.search(r'(\w+)\s+(\d{4})', date_str.lower())
                    if match:
                        month_str, year = match.groups()
                        month_num = month_map.get(month_str[:3])
                        if month_num:
                            date = datetime(int(year), month_num, 1)

                if date:
                    dates.append(date)
                    val = point["values"][0].get("extracted_value", 0)
                    values.append(float(val) if val else 0)

        if dates and values:
            has_data = True
            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name=f"{country_names.get(country, country)}",
                line=dict(color=colors.get(country, "#666"), width=2),
                hovertemplate=f'<b>{country_names.get(country, country)}</b><br>%{{x|%b %Y}}: %{{y}}<extra></extra>'
            ))

    if not has_data:
        st.warning("No se pudieron procesar los datos de ningún país")
        return

    fig.update_layout(
        title=f"Comparativa por país: {keyword}",
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.05)',
            title="Índice de interés"
        ),
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=height,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    st.plotly_chart(fig, width="stretch")

