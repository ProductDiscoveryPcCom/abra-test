"""
Score Cards Component
Tarjetas de Trend Score, Potential Score y Oportunidad
"""

import plotly.graph_objects as go
import streamlit as st
import math


def render_score_cards(
    trend_score: dict,
    potential_score: dict,
    opportunity: dict
) -> None:
    """
    Renderiza las tres tarjetas de scoring principales
    
    Args:
        trend_score: Dict con score, grade, factors, explanation
        potential_score: Dict con score, grade, factors, explanation
        opportunity: Dict con level, color, icon, action
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        _render_score_ring(
            title="Trend Score",
            score=trend_score.get("score", 0),
            grade=trend_score.get("grade", "F"),
            color="#F5C518",
            subtitle="¿Qué tan trendy es ahora?",
            tooltip=trend_score.get("explanation", "")
        )
    
    with col2:
        _render_score_ring(
            title="Potential Score",
            score=potential_score.get("score", 0),
            grade=potential_score.get("grade", "F"),
            color="#7C3AED",
            subtitle="¿Va a explotar?",
            tooltip=potential_score.get("explanation", "")
        )
    
    with col3:
        _render_opportunity_card(opportunity)


def _render_score_ring(
    title: str,
    score: int,
    grade: str,
    color: str,
    subtitle: str = "",
    tooltip: str = ""
) -> None:
    """Renderiza una tarjeta con ring de score"""
    
    # Crear ring gauge con Plotly
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={'suffix': "", 'font': {'size': 40, 'color': '#1A1A2E', 'family': 'Space Grotesk'}},
        gauge={
            'axis': {'range': [0, 100], 'showticklabels': False, 'ticks': ''},
            'bar': {'color': color, 'thickness': 0.8},
            'bgcolor': '#F3F4F6',
            'borderwidth': 0,
            'steps': [],
            'threshold': {
                'line': {'color': color, 'width': 0},
                'thickness': 0,
                'value': score
            }
        },
        domain={'x': [0.1, 0.9], 'y': [0.15, 0.85]}
    ))
    
    # Añadir grade en el centro inferior (más abajo)
    fig.add_annotation(
        x=0.5, y=0.02,
        text=grade,
        font=dict(size=20, color=color, family='Space Grotesk'),
        showarrow=False
    )
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=30),
        height=200,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Space Grotesk')
    )
    
    # Card container
    st.markdown(
        f'''
        <div style="background: white; border-radius: 12px; padding: 16px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-left: 4px solid {color};">
            <h4 style="margin: 0 0 4px 0; font-family: Space Grotesk; font-size: 1rem; color: #1A1A2E;">
                {title}
            </h4>
            <p style="margin: 0; font-size: 0.75rem; color: #64748B;">{subtitle}</p>
        </div>
        ''',
        unsafe_allow_html=True
    )
    
    st.plotly_chart(fig, width="stretch", key=f"ring_{title}")
    
    if tooltip:
        st.caption(f"💡 {tooltip}")


def _render_opportunity_card(opportunity: dict) -> None:
    """Renderiza la tarjeta de nivel de oportunidad"""
    level = opportunity.get("level", "N/A")
    color = opportunity.get("color", "#666")
    icon = opportunity.get("icon", "📊")
    action = opportunity.get("action", "")
    combined_score = opportunity.get("combined_score", 0)
    
    # Determinar color de fondo
    bg_colors = {
        "ALTA": "#D1FAE5",
        "MEDIA": "#FEF3C7",
        "BAJA": "#F3F4F6",
        "MUY BAJA": "#FEE2E2"
    }
    bg_color = bg_colors.get(level, "#F3F4F6")
    
    st.markdown(
        f'''
        <div style="background: {bg_color}; border-radius: 12px; padding: 24px; 
        text-align: center; height: 100%; min-height: 280px; display: flex; 
        flex-direction: column; justify-content: center; align-items: center;">
            <div style="font-size: 3rem; margin-bottom: 8px;">{icon}</div>
            <h3 style="margin: 0; font-family: Space Grotesk; font-size: 1.5rem; 
            color: {color}; font-weight: 700;">
                {level}
            </h3>
            <p style="margin: 8px 0 0 0; font-size: 0.875rem; color: #4B5563;">
                Oportunidad
            </p>
            <div style="margin-top: 16px; padding: 8px 16px; background: white; 
            border-radius: 8px; font-size: 0.875rem; color: #1A1A2E;">
                {action}
            </div>
            <p style="margin: 12px 0 0 0; font-size: 0.75rem; color: #64748B;">
                Score combinado: {combined_score}/100
            </p>
        </div>
        ''',
        unsafe_allow_html=True
    )


def render_opportunity_badge(opportunity: dict) -> None:
    """Renderiza un badge compacto de oportunidad"""
    level = opportunity.get("level", "N/A")
    color = opportunity.get("color", "#666")
    icon = opportunity.get("icon", "📊")
    
    st.markdown(
        f'''
        <span style="display: inline-flex; align-items: center; gap: 6px; 
        background: {color}20; color: {color}; padding: 4px 12px; 
        border-radius: 9999px; font-size: 0.875rem; font-weight: 600;">
            {icon} {level}
        </span>
        ''',
        unsafe_allow_html=True
    )


def render_score_breakdown(
    title: str,
    factors: dict,
    color: str = "#7C3AED"
) -> None:
    """
    Renderiza el desglose de factores de un score
    
    Args:
        factors: Dict con nombre_factor -> valor (0-100)
    """
    st.markdown(f"**{title}**")
    
    factor_names = {
        "current_vs_avg": "Valor actual vs media",
        "growth": "Crecimiento",
        "momentum": "Momentum",
        "consistency": "Consistencia",
        "acceleration": "Aceleración",
        "early_stage": "Etapa temprana",
        "rising_queries": "Queries en crecimiento",
        "growth_room": "Espacio de crecimiento"
    }
    
    for key, value in factors.items():
        display_name = factor_names.get(key, key.replace("_", " ").title())
        
        # Barra de progreso
        st.markdown(
            f'''
            <div style="margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; 
                margin-bottom: 4px; font-size: 0.75rem;">
                    <span style="color: #4B5563;">{display_name}</span>
                    <span style="color: #1A1A2E; font-weight: 600;">{value}</span>
                </div>
                <div style="height: 6px; background: #F3F4F6; border-radius: 3px; 
                overflow: hidden;">
                    <div style="height: 100%; width: {value}%; background: {color}; 
                    border-radius: 3px;"></div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )
