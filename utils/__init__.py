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
    """Renderiza el logo y título de la app con mascota Abra"""
    from pathlib import Path
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        # Intentar cargar la imagen de la mascota
        mascot_path = Path(__file__).parent.parent / "assets" / "images" / "abra_mascot.png"
        if mascot_path.exists():
            st.image(str(mascot_path), width=56)
        else:
            st.markdown('<span style="font-size: 2.5rem;">🔮</span>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(
            '''<div style="padding-top: 4px;">
                <span style="font-family: 'Space Grotesk', sans-serif; font-size: 1.4rem;
                font-weight: 700; background: linear-gradient(135deg, #F5C518 0%, #7C3AED 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                background-clip: text;">Abra Trend Hunter</span>
                <p style="margin: 0; font-size: 0.75rem; color: #64748B;">
                    🔮 Detecta tendencias antes que nadie
                </p>
            </div>''',
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
    """Renderiza el estado de las APIs en el sidebar con verificación de conectividad"""
    status = check_api_keys()
    
    # Inicializar estado de conexión en session_state si no existe
    if "api_connection_status" not in st.session_state:
        st.session_state.api_connection_status = {}
    
    st.sidebar.markdown("#### 🔌 Estado APIs")
    
    # Definición de APIs con sus módulos de test
    apis_config = [
        {
            "name": "SerpAPI",
            "key": "serpapi",
            "configured": status["serpapi"],
            "required": True,
            "test_module": "google_trends",
            "secret_key": "SERPAPI_KEY"
        },
        {
            "name": "Perplexity",
            "key": "perplexity",
            "configured": status["perplexity"],
            "required": False,
            "test_module": "market_intelligence",
            "secret_key": "PERPLEXITY_API_KEY"
        },
        {
            "name": "Claude",
            "key": "anthropic",
            "configured": status["anthropic"],
            "required": False,
            "test_module": "claude_provider",
            "secret_key": "ANTHROPIC_API_KEY"
        },
        {
            "name": "GPT-4o",
            "key": "openai",
            "configured": status["openai"],
            "required": False,
            "test_module": "openai_provider",
            "secret_key": "OPENAI_API_KEY"
        },
        {
            "name": "YouTube",
            "key": "youtube",
            "configured": status["youtube"],
            "required": False,
            "test_module": "youtube",
            "secret_key": "YOUTUBE_API_KEY"
        },
    ]
    
    # Renderizar cada API
    for api in apis_config:
        name = api["name"]
        configured = api["configured"]
        required = api["required"]
        conn_status = st.session_state.api_connection_status.get(api["key"])
        
        if not configured:
            # No configurada
            icon = "⚠️" if required else "○"
            status_text = "No configurada"
            color = "#EF4444" if required else "#9CA3AF"
            bg_color = "#FEE2E2" if required else "#F3F4F6"
        elif conn_status is None:
            # Configurada pero no verificada
            icon = "🔑"
            status_text = "Configurada"
            color = "#F59E0B"
            bg_color = "#FEF3C7"
        elif conn_status[0]:  # Conexión exitosa
            icon = "✅"
            status_text = conn_status[1] if len(conn_status[1]) < 25 else "Operativa"
            color = "#10B981"
            bg_color = "#D1FAE5"
        else:  # Conexión fallida
            icon = "❌"
            status_text = conn_status[1] if len(conn_status[1]) < 20 else "Error"
            color = "#EF4444"
            bg_color = "#FEE2E2"
        
        st.sidebar.markdown(
            f'''<div style="display: flex; justify-content: space-between; align-items: center;
                padding: 6px 10px; margin: 4px 0; border-radius: 6px;
                background: {bg_color}; font-size: 0.85rem;">
                <span style="font-weight: 500;">{icon} {name}</span>
                <span style="color: {color}; font-size: 0.7rem; 
                      max-width: 100px; overflow: hidden; text-overflow: ellipsis;
                      white-space: nowrap;">{status_text}</span>
            </div>''',
            unsafe_allow_html=True
        )
    
    # Botón para verificar conectividad
    if st.sidebar.button("🔄 Verificar conexiones", use_container_width=True, key="verify_apis"):
        _verify_all_connections(apis_config)
        st.rerun()


def _verify_all_connections(apis_config: list):
    """Verifica la conexión de todas las APIs configuradas"""
    import streamlit as st
    
    for api in apis_config:
        if not api["configured"]:
            continue
        
        key = api["key"]
        test_module = api["test_module"]
        secret_key = api["secret_key"]
        
        try:
            api_key = st.secrets.get(secret_key, "")
            
            if test_module == "google_trends":
                from modules.google_trends import GoogleTrendsModule
                module = GoogleTrendsModule(api_key)
                result = module.test_connection()
                st.session_state.api_connection_status[key] = result
                
            elif test_module == "market_intelligence":
                from modules.market_intelligence import MarketIntelligence
                module = MarketIntelligence(api_key)
                result = module.test_connection()
                st.session_state.api_connection_status[key] = result
                
            elif test_module == "claude_provider":
                from modules.providers.claude_provider import ClaudeProvider
                provider = ClaudeProvider(api_key)
                result = provider.test_connection()
                st.session_state.api_connection_status[key] = result
                
            elif test_module == "openai_provider":
                from modules.providers.openai_provider import OpenAIProvider
                provider = OpenAIProvider(api_key)
                result = provider.test_connection()
                st.session_state.api_connection_status[key] = result
                
            elif test_module == "youtube":
                from modules.youtube import YouTubeModule
                module = YouTubeModule(api_key)
                result = module.test_connection()
                st.session_state.api_connection_status[key] = result
                
            else:
                # API sin test_connection implementado
                st.session_state.api_connection_status[key] = (True, "Configurada")
                
        except Exception as e:
            st.session_state.api_connection_status[key] = (False, str(e)[:30])


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
        "selected_timeframe": "today 5-y",
        "search_category": 5,  # Informática
        "exact_match": True,
        "show_volume_estimate": False,
        "ai_provider": "claude",
        "show_trajectory": True,
        "api_connection_status": {}
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
    Renderiza un estado de carga con animación y mascota Abra

    Args:
        message: Mensaje a mostrar (será sanitizado)
    """
    from pathlib import Path
    
    # Sanitizar el mensaje para prevenir XSS
    safe_message = sanitize_html(message)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        # Mascota centrada
        mascot_path = Path(__file__).parent.parent / "assets" / "images" / "abra_mascot.png"
        if mascot_path.exists():
            st.image(str(mascot_path), width=64)
        else:
            st.markdown(
                '<div style="text-align: center; font-size: 2.5rem;">🔮</div>',
                unsafe_allow_html=True
            )
        
        # Mensaje y spinner
        st.markdown(
            f'<p style="text-align: center; color: #7C3AED; font-weight: 500;">{safe_message}</p>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<p style="text-align: center; color: #F5C518; font-size: 1.5rem;">• • •</p>',
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
    """Renderiza estado vacío inicial con mascota Abra"""
    from pathlib import Path
    
    # Container centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Mascota centrada
        mascot_path = Path(__file__).parent.parent / "assets" / "images" / "abra_mascot.png"
        if mascot_path.exists():
            subcol1, subcol2, subcol3 = st.columns([1, 1, 1])
            with subcol2:
                st.image(str(mascot_path), width=120)
        else:
            st.markdown(
                '<div style="text-align: center; font-size: 5rem;">🔮</div>',
                unsafe_allow_html=True
            )
        
        # Texto
        st.markdown(
            '''<div style="text-align: center; padding: 20px 0; color: #64748B;">
                <h3 style="color: #1A1A2E; margin-bottom: 8px; font-family: 'Space Grotesk', sans-serif;">
                    ¡Abra está listo para detectar tendencias!
                </h3>
                <p style="margin-bottom: 24px;">
                    Introduce una marca o producto para analizar su potencial
                </p>
            </div>''',
            unsafe_allow_html=True
        )
        
        # Pills de ejemplo
        pill_cols = st.columns(3)
        examples = [
            ("Beelink", "#F5C518", "#1A1A2E"),
            ("Framework Laptop", "#7C3AED", "white"),
            ("Steam Deck", "#10B981", "white")
        ]
        for i, (text, bg, color) in enumerate(examples):
            with pill_cols[i]:
                st.markdown(
                    f'<div style="background: {bg}; padding: 8px 12px; border-radius: 20px; '
                    f'text-align: center; font-size: 0.85rem; color: {color}; font-weight: 500;">{text}</div>',
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

