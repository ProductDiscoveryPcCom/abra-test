"""
Keyword Table Component
Tabla de "La gente también busca" con tabs, filtros y paginación
"""

import streamlit as st
import html
import math
from typing import List, Optional


def render_keyword_table(
    categorized_data: dict,
    items_per_page: int = 30
) -> None:
    """
    Renderiza la sección "La gente también busca" con tabs y filtros
    
    Args:
        categorized_data: Dict con 'categorized' (questions, comparatives, others, all)
        items_per_page: Número de items por página
    """
    st.markdown("#### 🔎 La gente también busca")
    
    categorized = categorized_data.get("categorized", {})
    total = categorized_data.get("total_count", 0)
    
    all_items = categorized.get("all", [])
    questions = categorized.get("questions", [])
    comparatives = categorized.get("comparatives", [])
    others = categorized.get("others", [])
    
    # Header con filtros
    col1, col2 = st.columns([3, 1])
    
    with col2:
        sort_options = ["Relevancia", "A-Z", "Z-A"]
        sort_by = st.selectbox("Ordenar por", sort_options, key="kw_sort", label_visibility="collapsed")
    
    # Tabs
    tab_all, tab_questions, tab_comparatives, tab_others = st.tabs([
        f"Todos ({len(all_items)})",
        f"Preguntas ({len(questions)})",
        f"Comparativas ({len(comparatives)})",
        f"Otros ({len(others)})"
    ])
    
    with tab_all:
        _render_keyword_grid(all_items, sort_by, items_per_page, "all")
    
    with tab_questions:
        _render_keyword_grid(questions, sort_by, items_per_page, "questions")
    
    with tab_comparatives:
        _render_keyword_grid(comparatives, sort_by, items_per_page, "comparatives")
    
    with tab_others:
        _render_keyword_grid(others, sort_by, items_per_page, "others")


def _render_keyword_grid(
    items: list,
    sort_by: str,
    items_per_page: int,
    key_prefix: str
) -> None:
    """Renderiza grid de keywords con paginación"""
    if not items:
        st.info("No hay datos disponibles")
        return
    
    # Ordenar
    if sort_by == "A-Z":
        items = sorted(items, key=str.lower)
    elif sort_by == "Z-A":
        items = sorted(items, key=str.lower, reverse=True)
    
    # Paginación
    total_pages = math.ceil(len(items) / items_per_page)
    
    if f"page_{key_prefix}" not in st.session_state:
        st.session_state[f"page_{key_prefix}"] = 1
    
    current_page = st.session_state[f"page_{key_prefix}"]
    
    # Calcular slice
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_items = items[start_idx:end_idx]
    
    # Renderizar en 3 columnas
    cols = st.columns(3)
    
    for i, item in enumerate(page_items):
        with cols[i % 3]:
            # Simular barra de volumen (relativa al primero)
            volume_pct = max(10, 100 - (i * 3))  # Decrece con la posición
            
            # Sanitizar item para evitar XSS
            safe_item = html.escape(str(item)) if item else ""
            
            st.markdown(
                f'''
                <div style="display: flex; align-items: center; gap: 8px; 
                padding: 8px 12px; margin-bottom: 6px; background: white; 
                border-radius: 6px; border: 1px solid #E5E7EB;">
                    <span style="flex: 1; font-size: 0.85rem; color: #374151; 
                    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                        {safe_item}
                    </span>
                    <div style="width: 60px; height: 6px; background: #F3F4F6; 
                    border-radius: 3px; overflow: hidden;">
                        <div style="height: 100%; width: {volume_pct}%; 
                        background: linear-gradient(90deg, #F5C518, #7C3AED); 
                        border-radius: 3px;"></div>
                    </div>
                </div>
                ''',
                unsafe_allow_html=True
            )
    
    # Paginación UI
    if total_pages > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        
        with col_prev:
            if st.button("← Anterior", disabled=current_page <= 1, key=f"prev_{key_prefix}"):
                st.session_state[f"page_{key_prefix}"] = current_page - 1
                st.rerun()
        
        with col_info:
            st.markdown(
                f'<p style="text-align: center; color: #6B7280; margin: 8px 0;">'
                f'Página {current_page} de {total_pages}</p>',
                unsafe_allow_html=True
            )
        
        with col_next:
            if st.button("Próximo →", disabled=current_page >= total_pages, key=f"next_{key_prefix}"):
                st.session_state[f"page_{key_prefix}"] = current_page + 1
                st.rerun()


