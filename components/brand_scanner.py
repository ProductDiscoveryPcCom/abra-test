"""
Brand Scanner Component
Análisis rápido de múltiples marcas desde CSV
"""

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
from typing import List, Dict, Optional


def render_brand_scanner(api_key: str, geo: str = "ES") -> None:
    """
    Renderiza el modo Scanner para análisis rápido de marcas

    Args:
        api_key: API key de SerpAPI
        geo: Código de país
    """
    st.markdown("### 🚀 Brand Scanner")
    st.caption("Análisis rápido de múltiples marcas. Sube un CSV y obtén el ranking por tendencia.")

    # Upload CSV
    uploaded_file = st.file_uploader(
        "📁 Sube tu CSV con marcas",
        type=['csv'],
        help="El CSV debe tener una columna llamada 'Brand' con los nombres de las marcas"
    )

    if uploaded_file is None:
        _render_upload_instructions()
        return

    # Leer CSV
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error leyendo CSV: {e}")
        return

    # Verificar columna Brand
    if 'Brand' not in df.columns:
        # Intentar con primera columna
        if len(df.columns) > 0:
            df = df.rename(columns={df.columns[0]: 'Brand'})
            st.info(f"Usando columna '{df.columns[0]}' como Brand")
        else:
            st.error("❌ El CSV debe tener una columna 'Brand'")
            return

    st.success(f"✅ {len(df)} marcas encontradas")

    # Preview
    with st.expander("👀 Preview de marcas"):
        st.dataframe(df.head(10), width="stretch")

    # Configuración
    col1, col2 = st.columns(2)

    with col1:
        num_brands = st.slider(
            "Marcas a analizar",
            min_value=1,
            max_value=min(len(df), 50),
            value=min(len(df), 20),
            help="Máximo 50 marcas por análisis para evitar límites de API"
        )

    with col2:
        timeframe = st.selectbox(
            "Período",
            options=["today 1-m", "today 3-m", "today 12-m"],
            format_func=lambda x: {
                "today 1-m": "Último mes",
                "today 3-m": "Últimos 3 meses",
                "today 12-m": "Último año"
            }.get(x),
            index=2
        )

    # Botón de análisis
    if st.button("🔍 Escanear marcas", type="primary", width="stretch"):
        brands = df['Brand'].head(num_brands).tolist()
        results = _scan_brands(brands, api_key, geo, timeframe)

        if results:
            _render_scanner_results(results, geo)


def render_quick_ranking(api_key: str, geo: str = "ES") -> None:
    """
    Modo ultra-rápido: solo índice de tendencia ordenado

    Args:
        api_key: API key de SerpAPI
        geo: Código de país
    """
    st.markdown("### ⚡ Quick Ranking")
    st.caption("Ordena marcas por índice de tendencia actual. Sin análisis profundo, solo ranking.")

    # Input de marcas (textarea o CSV)
    input_mode = st.radio(
        "Modo de entrada",
        ["📝 Lista de texto", "📁 Archivo CSV"],
        horizontal=True
    )

    brands = []

    if input_mode == "📝 Lista de texto":
        brands_text = st.text_area(
            "Marcas (una por línea)",
            placeholder="ASUS\nMSI\nGigabyte\nCorsair\nLogitech",
            height=150
        )
        if brands_text:
            brands = [b.strip() for b in brands_text.split('\n') if b.strip()]
    else:
        uploaded_file = st.file_uploader("CSV con marcas", type=['csv'])
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                col = 'Brand' if 'Brand' in df.columns else df.columns[0]
                brands = df[col].dropna().tolist()[:30]  # Máximo 30 para quick
            except Exception as e:
                st.error(f"Error: {e}")

    if not brands:
        st.info("Ingresa marcas para comenzar")
        return

    st.caption(f"📊 {len(brands)} marcas a analizar")

    if st.button("⚡ Obtener ranking", type="primary"):
        with st.spinner("Obteniendo índices de tendencia..."):
            results = _quick_scan(brands, api_key, geo)

        if results:
            _render_quick_ranking(results)


