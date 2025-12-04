"""
Product Analysis Module
Detecta y analiza productos de una marca

Funcionalidades:
- Detectar productos desde queries relacionadas
- Clasificar en matriz de oportunidad
- Comparar tendencias entre productos
- Análisis de ciclo de vida
"""

import re
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import streamlit as st


class OpportunityCategory(Enum):
    """Categorías de la matriz de oportunidad"""
    EMERGENTE = "emergente"      # Bajo volumen, alto crecimiento
    ESTRELLA = "estrella"        # Alto volumen, alto crecimiento
    CONSOLIDADO = "consolidado"  # Alto volumen, bajo crecimiento
    NICHO = "nicho"              # Bajo volumen, bajo crecimiento


class LifecycleStage(Enum):
    """Etapas del ciclo de vida"""
    LANZAMIENTO = "lanzamiento"
    CRECIMIENTO = "crecimiento"
    MADUREZ = "madurez"
    DECLIVE = "declive"


@dataclass
class ProductData:
    """Datos de un producto detectado"""
    name: str
    full_query: str
    volume: float = 0
    growth: float = 0
    category: OpportunityCategory = OpportunityCategory.NICHO
    lifecycle: LifecycleStage = LifecycleStage.LANZAMIENTO
    trend_values: List[float] = None

    def __post_init__(self):
        if self.trend_values is None:
            self.trend_values = []


