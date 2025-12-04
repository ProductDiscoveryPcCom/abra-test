"""
AliExpress Module
Obtiene datos de productos, tendencias y hotproducts de AliExpress
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import html


@dataclass
class AliExpressProduct:
    """Producto de AliExpress normalizado"""
    product_id: str
    title: str
    image_url: str
    price: float
    original_price: float
    currency: str
    discount: int
    orders: int
    rating: float
    shop_name: str
    category: str
    affiliate_link: str = ""

    @property
    def discount_pct(self) -> int:
        """Calcula porcentaje de descuento"""
        if self.original_price > 0:
            return int((1 - self.price / self.original_price) * 100)
        return 0


@dataclass
class AliExpressMetrics:
    """Métricas agregadas de búsqueda en AliExpress"""
    keyword: str
    total_products: int
    avg_price: float
    min_price: float
    max_price: float
    avg_orders: int
    total_orders: int
    avg_rating: float
    top_categories: List[str]
    price_range_distribution: Dict[str, int]
    has_trending: bool


class AliExpressModule:
    """Módulo para interactuar con AliExpress API"""

    def __init__(self, app_key: str, app_secret: str, tracking_id: str = ""):
        """
        Inicializa el módulo de AliExpress

        Args:
            app_key: API Key de AliExpress Open Platform
            app_secret: API Secret
            tracking_id: ID de tracking para afiliados (opcional)
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.tracking_id = tracking_id
        self._api = None
        self._initialized = False

    def _init_api(self) -> bool:
        """Inicializa la API de AliExpress"""
        if self._initialized:
            return self._api is not None

        try:
            from aliexpress_api import AliexpressApi, models
            self._api = AliexpressApi(
                self.app_key,
                self.app_secret,
                models.Language.ES,  # Español para PCComponentes
                models.Currency.EUR,
                self.tracking_id or "default"
            )
            self._initialized = True
            return True
        except ImportError:
            st.warning("⚠️ Módulo python-aliexpress-api no instalado")
            self._initialized = True
            return False
        except Exception as e:
            st.error(f"Error inicializando AliExpress API: {html.escape(str(e))}")
            self._initialized = True
            return False

    def search_products(
        self,
        keyword: str,
        max_results: int = 50,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "orders"  # orders, price_asc, price_desc
    ) -> List[AliExpressProduct]:
        """
        Busca productos en AliExpress

        Args:
            keyword: Término de búsqueda
            max_results: Máximo de resultados (default 50)
            min_price: Precio mínimo en EUR
            max_price: Precio máximo en EUR
            sort_by: Ordenar por (orders, price_asc, price_desc)

        Returns:
            Lista de productos
        """
        if not self._init_api():
            return []

        try:
            # Construir parámetros
            params = {
                "keywords": keyword,
                "page_size": min(max_results, 50)  # API limita a 50
            }

            if min_price:
                params["min_sale_price"] = int(min_price * 100)  # En centavos
            if max_price:
                params["max_sale_price"] = int(max_price * 100)

            # Mapear sort
            sort_map = {
                "orders": None,  # Default
                "price_asc": "SALE_PRICE_ASC",
                "price_desc": "SALE_PRICE_DESC"
            }
            if sort_by in sort_map and sort_map[sort_by]:
                params["sort"] = sort_map[sort_by]

            response = self._api.get_products(**params)

            if not response or not hasattr(response, 'products'):
                return []

            return self._parse_products(response.products)

        except Exception as e:
            st.error(f"Error buscando productos: {html.escape(str(e))}")
            return []

    def get_hotproducts(
        self,
        keyword: str,
        max_results: int = 20,
        category_id: Optional[str] = None
    ) -> List[AliExpressProduct]:
        """
        Obtiene productos en tendencia (hotproducts)

        Args:
            keyword: Término de búsqueda
            max_results: Máximo resultados
            category_id: ID de categoría opcional

        Returns:
            Lista de productos trending
        """
        if not self._init_api():
            return []

        try:
            params = {
                "keywords": keyword,
                "page_size": min(max_results, 50)
            }

            if category_id:
                params["category_ids"] = category_id

            response = self._api.get_hotproducts(**params)

            if not response or not hasattr(response, 'products'):
                return []

            return self._parse_products(response.products)

        except Exception as e:
            st.error(f"Error obteniendo hotproducts: {html.escape(str(e))}")
            return []

    def get_product_details(self, product_ids: List[str]) -> List[AliExpressProduct]:
        """
        Obtiene detalles de productos específicos

        Args:
            product_ids: Lista de IDs o URLs de productos

        Returns:
            Lista de productos con detalles
        """
        if not self._init_api():
            return []

        try:
            response = self._api.get_products_details(product_ids)
            return self._parse_products(response)
        except Exception as e:
            st.error(f"Error obteniendo detalles: {html.escape(str(e))}")
            return []

    def get_affiliate_link(self, product_url: str) -> Optional[str]:
        """
        Genera link de afiliado para un producto

        Args:
            product_url: URL del producto

        Returns:
            URL de afiliado o None
        """
        if not self._init_api():
            return None

        try:
            links = self._api.get_affiliate_links(product_url)
            if links and len(links) > 0:
                return links[0].promotion_link
            return None
        except Exception:
            return None

    def get_categories(self) -> Dict[str, List[Dict]]:
        """
        Obtiene categorías de AliExpress

        Returns:
            Dict con parent_categories y child_categories
        """
        if not self._init_api():
            return {"parent": [], "child": []}

        try:
            parents = self._api.get_parent_categories()
            return {
                "parent": [{"id": c.category_id, "name": c.category_name} for c in parents],
                "child": []
            }
        except Exception:
            return {"parent": [], "child": []}

    def calculate_metrics(
        self,
        keyword: str,
        products: List[AliExpressProduct]
    ) -> AliExpressMetrics:
        """
        Calcula métricas agregadas de productos

        Args:
            keyword: Keyword buscado
            products: Lista de productos

        Returns:
            Métricas agregadas
        """
        if not products:
            return AliExpressMetrics(
                keyword=keyword,
                total_products=0,
                avg_price=0,
                min_price=0,
                max_price=0,
                avg_orders=0,
                total_orders=0,
                avg_rating=0,
                top_categories=[],
                price_range_distribution={},
                has_trending=False
            )

        prices = [p.price for p in products if p.price > 0]
        orders = [p.orders for p in products]
        ratings = [p.rating for p in products if p.rating > 0]
        categories = [p.category for p in products if p.category]

        # Distribución de precios
        price_ranges = {
            "0-10€": 0,
            "10-25€": 0,
            "25-50€": 0,
            "50-100€": 0,
            "100-200€": 0,
            "200€+": 0
        }

        for price in prices:
            if price < 10:
                price_ranges["0-10€"] += 1
            elif price < 25:
                price_ranges["10-25€"] += 1
            elif price < 50:
                price_ranges["25-50€"] += 1
            elif price < 100:
                price_ranges["50-100€"] += 1
            elif price < 200:
                price_ranges["100-200€"] += 1
            else:
                price_ranges["200€+"] += 1

        # Top categorías
        from collections import Counter
        cat_counts = Counter(categories)
        top_cats = [cat for cat, _ in cat_counts.most_common(5)]

        return AliExpressMetrics(
            keyword=keyword,
            total_products=len(products),
            avg_price=sum(prices) / len(prices) if prices else 0,
            min_price=min(prices) if prices else 0,
            max_price=max(prices) if prices else 0,
            avg_orders=int(sum(orders) / len(orders)) if orders else 0,
            total_orders=sum(orders),
            avg_rating=sum(ratings) / len(ratings) if ratings else 0,
            top_categories=top_cats,
            price_range_distribution=price_ranges,
            has_trending=any(p.orders > 1000 for p in products)
        )

    def _parse_products(self, raw_products: list) -> List[AliExpressProduct]:
        """Parsea productos de la API a objetos normalizados"""
        products = []

        for p in raw_products:
            try:
                # Extraer campos con fallbacks
                pid = str(getattr(p, 'product_id', '') or getattr(p, 'productId', ''))
                title = str(getattr(p, 'product_title', '') or getattr(p, 'productTitle', ''))
                img = str(
                    getattr(p, 'product_main_image_url', '') or
                    getattr(p, 'productMainImageUrl', '')
                )
                price = self._parse_price(
                    getattr(p, 'target_sale_price', 0) or
                    getattr(p, 'targetSalePrice', 0)
                )
                orig_price = self._parse_price(
                    getattr(p, 'target_original_price', 0) or
                    getattr(p, 'targetOriginalPrice', 0)
                )
                currency = str(getattr(p, 'target_sale_price_currency', 'EUR'))
                discount = int(getattr(p, 'discount', 0) or 0)
                orders = self._parse_orders(
                    getattr(p, 'lastest_volume', 0) or
                    getattr(p, 'lastestVolume', 0)
                )
                rating = float(
                    getattr(p, 'evaluate_rate', 0) or
                    getattr(p, 'evaluateRate', 0) or 0
                )
                shop = str(
                    getattr(p, 'shop_name', '') or
                    getattr(p, 'shopName', '') or 'Unknown'
                )
                cat = str(
                    getattr(p, 'first_level_category_name', '') or
                    getattr(p, 'firstLevelCategoryName', '') or ''
                )
                aff_link = str(
                    getattr(p, 'promotion_link', '') or
                    getattr(p, 'promotionLink', '') or ''
                )

                product = AliExpressProduct(
                    product_id=pid,
                    title=title,
                    image_url=img,
                    price=price,
                    original_price=orig_price,
                    currency=currency,
                    discount=discount,
                    orders=orders,
                    rating=rating,
                    shop_name=shop,
                    category=cat,
                    affiliate_link=aff_link
                )
                products.append(product)
            except Exception:
                continue

        return products

    def _parse_price(self, value: Any) -> float:
        """Parsea precio a float"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '.').replace('€', '').strip()
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _parse_orders(self, value: Any) -> int:
        """Parsea número de pedidos"""
        try:
            if isinstance(value, str):
                value = value.replace(',', '').replace('+', '').strip()
            return int(float(value)) if value else 0
        except (ValueError, TypeError):
            return 0


def check_aliexpress_config() -> Dict[str, bool]:
    """Verifica si AliExpress está configurado"""
    return {
        "has_key": bool(st.secrets.get("ALIEXPRESS_KEY")),
        "has_secret": bool(st.secrets.get("ALIEXPRESS_SECRET")),
        "has_tracking": bool(st.secrets.get("ALIEXPRESS_TRACKING_ID")),
        "module_installed": _check_module_installed()
    }


def _check_module_installed() -> bool:
    """Verifica si el módulo está instalado"""
    try:
        import aliexpress_api
        return True
    except ImportError:
        return False


def get_aliexpress_module() -> Optional[AliExpressModule]:
    """Factory para obtener módulo configurado"""
    config = check_aliexpress_config()

    if not config["has_key"] or not config["has_secret"]:
        return None

    return AliExpressModule(
        app_key=st.secrets.get("ALIEXPRESS_KEY", ""),
        app_secret=st.secrets.get("ALIEXPRESS_SECRET", ""),
        tracking_id=st.secrets.get("ALIEXPRESS_TRACKING_ID", "")
    )