def _scan_brands(
    brands: List[str],
    api_key: str,
    geo: str,
    timeframe: str
) -> List[Dict]:
    """Escanea múltiples marcas y obtiene métricas"""

    results = []
    progress = st.progress(0)
    status = st.empty()

    for idx, brand in enumerate(brands):
        status.text(f"Analizando {idx+1}/{len(brands)}: {brand}")

        try:
            # Obtener datos de tendencia
            data = _get_trend_data(brand, api_key, geo, timeframe)

            if data:
                # Calcular métricas
                timeline = data.get('interest_over_time', {}).get('timeline_data', [])

                current_index = 0
                avg_index = 0
                growth = 0

                if timeline:
                    values = [
                        p['values'][0]['extracted_value']
                        for p in timeline
                        if p.get('values') and len(p['values']) > 0
                    ]

                    if values:
                        current_index = values[-1] if values else 0
                        avg_index = sum(values) / len(values)

                        # Calcular crecimiento
                        if len(values) >= 4:
                            recent = sum(values[-3:]) / 3
                            previous = sum(values[:-3]) / max(1, len(values) - 3)
                            if previous > 0:
                                growth = ((recent - previous) / previous) * 100

                results.append({
                    'brand': brand,
                    'current_index': current_index,
                    'avg_index': round(avg_index, 1),
                    'growth': round(growth, 1),
                    'status': 'ok'
                })
            else:
                results.append({
                    'brand': brand,
                    'current_index': 0,
                    'avg_index': 0,
                    'growth': 0,
                    'status': 'error'
                })

        except Exception as e:
            results.append({
                'brand': brand,
                'current_index': 0,
                'avg_index': 0,
                'growth': 0,
                'status': 'error'
            })

        progress.progress((idx + 1) / len(brands))
        time.sleep(0.5)  # Rate limiting

    status.text("✅ Escaneo completado")
    return results


def _quick_scan(brands: List[str], api_key: str, geo: str) -> List[Dict]:
    """Escaneo ultra-rápido: solo índice actual"""

    results = []
    progress = st.progress(0)

    for idx, brand in enumerate(brands):
        try:
            data = _get_trend_data(brand, api_key, geo, "today 1-m")

            current_index = 0
            if data:
                timeline = data.get('interest_over_time', {}).get('timeline_data', [])
                if timeline and timeline[-1].get('values'):
                    current_index = timeline[-1]['values'][0].get('extracted_value', 0)

            results.append({
                'brand': brand,
                'index': current_index
            })

        except Exception:
            results.append({
                'brand': brand,
                'index': 0
            })

        progress.progress((idx + 1) / len(brands))
        time.sleep(0.3)

    return results


def _get_trend_data(brand: str, api_key: str, geo: str, timeframe: str) -> Optional[Dict]:
    """Obtiene datos de Google Trends para una marca"""

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_trends",
        "q": brand,
        "data_type": "TIMESERIES",
        "date": timeframe,
        "geo": geo,
        "api_key": api_key
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def _render_scanner_results(results: List[Dict], geo: str) -> None:
    """Renderiza resultados del scanner"""

    # Crear DataFrame
    df = pd.DataFrame(results)
    df = df[df['status'] == 'ok']  # Solo resultados válidos

    if df.empty:
        st.warning("No se obtuvieron resultados válidos")
        return

    # Ordenar por índice actual
    df = df.sort_values('current_index', ascending=False)

    # Métricas resumen
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Marcas analizadas", len(df))
    with col2:
        st.metric("Índice promedio", f"{df['current_index'].mean():.0f}")
    with col3:
        top_brand = df.iloc[0]['brand'] if len(df) > 0 else "N/A"
        st.metric("Top marca", top_brand)
    with col4:
        growing = len(df[df['growth'] > 0])
        st.metric("En crecimiento", f"{growing}/{len(df)}")

    st.markdown("---")

    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["📊 Ranking", "📈 Gráfico", "💾 Exportar"])

    with tab1:
        _render_ranking_table(df)

    with tab2:
        _render_ranking_chart(df)

    with tab3:
        _render_export(df, geo)


def _render_ranking_table(df: pd.DataFrame) -> None:
    """Tabla de ranking interactiva"""

    st.markdown("#### 🏆 Ranking por Índice de Tendencia")

    # Formatear para mostrar
    display_df = df[['brand', 'current_index', 'avg_index', 'growth']].copy()
    display_df.columns = ['Marca', 'Índice Actual', 'Índice Promedio', 'Crecimiento %']
    display_df = display_df.reset_index(drop=True)
    display_df.index = display_df.index + 1  # Ranking desde 1

    # Colorear crecimiento
    def color_growth(val):
        if val > 10:
            return 'background-color: rgba(16, 185, 129, 0.3)'
        elif val < -10:
            return 'background-color: rgba(239, 68, 68, 0.3)'
        return ''

    styled_df = display_df.style.applymap(color_growth, subset=['Crecimiento %'])
    st.dataframe(styled_df, width="stretch", height=400)


