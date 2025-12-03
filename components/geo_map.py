"""
Geo Map Component
Visualización de interés por país (ES, PT, FR, IT, DE)
"""

import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from typing import Dict


# Configuración de países
COUNTRIES = {
    "ES": {"name": "España", "flag": "🇪🇸", "color": "#F5C518"},
    "PT": {"name": "Portugal", "flag": "🇵🇹", "color": "#10B981"},
    "FR": {"name": "Francia", "flag": "🇫🇷", "color": "#3B82F6"},
    "IT": {"name": "Italia", "flag": "🇮🇹", "color": "#EF4444"},
    "DE": {"name": "Alemania", "flag": "🇩🇪", "color": "#8B5CF6"}
}


def render_geo_comparison(
    country_data: dict,
    keyword: str
) -> None:
    """
    Renderiza la comparativa de interés por país
    
    Args:
        country_data: Dict con código_país -> {timeline_data, growth_rate, current_value}
        keyword: Término buscado
    """
    st.markdown("#### 🌍 Interés por país")
    
    if not country_data:
        st.info("No hay datos geográficos disponibles")
        return
    
    # Calcular valores agregados por país
    country_scores = {}
    
    for code, data in country_data.items():
        if not data.get("success"):
            continue
        
        timeline = data.get("timeline_data", [])
        if not timeline:
            continue
        
        # Calcular valor promedio
        values = []
        for point in timeline:
            if "values" in point and len(point["values"]) > 0:
                val = point["values"][0].get("extracted_value", 0)
                if val:
                    values.append(float(val))
        
        if values:
            avg_value = sum(values) / len(values)
            current_value = values[-1] if values else 0
            
            # Calcular crecimiento
            if len(values) >= 4:
                recent = sum(values[-2:]) / 2
                previous = sum(values[:2]) / 2
                growth = ((recent - previous) / previous * 100) if previous > 0 else 0
            else:
                growth = 0
            
            country_scores[code] = {
                "avg_value": avg_value,
                "current_value": current_value,
                "growth": growth,
                "values": values
            }
    
    if not country_scores:
        st.warning("No se pudieron procesar los datos de países")
        return
    
    # Normalizar valores (el máximo = 100)
    max_avg = max(s["avg_value"] for s in country_scores.values())
    
    if max_avg > 0:
        for code in country_scores:
            country_scores[code]["normalized"] = (country_scores[code]["avg_value"] / max_avg) * 100
    
    # Ordenar por valor
    sorted_countries = sorted(
        country_scores.items(),
        key=lambda x: x[1]["normalized"],
        reverse=True
    )
    
    # Opción de visualización
    view_type = st.radio(
        "Vista",
        ["Barras", "Mapa"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if view_type == "Barras":
        _render_bar_comparison(sorted_countries)
    else:
        _render_choropleth_map(sorted_countries, keyword)
    
    # Tabla detallada
    st.markdown("##### Detalle por país")
    _render_country_table(sorted_countries)


def _render_bar_comparison(sorted_countries: list) -> None:
    """Renderiza barras horizontales de comparación"""
    
    for code, scores in sorted_countries:
        country_info = COUNTRIES.get(code, {"name": code, "flag": "🏳️", "color": "#666"})
        normalized = scores.get("normalized", 0)
        growth = scores.get("growth", 0)
        
        # Determinar icono de tendencia
        if growth > 10:
            trend_icon = "📈"
            growth_color = "#10B981"
        elif growth < -10:
            trend_icon = "📉"
            growth_color = "#EF4444"
        else:
            trend_icon = "➡️"
            growth_color = "#6B7280"
        
        st.markdown(
            f'''
            <div style="display: flex; align-items: center; gap: 12px; 
            padding: 12px; margin-bottom: 8px; background: white; 
            border-radius: 8px; border: 1px solid #E5E7EB;">
                <span style="font-size: 1.5rem;">{country_info["flag"]}</span>
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between; 
                    margin-bottom: 4px;">
                        <span style="font-weight: 600; color: #1A1A2E;">
                            {country_info["name"]}
                        </span>
                        <span style="color: {growth_color}; font-size: 0.85rem;">
                            {trend_icon} {growth:+.1f}%
                        </span>
                    </div>
                    <div style="height: 8px; background: #F3F4F6; border-radius: 4px; 
                    overflow: hidden;">
                        <div style="height: 100%; width: {normalized}%; 
                        background: {country_info["color"]}; border-radius: 4px; 
                        transition: width 0.3s;"></div>
                    </div>
                </div>
                <span style="font-weight: 600; color: #1A1A2E; min-width: 40px; 
                text-align: right;">{normalized:.0f}</span>
            </div>
            ''',
            unsafe_allow_html=True
        )


def _render_choropleth_map(sorted_countries: list, keyword: str) -> None:
    """Renderiza mapa de calor de Europa"""
    
    # Preparar datos para Plotly
    country_codes_iso3 = {
        "ES": "ESP",
        "PT": "PRT",
        "FR": "FRA",
        "IT": "ITA",
        "DE": "DEU"
    }
    
    data = {
        "iso_alpha": [],
        "country": [],
        "value": []
    }
    
    for code, scores in sorted_countries:
        if code in country_codes_iso3:
            data["iso_alpha"].append(country_codes_iso3[code])
            data["country"].append(COUNTRIES[code]["name"])
            data["value"].append(scores.get("normalized", 0))
    
    fig = go.Figure(data=go.Choropleth(
        locations=data["iso_alpha"],
        z=data["value"],
        text=data["country"],
        colorscale=[
            [0, "#F3F4F6"],
            [0.5, "#FEF3C7"],
            [1, "#F5C518"]
        ],
        autocolorscale=False,
        marker_line_color='white',
        marker_line_width=1,
        colorbar_title="Interés",
        hovertemplate='<b>%{text}</b><br>Interés: %{z:.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        geo=dict(
            scope='europe',
            showframe=False,
            showcoastlines=True,
            coastlinecolor='#E5E7EB',
            showland=True,
            landcolor='#FAFAFA',
            projection_type='natural earth',
            center=dict(lat=48, lon=10),
            lataxis_range=[35, 60],
            lonaxis_range=[-12, 25]
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=350,
        title=dict(
            text=f"Interés en '{keyword}' por país",
            font=dict(size=14, family='Space Grotesk')
        )
    )
    
    st.plotly_chart(fig, width="stretch")


def _render_country_table(sorted_countries: list) -> None:
    """Renderiza tabla detallada por país"""
    
    # Crear columnas para la tabla
    cols = st.columns([2, 2, 2, 2, 2])
    
    # Headers
    headers = ["País", "Interés", "Actual", "Crecimiento", "Tendencia"]
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")
    
    # Filas
    for code, scores in sorted_countries:
        country_info = COUNTRIES.get(code, {"name": code, "flag": "🏳️"})
        
        cols = st.columns([2, 2, 2, 2, 2])
        
        cols[0].markdown(f"{country_info['flag']} {country_info['name']}")
        cols[1].markdown(f"{scores.get('normalized', 0):.0f}/100")
        cols[2].markdown(f"{scores.get('current_value', 0):.0f}")
        
        growth = scores.get("growth", 0)
        growth_color = "#10B981" if growth > 0 else "#EF4444" if growth < 0 else "#6B7280"
        cols[3].markdown(
            f'<span style="color: {growth_color};">{growth:+.1f}%</span>',
            unsafe_allow_html=True
        )
        
        # Mini sparkline
        values = scores.get("values", [])
        if values and len(values) >= 3:
            trend = "📈" if values[-1] > values[0] else "📉" if values[-1] < values[0] else "➡️"
            cols[4].markdown(trend)
        else:
            cols[4].markdown("—")


def render_country_selector(
    default_countries: list = None
) -> list:
    """
    Renderiza selector de países
    
    Returns:
        Lista de códigos de países seleccionados
    """
    if default_countries is None:
        default_countries = ["ES", "PT", "FR", "IT", "DE"]
    
    options = [f"{COUNTRIES[c]['flag']} {COUNTRIES[c]['name']}" for c in COUNTRIES]
    
    selected = st.multiselect(
        "Países",
        options,
        default=[f"{COUNTRIES[c]['flag']} {COUNTRIES[c]['name']}" for c in default_countries],
        help="Selecciona los países a comparar"
    )
    
    # Convertir de vuelta a códigos
    selected_codes = []
    for s in selected:
        for code, info in COUNTRIES.items():
            if f"{info['flag']} {info['name']}" == s:
                selected_codes.append(code)
                break
    
    return selected_codes