class ProductAnalyzer:
    """Analizador de productos de marca"""

    BASE_URL = "https://serpapi.com/search.json"

    # Patrones comunes de nombres de producto (alfanuméricos)
    PRODUCT_PATTERNS = [
        r'\b([A-Z]{2,}[\-\s]?\d{1,4}[A-Z]?(?:\s?(?:Pro|Plus|Max|Ultra|Lite|Mini|Air))?)\b',  # SER5 Pro, EQ12, GTR7
        r'\b(\d{3,4}[A-Z]?(?:\s?(?:Pro|Plus|Max|Ultra|Lite|Mini))?)\b',  # 3080, 4090 Ti
        r'\b([A-Z][a-z]+\s?\d{1,2}(?:\s?(?:Pro|Plus|Max|Ultra))?)\b',  # Ryzen 9, Core i7
    ]

    # Palabras a excluir (no son productos)
    EXCLUDE_WORDS = [
        'amazon', 'ebay', 'aliexpress', 'review', 'reviews', 'precio', 'price',
        'comprar', 'buy', 'best', 'mejor', 'vs', 'versus', 'comparison',
        'driver', 'drivers', 'manual', 'support', 'warranty', 'garantia',
        'españa', 'spain', 'usa', 'uk', 'europe', 'reddit', 'forum',
        '2023', '2024', '2025'
    ]

    # Umbrales para clasificación
    VOLUME_THRESHOLD = 50  # Índice de volumen para considerar "alto"
    GROWTH_THRESHOLD = 15  # % de crecimiento para considerar "alto"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def detect_products(
        self,
        brand: str,
        related_queries: List[dict],
        related_topics: List[dict] = None,
        autocomplete: List[str] = None
    ) -> List[ProductData]:
        """
        Detecta productos de una marca desde múltiples fuentes

        Args:
            brand: Nombre de la marca
            related_queries: Queries relacionadas de Google Trends
            related_topics: Topics relacionados (opcional)
            autocomplete: Sugerencias de autocompletado (opcional)

        Returns:
            Lista de ProductData detectados
        """
        brand_lower = brand.lower().strip()
        detected_products = {}

        # 1. Extraer de related queries
        all_queries = []
        if related_queries:
            for q in related_queries:
                query_text = q.get("query", "") if isinstance(q, dict) else str(q)
                if query_text:
                    all_queries.append({
                        "text": query_text,
                        "growth": self._safe_extract_value(q.get("extracted_value", 0) if isinstance(q, dict) else 0)
                    })

        # 2. Añadir autocomplete si existe
        if autocomplete:
            for suggestion in autocomplete:
                if suggestion and suggestion.lower() not in [q["text"].lower() for q in all_queries]:
                    all_queries.append({"text": suggestion, "growth": 0})

        # 3. Procesar queries para extraer productos
        for query_data in all_queries:
            query = query_data["text"].lower()
            growth = query_data["growth"]

            # Debe contener la marca
            if brand_lower not in query:
                continue

            # Excluir queries genéricas
            if any(exclude in query for exclude in self.EXCLUDE_WORDS):
                continue

            # Extraer nombre de producto
            product_name = self._extract_product_name(query, brand_lower)

            if product_name and len(product_name) >= 2:
                # Normalizar nombre
                product_key = product_name.lower().replace(" ", "")

                if product_key not in detected_products:
                    detected_products[product_key] = ProductData(
                        name=product_name.upper(),
                        full_query=query_data["text"],
                        growth=growth if isinstance(growth, (int, float)) else 0
                    )
                else:
                    # Actualizar si tiene mayor crecimiento
                    current_growth = detected_products[product_key].growth
                    if isinstance(growth, (int, float)) and growth > current_growth:
                        detected_products[product_key].growth = growth

        return list(detected_products.values())

    def _extract_product_name(self, query: str, brand: str) -> Optional[str]:
        """Extrae el nombre del producto de una query"""
        # Remover la marca de la query
        query_without_brand = query.replace(brand, "").strip()

        # Buscar patrones de producto
        for pattern in self.PRODUCT_PATTERNS:
            matches = re.findall(pattern, query_without_brand, re.IGNORECASE)
            if matches:
                return matches[0].strip()

        # Si no hay patrón, tomar las primeras palabras después de la marca
        words = query_without_brand.split()
        if words:
            # Filtrar palabras muy cortas o excluidas
            product_words = []
            for word in words[:3]:
                word_clean = word.strip()
                if len(word_clean) >= 2 and word_clean not in self.EXCLUDE_WORDS:
                    product_words.append(word_clean)

            if product_words:
                return " ".join(product_words[:2])

        return None

    def _safe_extract_value(self, value) -> float:
        """Extrae valor numérico de forma segura"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            if value.lower() == "breakout":
                return 5000.0  # Valor alto para breakout
            # Intentar extraer número
            numbers = re.findall(r'[\d.]+', value)
            if numbers:
                try:
                    return float(numbers[0])
                except (ValueError, IndexError):
                    pass
        return 0.0

    def get_products_comparison(
        self,
        brand: str,
        products: List[ProductData],
        geo: str = "ES",
        timeframe: str = "today 12-m"
    ) -> Dict:
        """
        Obtiene datos comparativos de tendencias para los productos
        Usa Google Trends para comparar hasta 5 productos

        Returns:
            Dict con datos de tendencia por producto
        """
        if not products:
            return {"success": True, "products": [], "comparison_data": {}}

        # Limitar a 5 productos (límite de Google Trends)
        products_to_compare = products[:5]

        # Construir queries de comparación
        queries = [f"{brand} {p.name}" for p in products_to_compare]
        q_param = ",".join(queries)

        params = {
            "engine": "google_trends",
            "q": q_param,
            "data_type": "TIMESERIES",
            "geo": geo,
            "date": timeframe,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            timeline_data = data.get("interest_over_time", {}).get("timeline_data", [])
            averages = data.get("interest_over_time", {}).get("averages", [])

            # Procesar datos por producto
            comparison = {}

            for i, product in enumerate(products_to_compare):
                product_values = []

                for point in timeline_data:
                    values = point.get("values", [])
                    if i < len(values):
                        val = self._safe_extract_value(values[i].get("extracted_value", 0))
                        product_values.append(val)

                # Calcular métricas
                if product_values:
                    avg_volume = sum(product_values) / len(product_values)
                    current_value = product_values[-1] if product_values else 0

                    # Calcular crecimiento
                    if len(product_values) >= 4:
                        recent = sum(product_values[-3:]) / 3
                        previous = sum(product_values[:-3]) / max(1, len(product_values) - 3)
                        growth = ((recent - previous) / max(1, previous)) * 100
                    else:
                        growth = 0

                    product.volume = avg_volume
                    product.growth = growth
                    product.trend_values = product_values
                else:
                    product.volume = 0
                    product.growth = 0
                    product.trend_values = []

                comparison[product.name] = {
                    "values": product_values,
                    "volume": product.volume,
                    "growth": product.growth
                }

            return {
                "success": True,
                "products": products_to_compare,
                "comparison_data": comparison,
                "timeline_data": timeline_data
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "products": products,
                "comparison_data": {}
            }

    def classify_products(self, products: List[ProductData]) -> Dict[OpportunityCategory, List[ProductData]]:
        """
        Clasifica productos en la matriz de oportunidad

        Cuadrantes:
        - EMERGENTE: Bajo volumen, Alto crecimiento (🚀 Apostar)
        - ESTRELLA: Alto volumen, Alto crecimiento (⭐ Potenciar)
        - CONSOLIDADO: Alto volumen, Bajo crecimiento (💎 Mantener)
        - NICHO: Bajo volumen, Bajo crecimiento (👀 Observar)
        """
        if not products:
            return {cat: [] for cat in OpportunityCategory}

        # Calcular umbrales dinámicos basados en los datos
        volumes = [p.volume for p in products if p.volume > 0]
        growths = [p.growth for p in products]

        if volumes:
            volume_threshold = sum(volumes) / len(volumes)  # Media como umbral
        else:
            volume_threshold = self.VOLUME_THRESHOLD

        if growths:
            growth_threshold = sum(growths) / len(growths)
        else:
            growth_threshold = self.GROWTH_THRESHOLD

        # Asegurar umbrales mínimos
        volume_threshold = max(volume_threshold, 1)
        growth_threshold = max(growth_threshold, 5)

        classified = {cat: [] for cat in OpportunityCategory}

        for product in products:
            high_volume = product.volume >= volume_threshold
            high_growth = product.growth >= growth_threshold

            if high_volume and high_growth:
                product.category = OpportunityCategory.ESTRELLA
            elif not high_volume and high_growth:
                product.category = OpportunityCategory.EMERGENTE
            elif high_volume and not high_growth:
                product.category = OpportunityCategory.CONSOLIDADO
            else:
                product.category = OpportunityCategory.NICHO

            classified[product.category].append(product)

        return classified

    def determine_lifecycle(self, products: List[ProductData]) -> List[ProductData]:
        """
        Determina la etapa del ciclo de vida de cada producto

        Basado en:
        - Volumen actual
        - Tasa de crecimiento
        - Tendencia de los valores
        """
        for product in products:
            values = product.trend_values
            volume = product.volume
            growth = product.growth

            # Analizar tendencia de los valores
            if values and len(values) >= 6:
                first_half = sum(values[:len(values)//2]) / max(1, len(values)//2)
                second_half = sum(values[len(values)//2:]) / max(1, len(values) - len(values)//2)
                trend_direction = second_half - first_half
            else:
                trend_direction = growth

            # Clasificar ciclo de vida
            if volume < 20 and growth > 50:
                product.lifecycle = LifecycleStage.LANZAMIENTO
            elif growth > 20 and trend_direction > 0:
                product.lifecycle = LifecycleStage.CRECIMIENTO
            elif volume > 30 and abs(growth) < 15:
                product.lifecycle = LifecycleStage.MADUREZ
            elif growth < -10 or trend_direction < -10:
                product.lifecycle = LifecycleStage.DECLIVE
            else:
                # Default basado en volumen
                if volume < 30:
                    product.lifecycle = LifecycleStage.LANZAMIENTO
                else:
                    product.lifecycle = LifecycleStage.MADUREZ

        return products

    def get_shopping_products(
        self,
        brand: str,
        country: str = "ES"
    ) -> Dict:
        """
        Obtiene productos reales de Google Shopping

        Returns:
            Dict con productos incluyendo precios y disponibilidad
        """
        params = {
            "engine": "google_shopping",
            "q": brand,
            "gl": country.lower(),
            "hl": "es" if country == "ES" else "en",
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            shopping_results = data.get("shopping_results", [])

            products = []
            for item in shopping_results[:10]:
                products.append({
                    "title": item.get("title", ""),
                    "price": item.get("price", ""),
                    "extracted_price": item.get("extracted_price", 0),
                    "source": item.get("source", ""),
                    "link": item.get("link", ""),
                    "thumbnail": item.get("thumbnail", ""),
                    "rating": item.get("rating", 0),
                    "reviews": item.get("reviews", 0)
                })

            return {
                "success": True,
                "products": products,
                "total": len(products),
                "brand": brand
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "products": []
            }

    def generate_product_insights(
        self,
        brand: str,
        classified_products: Dict[OpportunityCategory, List[ProductData]]
    ) -> Dict:
        """
        Genera insights y recomendaciones sobre los productos
        """
        insights = {
            "top_opportunities": [],
            "recommendations": [],
            "warnings": [],
            "summary": ""
        }

        # Contar productos por categoría
        counts = {cat.value: len(prods) for cat, prods in classified_products.items()}
        total = sum(counts.values())

        if total == 0:
            insights["summary"] = f"No se detectaron productos específicos para {brand}."
            insights["recommendations"].append(
                "Considera buscar con nombres de producto específicos o revisar el catálogo de la marca."
            )
            return insights

        # Top oportunidades (emergentes + estrellas ordenados por crecimiento)
        opportunities = []
        for cat in [OpportunityCategory.EMERGENTE, OpportunityCategory.ESTRELLA]:
            for product in classified_products.get(cat, []):
                opportunities.append(product)

        opportunities.sort(key=lambda p: p.growth, reverse=True)
        insights["top_opportunities"] = opportunities[:5]

        # Generar resumen
        estrellas = counts.get("estrella", 0)
        emergentes = counts.get("emergente", 0)
        consolidados = counts.get("consolidado", 0)
        nicho = counts.get("nicho", 0)

        summary_parts = [f"{brand} tiene {total} productos detectados:"]

        if estrellas > 0:
            summary_parts.append(f"{estrellas} producto(s) estrella con alto rendimiento")
        if emergentes > 0:
            summary_parts.append(f"{emergentes} producto(s) emergente(s) con potencial de crecimiento")
        if consolidados > 0:
            summary_parts.append(f"{consolidados} producto(s) consolidado(s) en el mercado")
        if nicho > 0:
            summary_parts.append(f"{nicho} producto(s) de nicho o en observación")

        insights["summary"] = ". ".join(summary_parts) + "."

        # Recomendaciones
        if emergentes > 0:
            insights["recommendations"].append(
                "🚀 Invertir en productos emergentes: alto potencial con competencia aún baja."
            )

        if estrellas > 0:
            insights["recommendations"].append(
                "⭐ Potenciar productos estrella: asegurar stock y visibilidad."
            )

        if consolidados > 0 and estrellas == 0 and emergentes == 0:
            insights["warnings"].append(
                "⚠️ La marca solo tiene productos consolidados. Riesgo de estancamiento."
            )

        if nicho > total * 0.7:
            insights["warnings"].append(
                "⚠️ Mayoría de productos en nicho/declive. Evaluar viabilidad de la marca."
            )

        return insights

    def full_analysis(
        self,
        brand: str,
        related_queries: List[dict],
        geo: str = "ES",
        timeframe: str = "today 12-m",
        include_shopping: bool = True,
        max_products: int = 20
    ) -> Dict:
        """
        Ejecuta análisis completo de productos de múltiples fuentes

        Sources:
        - Google Trends Related Queries (rising + top)
        - Google Trends Autocomplete
        - Google Shopping (productos reales con precios)

        Args:
            brand: Nombre de la marca
            related_queries: Queries relacionadas de Google Trends
            geo: País
            timeframe: Período de tiempo
            include_shopping: Incluir productos de Google Shopping
            max_products: Máximo de productos a analizar

        Returns:
            Dict con todos los datos y análisis
        """
        all_products = []
        shopping_products = []

        # 1. Detectar productos desde queries relacionadas
        trend_products = self.detect_products(brand, related_queries)
        all_products.extend(trend_products)

        # 2. Obtener autocomplete para más sugerencias
        autocomplete_suggestions = self._get_autocomplete(brand, geo)
        if autocomplete_suggestions:
            autocomplete_products = self.detect_products(
                brand,
                [{"query": s, "extracted_value": 0} for s in autocomplete_suggestions]
            )
            # Añadir solo los que no están duplicados
            existing_names = {p.name.lower() for p in all_products}
            for p in autocomplete_products:
                if p.name.lower() not in existing_names:
                    all_products.append(p)
                    existing_names.add(p.name.lower())

        # 3. Obtener productos de Google Shopping (datos reales)
        if include_shopping:
            shopping_result = self.get_shopping_products(brand, geo)
            if shopping_result.get("success"):
                shopping_products = shopping_result.get("products", [])

                # Extraer nombres de productos de Shopping
                for sp in shopping_products:
                    product_name = self._extract_product_from_shopping(sp.get("title", ""), brand)
                    if product_name:
                        existing_names = {p.name.lower() for p in all_products}
                        if product_name.lower() not in existing_names:
                            all_products.append(ProductData(
                                name=product_name.upper(),
                                full_query=sp.get("title", ""),
                                volume=0,  # Se actualizará con trends
                                growth=0
                            ))

        # Limitar productos
        all_products = all_products[:max_products]

        if not all_products:
            return {
                "success": True,
                "brand": brand,
                "products": [],
                "shopping_products": shopping_products,
                "classified": {cat: [] for cat in OpportunityCategory},
                "insights": self.generate_product_insights(brand, {}),
                "comparison_data": {},
                "sources": {
                    "trends": 0,
                    "autocomplete": len(autocomplete_suggestions) if autocomplete_suggestions else 0,
                    "shopping": len(shopping_products)
                }
            }

        # 4. Obtener datos comparativos de tendencias (máx 5 a la vez por limitación de API)
        products_with_data = []
        for i in range(0, len(all_products), 5):
            batch = all_products[i:i+5]
            comparison_result = self.get_products_comparison(brand, batch, geo, timeframe)
            if comparison_result.get("success"):
                products_with_data.extend(comparison_result.get("products", batch))
            else:
                products_with_data.extend(batch)

        # 5. Clasificar productos
        classified = self.classify_products(products_with_data)

        # 6. Determinar ciclo de vida
        self.determine_lifecycle(products_with_data)

        # 7. Generar insights
        insights = self.generate_product_insights(brand, classified)

        return {
            "success": True,
            "brand": brand,
            "products": products_with_data,
            "shopping_products": shopping_products,
            "classified": classified,
            "insights": insights,
            "comparison_data": {},
            "sources": {
                "trends": len(trend_products),
                "autocomplete": len(autocomplete_suggestions) if autocomplete_suggestions else 0,
                "shopping": len(shopping_products)
            }
        }

    def _get_autocomplete(self, brand: str, geo: str = "ES") -> List[str]:
        """
        Obtiene sugerencias de autocomplete de Google Trends

        Returns:
            Lista de sugerencias
        """
        params = {
            "engine": "google_trends_autocomplete",
            "q": brand,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            suggestions = []
            for item in data.get("suggestions", []):
                title = item.get("title", "")
                if title and brand.lower() in title.lower():
                    suggestions.append(title)

            return suggestions[:20]  # Limitar

        except Exception:
            return []

    def _extract_product_from_shopping(self, title: str, brand: str) -> Optional[str]:
        """
        Extrae nombre de producto de un título de Google Shopping

        Args:
            title: Título del producto (ej: "Beelink SER5 Pro Mini PC AMD Ryzen 5 5560U")
            brand: Nombre de la marca

        Returns:
            Nombre del producto o None
        """
        if not title:
            return None

        title_lower = title.lower()
        brand_lower = brand.lower()

        # Verificar que contiene la marca
        if brand_lower not in title_lower:
            return None

        # Buscar patrones de modelo después de la marca
        patterns = [
            rf'{re.escape(brand_lower)}\s+([A-Z0-9]{{2,}}[\-\s]?[A-Z0-9]*(?:\s+(?:Pro|Plus|Max|Ultra|Mini|Lite))?)',
            rf'([A-Z0-9]{{2,}}[\-\s]?[A-Z0-9]*)\s+{re.escape(brand_lower)}',
        ]

        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                product_name = match.group(1).strip()
                if len(product_name) >= 2 and len(product_name) <= 20:
                    return product_name

        return None

    def get_extended_shopping(
        self,
        brand: str,
        country: str = "ES",
        max_results: int = 40
    ) -> Dict:
        """
        Obtiene más productos de Google Shopping con paginación

        Returns:
            Dict con productos extendidos
        """
        all_products = []

        # Primera página
        result = self.get_shopping_products(brand, country)
        if result.get("success"):
            all_products.extend(result.get("products", []))

        # Búsquedas adicionales con modificadores
        modifiers = ["Pro", "Mini", "Ultra", "Plus", "Max", "review", "precio"]

        for modifier in modifiers:
            if len(all_products) >= max_results:
                break

            query = f"{brand} {modifier}"
            params = {
                "engine": "google_shopping",
                "q": query,
                "gl": country.lower(),
                "hl": "es" if country == "ES" else "en",
                "api_key": self.api_key,
                "num": 10
            }

            try:
                response = requests.get(self.BASE_URL, params=params, timeout=15)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("shopping_results", []):
                        # Evitar duplicados
                        if not any(p.get("link") == item.get("link") for p in all_products):
                            all_products.append({
                                "title": item.get("title", ""),
                                "price": item.get("price", ""),
                                "extracted_price": item.get("extracted_price", 0),
                                "source": item.get("source", ""),
                                "link": item.get("link", ""),
                                "thumbnail": item.get("thumbnail", ""),
                                "rating": item.get("rating", 0),
                                "reviews": item.get("reviews", 0)
                            })
            except Exception:
                continue

        return {
            "success": True,
            "products": all_products[:max_results],
            "total": len(all_products),
            "brand": brand
        }

