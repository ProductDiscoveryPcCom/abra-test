"""
Abra Trend Hunter - Utilities
Funciones auxiliares y helpers
"""

import streamlit as st
from datetime import datetime
import html as html_module

# Import de validaciones
from .validation import (
    sanitize_html, sanitize_for_query, sanitize_filename,
    safe_float, safe_int, safe_divide, safe_percentage_change,
    safe_list, safe_dict, safe_get, safe_average,
    validate_hex_color, hex_to_rgba
)


def load_css():
    """Carga los estilos CSS personalizados"""
    try:
        with open("assets/custom.css", "r", encoding="utf-8") as f:
            css_content = f.read()
            # No escapamos el CSS ya que es nuestro archivo estático
            st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass
    except Exception:
        pass  # Silenciar otros errores de lectura


def render_logo():
    """Renderiza el logo y título de la app"""
    # HTML estático seguro - no hay input de usuario
    st.markdown(
        '''
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 1rem;">
            <span style="font-size: 2.5rem;">🔮</span>
            <div>
                <span style="font-family: 'Space Grotesk', sans-serif; font-size: 1.75rem;
                font-weight: 700; background: linear-gradient(135deg, #F5C518 0%, #7C3AED 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text;">Abra Trend Hunter</span>
                <p style="margin: 0; font-size: 0.8rem; color: #64748B;">
                    Detecta tendencias antes que nadie
                </p>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )


def check_api_keys() -> dict:
    """
    Verifica qué API keys están configuradas

    Returns:
        Dict con estado de cada API key
    """
    try:
        return {
            "serpapi": bool(st.secrets.get("SERPAPI_KEY", "")),
            "anthropic": bool(st.secrets.get("ANTHROPIC_API_KEY", "")),
            "openai": bool(st.secrets.get("OPENAI_API_KEY", "")),
            "perplexity": bool(st.secrets.get("PERPLEXITY_API_KEY", "")),
            "youtube": bool(st.secrets.get("YOUTUBE_API_KEY", "")),
            "aliexpress": bool(st.secrets.get("ALIEXPRESS_KEY", ""))
        }
    except Exception:
        return {
            "serpapi": False,
            "anthropic": False,
            "openai": False,
            "perplexity": False,
            "youtube": False,
            "aliexpress": False
        }


def render_api_status():
    """Renderiza el estado de las APIs en el sidebar"""
    status = check_api_keys()

    st.sidebar.markdown("#### 🔑 Estado APIs")

    apis = [
        ("SerpAPI", status["serpapi"], "Requerida"),
        ("YouTube", status["youtube"], "Opcional"),
        ("Claude", status["anthropic"], "Opcional"),
        ("GPT-4", status["openai"], "Opcional"),
        ("Perplexity", status["perplexity"], "Opcional"),
        ("AliExpress", status["aliexpress"], "Opcional")
    ]

    for name, configured, required in apis:
        if configured:
            icon = "✅"
            color = "#10B981"
        else:
            icon = "⚠️" if required == "Requerida" else "○"
            color = "#EF4444" if required == "Requerida" else "#9CA3AF"

        # Los valores aquí son estáticos/internos, no necesitan escape
        st.sidebar.markdown(
            f'<div style="display: flex; justify-content: space-between; '
            f'padding: 4px 0; font-size: 0.85rem;">'
            f'<span>{icon} {name}</span>'
            f'<span style="color: {color}; font-size: 0.75rem;">{required}</span>'
            f'</div>',
            unsafe_allow_html=True
        )


def format_number(num: float) -> str:
    """
    Formatea números grandes (ej: 64000 -> 64K)

    Args:
        num: Número a formatear

    Returns:
        String formateado
    """
    num = safe_float(num, 0)

    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return f"{num:.0f}"


def format_growth(growth: float) -> tuple:
    """
    Formatea el crecimiento con color e icono

    Args:
        growth: Porcentaje de crecimiento

    Returns:
        (texto_formateado, color)
    """
    growth = safe_float(growth, 0)

    if growth > 0:
        return f"▲ {growth:.1f}%", "#10B981"
    elif growth < 0:
        return f"▼ {abs(growth):.1f}%", "#EF4444"
    else:
        return "→ 0%", "#6B7280"


def get_time_greeting() -> str:
    """Retorna saludo basado en la hora"""
    try:
        hour = datetime.now().hour
        if hour < 12:
            return "Buenos días"
        elif hour < 20:
            return "Buenas tardes"
        else:
            return "Buenas noches"
    except Exception:
        return "Hola"


def init_session_state():
    """Inicializa el estado de la sesión"""
    defaults = {
        "search_history": [],
        "current_keyword": "",
        "selected_country": "ES",
        "selected_timeframe": "today 12-m",
        "ai_provider": "claude",
        "show_trajectory": True
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_to_history(keyword: str):
    """
    Añade un término al historial de búsquedas

    Args:
        keyword: Término de búsqueda
    """
    if not keyword:
        return

    # Sanitizar el keyword
    keyword_clean = sanitize_for_query(keyword)

    if not keyword_clean:
        return

    # Verificar que existe el historial
    if "search_history" not in st.session_state:
        st.session_state.search_history = []

    # Evitar duplicados
    if keyword_clean not in st.session_state.search_history:
        st.session_state.search_history.insert(0, keyword_clean)
        # Mantener solo los últimos 10
        st.session_state.search_history = st.session_state.search_history[:10]


def render_search_history():
    """
    Renderiza el historial de búsquedas como pills clickeables

    Returns:
        Término seleccionado o None
    """
    if "search_history" not in st.session_state or not st.session_state.search_history:
        return None

    st.markdown("**Búsquedas recientes:**")

    history = st.session_state.search_history[:5]
    cols = st.columns(min(5, len(history)))

    selected = None
    for i, term in enumerate(history):
        with cols[i]:
            # Sanitizar para mostrar
            term_display = sanitize_html(term)[:30]
            if st.button(term_display, key=f"hist_{i}", width="stretch"):
                selected = term

    return selected


def render_loading_state(message: str = "Analizando tendencias..."):
    """
    Renderiza un estado de carga con animación

    Args:
        message: Mensaje a mostrar (será sanitizado)
    """
    # Sanitizar el mensaje para prevenir XSS
    safe_message = sanitize_html(message)

    st.markdown(
        f'''
        <div style="display: flex; align-items: center; justify-content: center;
        padding: 40px; gap: 12px;">
            <div class="loading" style="font-size: 2rem;">🔮</div>
            <span style="color: #64748B; font-size: 1rem;">{safe_message}</span>
        </div>
        ''',
        unsafe_allow_html=True
    )


def render_error_state(message: str, suggestion: str = None):
    """
    Renderiza un estado de error

    Args:
        message: Mensaje de error (será sanitizado)
        suggestion: Sugerencia opcional (será sanitizada)
    """
    # Sanitizar mensajes
    safe_message = sanitize_html(message)
    st.error(safe_message)

    if suggestion:
        safe_suggestion = sanitize_html(suggestion)
        st.info(f"💡 {safe_suggestion}")


def render_empty_state():
    """Renderiza estado vacío inicial"""
    # HTML estático seguro - no hay input de usuario
    st.markdown(
        '''
        <div style="text-align: center; padding: 60px 20px; color: #64748B;">
            <div style="font-size: 4rem; margin-bottom: 16px;">🔮</div>
            <h3 style="color: #1A1A2E; margin-bottom: 8px;">
                Busca una marca o producto
            </h3>
            <p style="margin-bottom: 24px;">
                Introduce un término para analizar su tendencia
            </p>
            <div style="display: flex; gap: 8px; justify-content: center; flex-wrap: wrap;">
                <span style="background: #F3F4F6; padding: 6px 12px; border-radius: 6px;
                font-size: 0.85rem;">Ej: Beelink</span>
                <span style="background: #F3F4F6; padding: 6px 12px; border-radius: 6px;
                font-size: 0.85rem;">Framework Laptop</span>
                <span style="background: #F3F4F6; padding: 6px 12px; border-radius: 6px;
                font-size: 0.85rem;">Steam Deck</span>
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )


# Re-export de funciones de validación para uso fácil
__all__ = [
    'load_css', 'render_logo', 'check_api_keys', 'render_api_status',
    'format_number', 'format_growth', 'get_time_greeting',
    'init_session_state', 'add_to_history', 'render_search_history',
    'render_loading_state', 'render_error_state', 'render_empty_state',
    'sanitize_html', 'sanitize_for_query', 'safe_float', 'safe_int',
    'safe_divide', 'safe_get', 'safe_list', 'safe_dict'
]