def _render_ranking_chart(df: pd.DataFrame) -> None:
    """Gráfico de barras del ranking"""

    # Top 20 para el gráfico
    chart_df = df.head(20).copy()

    # Gráfico de barras horizontal
    fig = px.bar(
        chart_df,
        x='current_index',
        y='brand',
        orientation='h',
        color='growth',
        color_continuous_scale=['#EF4444', '#F5C518', '#10B981'],
        labels={
            'current_index': 'Índice de Tendencia',
            'brand': 'Marca',
            'growth': 'Crecimiento %'
        },
        title='Top 20 Marcas por Índice de Tendencia'
    )

    fig.update_layout(
        height=500,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )

    st.plotly_chart(fig, width="stretch")

    # Scatter: Índice vs Crecimiento
    st.markdown("#### 📊 Matriz: Tendencia vs Crecimiento")

    fig2 = px.scatter(
        df,
        x='current_index',
        y='growth',
        text='brand',
        size='avg_index',
        color='growth',
        color_continuous_scale=['#EF4444', '#F5C518', '#10B981'],
        labels={
            'current_index': 'Índice de Tendencia Actual',
            'growth': 'Crecimiento %',
            'avg_index': 'Índice Promedio'
        }
    )

    fig2.update_traces(textposition='top center', textfont_size=9)
    fig2.update_layout(height=500)

    # Líneas de referencia
    fig2.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    fig2.add_vline(x=df['current_index'].median(), line_dash="dash", line_color="gray", opacity=0.5)

    st.plotly_chart(fig2, width="stretch")


def _render_quick_ranking(results: List[Dict]) -> None:
    """Renderiza ranking rápido (solo índice)"""

    df = pd.DataFrame(results)
    df = df.sort_values('index', ascending=False)
    df = df.reset_index(drop=True)
    df.index = df.index + 1

    st.markdown("#### ⚡ Quick Ranking")

    # Mostrar como tabla simple
    for idx, row in df.iterrows():
        col1, col2, col3 = st.columns([1, 3, 2])

        with col1:
            if idx <= 3:
                medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(idx, "")
                st.markdown(f"### {medal} {idx}")
            else:
                st.markdown(f"### {idx}")

        with col2:
            st.markdown(f"**{row['brand']}**")

        with col3:
            # Barra de progreso visual
            pct = min(row['index'], 100)
            color = "#10B981" if pct >= 70 else "#F5C518" if pct >= 40 else "#6B7280"
            st.markdown(
                f'<div style="background: #E5E7EB; border-radius: 4px; height: 24px; overflow: hidden;">'
                f'<div style="background: {color}; width: {pct}%; height: 100%; display: flex; align-items: center; padding-left: 8px;">'
                f'<span style="color: white; font-weight: 600; font-size: 0.8rem;">{row["index"]}</span>'
                f'</div></div>',
                unsafe_allow_html=True
            )


def _render_export(df: pd.DataFrame, geo: str) -> None:
    """Opciones de exportación"""

    st.markdown("#### 💾 Exportar Resultados")

    # Preparar CSV
    export_df = df[['brand', 'current_index', 'avg_index', 'growth']].copy()
    export_df.columns = ['Marca', 'Indice_Actual', 'Indice_Promedio', 'Crecimiento_Pct']

    csv = export_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Descargar CSV",
        data=csv,
        file_name=f"brand_scanner_{geo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        width="stretch"
    )

    st.caption(f"Exportando {len(df)} marcas analizadas")


def _render_upload_instructions() -> None:
    """Instrucciones de uso"""

    st.markdown("""
    #### 📋 Formato del CSV

    Tu archivo debe tener una columna `Brand`:

    ```
    Brand
    ASUS
    MSI
    Gigabyte
    Corsair
    Logitech
    ```

    #### ⚡ Límites

    - Máximo 50 marcas por análisis
    - ~1 segundo por marca
    - Resultados ordenados por índice de tendencia
    """)

    # CSV de ejemplo
    example_df = pd.DataFrame({
        'Brand': ['ASUS', 'MSI', 'Gigabyte', 'Corsair', 'Logitech', 'Razer', 'SteelSeries', 'HyperX']
    })

    csv_example = example_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📥 Descargar CSV de ejemplo",
        data=csv_example,
        file_name="marcas_ejemplo.csv",
        mime="text/csv"
    )