def render_questions_panel(questions: list, show_depth: bool = True) -> None:
    """
    Renderiza panel dedicado de preguntas de usuarios (PAA expandido)
    
    Args:
        questions: Lista de dicts con question, snippet, source, link, depth
        show_depth: Mostrar indicador de profundidad de la pregunta
    """
    total = len(questions) if questions else 0
    st.markdown(f"#### ❓ Preguntas de usuarios ({total})")
    
    if not questions:
        st.info("No se encontraron preguntas frecuentes")
        return
    
    # Agrupar por profundidad si hay varias
    depths = set(q.get("depth", 0) for q in questions)
    
    if len(depths) > 1 and show_depth:
        # Mostrar tabs por profundidad
        depth_labels = {
            0: "🎯 Principales",
            1: "🔄 Relacionadas",
            2: "🔍 Profundas"
        }
        
        tabs = st.tabs([f"{depth_labels.get(d, f'Nivel {d}')} ({len([q for q in questions if q.get('depth', 0) == d])})" 
                       for d in sorted(depths)])
        
        for tab, depth in zip(tabs, sorted(depths)):
            with tab:
                depth_questions = [q for q in questions if q.get("depth", 0) == depth]
                _render_question_list(depth_questions, expanded=depth == 0)
    else:
        _render_question_list(questions, expanded=True)


def _render_question_list(questions: list, expanded: bool = False) -> None:
    """Renderiza lista de preguntas con expanders"""
    for i, q in enumerate(questions[:15]):
        question = html.escape(str(q.get("question", "")))
        snippet = html.escape(str(q.get("snippet", "")))
        source = html.escape(str(q.get("source", "")))
        link = q.get("link", "")
        
        # Validar que el link sea una URL válida
        if link and not link.startswith(('http://', 'https://')):
            link = ""
        
        with st.expander(f"**{question}**", expanded=expanded and i < 3):
            if snippet:
                st.markdown(
                    f'<p style="color: #4B5563; font-size: 0.9rem; margin-bottom: 8px;">'
                    f'{snippet}</p>',
                    unsafe_allow_html=True
                )
            
            if source and link:
                st.markdown(
                    f'<a href="{link}" target="_blank" style="color: #7C3AED; '
                    f'font-size: 0.8rem; text-decoration: none;">Fuente: {source} →</a>',
                    unsafe_allow_html=True
                )
    
    if len(questions) > 15:
        st.caption(f"... y {len(questions) - 15} preguntas más")


def render_keyword_pills(keywords: list, max_display: int = 15) -> None:
    """
    Renderiza keywords como pills/tags clickeables
    """
    if not keywords:
        return
    
    pills_html = ""
    for kw in keywords[:max_display]:
        pills_html += f'''
            <span style="display: inline-block; background: #F3F4F6; 
            border: 1px solid #E5E7EB; border-radius: 9999px; 
            padding: 4px 12px; margin: 4px; font-size: 0.8rem; 
            color: #374151; cursor: pointer; transition: all 0.2s;"
            onmouseover="this.style.background='#FEF3C7'; this.style.borderColor='#F5C518';"
            onmouseout="this.style.background='#F3F4F6'; this.style.borderColor='#E5E7EB';">
                {kw}
            </span>
        '''
    
    if len(keywords) > max_display:
        pills_html += f'''
            <span style="display: inline-block; color: #7C3AED; 
            padding: 4px 12px; margin: 4px; font-size: 0.8rem;">
                +{len(keywords) - max_display} más
            </span>
        '''
    
    st.markdown(
        f'<div style="line-height: 2.5;">{pills_html}</div>',
        unsafe_allow_html=True
    )


def render_search_suggestions(suggestions: list) -> None:
    """
    Renderiza sugerencias de búsqueda como lista simple
    """
    if not suggestions:
        return
    
    st.markdown("##### 💡 Sugerencias de búsqueda")
    
    for suggestion in suggestions[:10]:
        st.markdown(
            f'''
            <div style="padding: 8px 12px; margin-bottom: 4px; 
            border-left: 3px solid #F5C518; background: #FAFAFA;">
                <span style="color: #374151; font-size: 0.9rem;">{suggestion}</span>
            </div>
            ''',
            unsafe_allow_html=True
        )
