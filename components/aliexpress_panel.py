"""
AliExpress Panel Component
Visualiza datos de productos y tendencias de AliExpress
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import html as html_module
from typing import List, Optional
import pandas as pd


def render_aliexpress_panel(
    keyword: str,
    products: list,
    hotproducts: list,
    metrics: any
) -> None:
    """
    Renderiza el panel completo de AliExpress

    Args:
        keyword: Keyword buscado
        products: Lista de productos encontrados
        hotproducts: Lista de productos trending
        metrics: Métricas calculadas
    """
    st.markdown("### 🛒 Datos de AliExpress")
    st.caption(f"Análisis de mercado para: **{html_module.escape(keyword)}**")

    if not products and not hotproducts:
        st.info("No se encontraron productos en AliExpress para este término.")
        return

    # Métricas principales
    _render_metrics_summary(metrics)

    st.markdown("---")

    # Tabs para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔥 Trending",
        "📦 Todos los productos",
        "📊 Análisis de precios",
        "🏪 Por tienda"
    ])

    with tab1:
        _render_hotproducts(hotproducts)

    with tab2:
        _render_product_grid(products)

    with tab3:
        _render_price_analysis(products, metrics)

    with tab4:
        _render_shop_analysis(products)


def render_aliexpress_mini(keyword: str, metrics: any) -> None:
    """
    Renderiza versión compacta para sidebar o resumen

    Args:
        keyword: Keyword buscado
        metrics: Métricas calculadas
    """
    if not metrics or metrics.total_products == 0:
        return

    st.markdown("#### 🛒 AliExpress")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Productos", f"{metrics.total_products:,}")
        st.metric("Precio medio", f"€{metrics.avg_price:.2f}")

    with col2:
        st.metric("Pedidos totales", f"{metrics.total_orders:,}")
        if metrics.has_trending:
            st.success("🔥 Con productos trending")
        else:
            st.info("📦 Sin trending")


def _render_metrics_summary(metrics: any) -> None:
    """Renderiza resumen de métricas"""
    if not metrics:
        return

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "Total productos",
            f"{metrics.total_products:,}",
            help="Productos encontrados en AliExpress"
        )

    with col2:
        st.metric(
            "Precio medio",
            f"€{metrics.avg_price:.2f}",
            help="Precio promedio de todos los productos"
        )

    with col3:
        st.metric(
            "Rango de precios",
            f"€{metrics.min_price:.0f} - €{metrics.max_price:.0f}",
            help="Precio mínimo y máximo"
        )

    with col4:
        st.metric(
            "Pedidos totales",
            f"{metrics.total_orders:,}",
            help="Suma de todos los pedidos"
        )

    with col5:
        st.metric(
            "Rating medio",
            f"⭐ {metrics.avg_rating:.1f}" if metrics.avg_rating > 0 else "N/A",
            help="Valoración media de productos"
        )

    # Indicador de trending
    if metrics.has_trending:
        st.success("🔥 **Productos con alto volumen de ventas detectados** - Esta marca/producto tiene tracción en AliExpress")


def _render_hotproducts(products: list) -> None:
    """Renderiza productos en tendencia"""
    if not products:
        st.info("No hay productos trending para mostrar")
        return

    st.markdown("#### 🔥 Productos más vendidos")

    # Grid de 3 columnas
    for i in range(0, min(len(products), 9), 3):
        cols = st.columns(3)

        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(products):
                break

            product = products[idx]

            with col:
                _render_product_card(product, show_rank=True, rank=idx + 1)


def _render_product_grid(products: list) -> None:
    """Renderiza grid de productos"""
    if not products:
        st.info("No hay productos para mostrar")
        return

    # Filtros
    col1, col2, col3 = st.columns(3)

    with col1:
        sort_by = st.selectbox(
            "Ordenar por",
            options=["orders", "price_asc", "price_desc", "rating"],
            format_func=lambda x: {
                "orders": "Más vendidos",
                "price_asc": "Precio: menor a mayor",
                "price_desc": "Precio: mayor a menor",
                "rating": "Mejor valorados"
            }.get(x)
        )

    with col2:
        min_price = st.number_input("Precio mínimo (€)", min_value=0.0, value=0.0)

    with col3:
        max_price = st.number_input("Precio máximo (€)", min_value=0.0, value=1000.0)

    # Filtrar y ordenar
    filtered = [p for p in products if min_price <= p.price <= max_price]

    if sort_by == "orders":
        filtered.sort(key=lambda x: x.orders, reverse=True)
    elif sort_by == "price_asc":
        filtered.sort(key=lambda x: x.price)
    elif sort_by == "price_desc":
        filtered.sort(key=lambda x: x.price, reverse=True)
    elif sort_by == "rating":
        filtered.sort(key=lambda x: x.rating, reverse=True)

    st.caption(f"Mostrando {len(filtered)} productos")

    # Grid
    for i in range(0, min(len(filtered), 12), 4):
        cols = st.columns(4)

        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(filtered):
                break

            with col:
                _render_product_card(filtered[idx])


def _render_product_card(product: any, show_rank: bool = False, rank: int = 0) -> None:
    """Renderiza tarjeta de producto individual"""
    with st.container():
        # Imagen
        if product.image_url:
            st.image(product.image_url, width="stretch")

        # Título (truncado)
        title = html_module.escape(product.title[:50] + "..." if len(product.title) > 50 else product.title)

        if show_rank:
            st.markdown(f"**#{rank}** {title}")
        else:
            st.markdown(f"**{title}**")

        # Precio
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"💰 **€{product.price:.2f}**")
        with col2:
            if product.discount > 0:
                st.markdown(f"🏷️ -{product.discount}%")

        # Pedidos y rating
        st.caption(f"📦 {product.orders:,} pedidos · ⭐ {product.rating:.1f}")

        # Tienda
        shop = html_module.escape(product.shop_name[:20]) if product.shop_name else "Unknown"
        st.caption(f"🏪 {shop}")

        st.markdown("---")


def _render_price_analysis(products: list, metrics: any) -> None:
    """Análisis de distribución de precios"""
    if not products or not metrics:
        st.info("No hay datos suficientes para análisis")
        return

    st.markdown("#### 📊 Distribución de precios")

    col1, col2 = st.columns(2)

    with col1:
        # Histograma de precios
        prices = [p.price for p in products if p.price > 0 and p.price < 500]

        if prices:
            fig = px.histogram(
                x=prices,
                nbins=20,
                title="Distribución de precios",
                labels={"x": "Precio (€)", "y": "Cantidad"},
                color_discrete_sequence=["#7C3AED"]
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, width="stretch")

    with col2:
        # Gráfico de rangos
        if metrics.price_range_distribution:
            df = pd.DataFrame([
                {"Rango": k, "Productos": v}
                for k, v in metrics.price_range_distribution.items()
                if v > 0
            ])

            if not df.empty:
                fig = px.pie(
                    df,
                    values="Productos",
                    names="Rango",
                    title="Productos por rango de precio",
                    color_discrete_sequence=px.colors.sequential.Purples
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, width="stretch")

    # Relación precio vs pedidos
    st.markdown("#### 💰 Precio vs Ventas")

    df_scatter = pd.DataFrame([
        {
            "Precio": p.price,
            "Pedidos": p.orders,
            "Rating": p.rating,
            "Producto": p.title[:30]
        }
        for p in products if p.price > 0 and p.price < 500
    ])

    if not df_scatter.empty:
        fig = px.scatter(
            df_scatter,
            x="Precio",
            y="Pedidos",
            size="Rating",
            hover_name="Producto",
            color="Rating",
            color_continuous_scale="Viridis",
            title="Relación entre precio y volumen de ventas"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width="stretch")


def _render_shop_analysis(products: list) -> None:
    """Análisis por tienda/vendedor"""
    if not products:
        st.info("No hay datos de tiendas")
        return

    st.markdown("#### 🏪 Análisis por vendedor")

    # Agrupar por tienda
    from collections import defaultdict
    shops = defaultdict(lambda: {"products": 0, "total_orders": 0, "avg_price": [], "ratings": []})

    for p in products:
        shop = p.shop_name or "Unknown"
        shops[shop]["products"] += 1
        shops[shop]["total_orders"] += p.orders
        if p.price > 0:
            shops[shop]["avg_price"].append(p.price)
        if p.rating > 0:
            shops[shop]["ratings"].append(p.rating)

    # Crear DataFrame
    shop_data = []
    for shop, data in shops.items():
        shop_data.append({
            "Tienda": shop[:30],
            "Productos": data["products"],
            "Pedidos totales": data["total_orders"],
            "Precio medio": sum(data["avg_price"]) / len(data["avg_price"]) if data["avg_price"] else 0,
            "Rating medio": sum(data["ratings"]) / len(data["ratings"]) if data["ratings"] else 0
        })

    df = pd.DataFrame(shop_data)
    df = df.sort_values("Pedidos totales", ascending=False).head(15)

    # Tabla
    st.dataframe(
        df.style.format({
            "Precio medio": "€{:.2f}",
            "Rating medio": "{:.1f}",
            "Pedidos totales": "{:,}"
        }),
        use_container_width=True,
        hide_index=True
    )

    # Gráfico de barras
    if len(df) > 0:
        fig = px.bar(
            df.head(10),
            x="Tienda",
            y="Pedidos totales",
            color="Rating medio",
            color_continuous_scale="RdYlGn",
            title="Top 10 vendedores por volumen"
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, width="stretch")


def render_aliexpress_config() -> None:
    """Renderiza sección de configuración de AliExpress"""
    from modules.aliexpress import check_aliexpress_config

    config = check_aliexpress_config()

    st.markdown("### 🛒 Configuración AliExpress")

    # Estado
    col1, col2, col3 = st.columns(3)

    with col1:
        if config["has_key"]:
            st.success("✅ API Key configurada")
        else:
            st.error("❌ API Key no configurada")

    with col2:
        if config["has_secret"]:
            st.success("✅ API Secret configurado")
        else:
            st.error("❌ API Secret no configurado")

    with col3:
        if config["module_installed"]:
            st.success("✅ Módulo instalado")
        else:
            st.warning("⚠️ Módulo no instalado")

    # Instrucciones
    with st.expander("📋 Cómo configurar AliExpress API"):
        st.markdown("""
        ### Paso 1: Crear cuenta en AliExpress Open Platform

        1. Ve a [AliExpress Open Platform](https://portals.aliexpress.com/)
        2. Regístrate como desarrollador
        3. Crea una nueva aplicación

        ### Paso 2: Obtener credenciales

        Una vez aprobada tu aplicación, obtendrás:
        - **App Key**: Tu identificador de aplicación
        - **App Secret**: Tu clave secreta
        - **Tracking ID**: Para programa de afiliados (opcional)

        ### Paso 3: Configurar en Streamlit

        Añade a tu archivo `secrets.toml`:

        ```toml
        ALIEXPRESS_KEY = "tu_app_key"
        ALIEXPRESS_SECRET = "tu_app_secret"
        ALIEXPRESS_TRACKING_ID = "tu_tracking_id"  # Opcional
        ```

        ### Paso 4: Instalar dependencia

        ```bash
        pip install python-aliexpress-api
        ```
        """)


def render_aliexpress_comparison(keyword: str, trends_score: int, ali_metrics: any) -> None:
    """
    Compara datos de Google Trends con AliExpress

    Útil para detectar discrepancias (ej: poco buscado pero muy vendido)
    """
    st.markdown("### 🔄 Comparativa: Búsquedas vs Ventas")

    if not ali_metrics or ali_metrics.total_products == 0:
        st.info("No hay datos de AliExpress para comparar")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔍 Google Trends")
        st.metric("Índice de tendencia", trends_score)

        if trends_score < 30:
            st.warning("Bajo volumen de búsquedas")
        elif trends_score < 70:
            st.info("Volumen moderado de búsquedas")
        else:
            st.success("Alto volumen de búsquedas")

    with col2:
        st.markdown("#### 🛒 AliExpress")
        st.metric("Productos disponibles", ali_metrics.total_products)
        st.metric("Pedidos totales", f"{ali_metrics.total_orders:,}")

        if ali_metrics.total_orders > 10000:
            st.success("Alto volumen de ventas")
        elif ali_metrics.total_orders > 1000:
            st.info("Volumen moderado de ventas")
        else:
            st.warning("Bajo volumen de ventas")

    # Análisis de discrepancia
    st.markdown("---")

    # Calcular ratio
    if trends_score > 0 and ali_metrics.total_orders > 0:
        # Normalizar a escala similar
        ali_score = min(100, (ali_metrics.total_orders / 100))  # Escalar pedidos

        if trends_score < 30 and ali_metrics.total_orders > 5000:
            st.success("""
            🎯 **Oportunidad detectada**:
            Bajo volumen de búsquedas pero alto volumen de ventas en AliExpress.
            Esto puede indicar un producto con demanda real pero poca competencia en marketing/SEO.
            """)
        elif trends_score > 70 and ali_metrics.total_orders < 500:
            st.warning("""
            ⚠️ **Alerta**:
            Alto volumen de búsquedas pero pocos pedidos en AliExpress.
            Puede indicar interés sin conversión o que el producto no está disponible en AliExpress.
            """)
        else:
            st.info("📊 Los datos de búsquedas y ventas están alineados.")

