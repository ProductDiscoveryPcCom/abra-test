"""
URL Product Analyzer
Analiza URLs de productos para extraer marca, modelo y métricas.

Usa Perplexity para análisis inteligente y extracción de datos.
Preparado para futuras integraciones con Semrush, Ahrefs, etc.
"""

import re
import requests
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse
import streamlit as st


@dataclass
class ProductAnalysis:
    """Resultado del análisis de un producto desde URL"""
    # Datos básicos extraídos
    url: str
    domain: str
    brand: str = ""
    model: str = ""
    category: str = ""
    price: Optional[float] = None
    currency: str = "EUR"
    
    # Datos de tendencia (de Google Trends si disponible)
    trend_score: int = 0
    search_volume_estimate: str = ""
    
    # Análisis de mercado (de Perplexity)
    market_position: str = ""  # "líder", "challenger", "nicho", "emergente"
    competitors: List[str] = field(default_factory=list)
    target_audience: str = ""
    price_segment: str = ""  # "budget", "mid-range", "premium", "luxury"
    
    # Insights de Perplexity
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    
    # Métricas web (preparado para Semrush/Ahrefs)
    domain_authority: Optional[int] = None
    monthly_visits: Optional[int] = None
    organic_keywords: Optional[int] = None
    
    # Metadata
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    analysis_source: str = "perplexity"
    raw_content: str = ""
    errors: List[str] = field(default_factory=list)


class URLProductAnalyzer:
    """
    Analizador de URLs de productos.
    
    Extrae información de producto desde una URL y enriquece con datos
    de mercado usando Perplexity.
    """
    
    # Patrones de retailers conocidos para extracción optimizada
    KNOWN_RETAILERS = {
        "pccomponentes.com": {
            "brand_selector": "data-brand",
            "price_pattern": r'"price":\s*(\d+\.?\d*)',
            "category": "tech"
        },
        "amazon.es": {
            "brand_pattern": r'Marca:\s*</span>\s*<span[^>]*>([^<]+)',
            "price_pattern": r'"priceAmount":\s*(\d+\.?\d*)',
            "category": "general"
        },
        "amazon.com": {
            "brand_pattern": r'Marca:\s*</span>\s*<span[^>]*>([^<]+)',
            "price_pattern": r'"priceAmount":\s*(\d+\.?\d*)',
            "category": "general"
        },
        "mediamarkt.es": {
            "price_pattern": r'"price":\s*"?(\d+\.?\d*)',
            "category": "tech"
        },
        "aliexpress.com": {
            "price_pattern": r'"formattedActivityPrice":\s*"[€$]?\s*(\d+\.?\d*)',
            "category": "general"
        }
    }
    
    # Patrones genéricos de marcas tech (ORDEN IMPORTA: más específicos primero)
    BRAND_PATTERNS = [
        # Mini PCs (antes que CPUs para evitar conflictos con AMD/Intel)
        r'\b(Minisforum|Beelink|GMKtec|GEEKOM|Intel NUC|ASUS NUC|Acemagic|Trigkey|CHUWI)\b',
        # Periféricos gaming (marcas específicas primero)
        r'\b(Attack Shark|Pulsar|Lamzu|Finalmouse|Glorious|Wooting|Ducky|Keychron|Akko)\b',
        r'\b(Logitech|Razer|Corsair|SteelSeries|HyperX)\b',
        # Consolas
        r'\b(Steam Deck|ROG Ally|Legion Go|PlayStation|Xbox|Nintendo Switch)\b',
        # GPUs (modelos específicos)
        r'\b(ASUS|MSI|Gigabyte|EVGA|Zotac|Sapphire|PowerColor|XFX)\b',
        # Después las marcas genéricas de chips
        r'\b(NVIDIA|AMD|Intel)\b',
        # CPUs (patrones más específicos)
        r'\b(AMD Ryzen|Intel Core|Threadripper)\b',
        # Móviles
        r'\b(Apple|Samsung|Xiaomi|OnePlus|Google Pixel|Huawei|Oppo|Realme|Nothing)\b',
        # Monitores
        r'\b(LG|Dell|BenQ|AOC|ViewSonic|Acer|Alienware)\b',
        # Storage
        r'\b(Western Digital|WD|Seagate|Crucial|Kingston|Sabrent)\b',
        # Audio
        r'\b(Sony|Bose|Sennheiser|Audio-Technica|Beyerdynamic|JBL)\b',
    ]
    
    def __init__(self, perplexity_api_key: str = None):
        """
        Inicializa el analizador.
        
        Args:
            perplexity_api_key: API Key de Perplexity (opcional, se puede pasar después)
        """
        self.perplexity_key = perplexity_api_key
        self._last_error = ""
        
    def analyze_url(
        self, 
        url: str,
        use_perplexity: bool = True,
        extract_trends: bool = True
    ) -> ProductAnalysis:
        """
        Analiza una URL de producto.
        
        Args:
            url: URL del producto a analizar
            use_perplexity: Si usar Perplexity para enriquecer análisis
            extract_trends: Si extraer datos de Google Trends
            
        Returns:
            ProductAnalysis con todos los datos extraídos
        """
        result = ProductAnalysis(url=url, domain=self._extract_domain(url))
        
        # 1. Obtener contenido de la página
        page_content = self._fetch_page(url)
        if not page_content:
            result.errors.append(f"No se pudo obtener contenido de {url}")
            return result
        
        result.raw_content = page_content[:5000]  # Guardar muestra
        
        # 2. Extraer datos básicos (brand, price)
        self._extract_basic_info(result, page_content)
        
        # 3. Enriquecer con Perplexity
        if use_perplexity and self.perplexity_key:
            self._enrich_with_perplexity(result)
        
        # 4. Obtener datos de tendencia
        if extract_trends and result.brand:
            self._extract_trend_data(result)
        
        return result
    
    def _extract_domain(self, url: str) -> str:
        """Extrae el dominio de una URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Quitar www.
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
    
    def _fetch_page(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Obtiene el contenido de una página.
        
        Args:
            url: URL a obtener
            timeout: Timeout en segundos
            
        Returns:
            Contenido HTML o None si falla
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            return response.text
            
        except requests.exceptions.Timeout:
            self._last_error = "Timeout obteniendo página"
            return None
        except requests.exceptions.RequestException as e:
            self._last_error = f"Error HTTP: {str(e)[:100]}"
            return None
    
    def _extract_basic_info(self, result: ProductAnalysis, content: str):
        """
        Extrae información básica del producto del HTML.
        
        Args:
            result: ProductAnalysis a actualizar
            content: Contenido HTML
        """
        # Intentar con patrones específicos del retailer
        retailer_config = self.KNOWN_RETAILERS.get(result.domain, {})
        
        # Extraer precio
        price_pattern = retailer_config.get("price_pattern")
        if price_pattern:
            match = re.search(price_pattern, content)
            if match:
                try:
                    result.price = float(match.group(1))
                except ValueError:
                    pass
        
        # Si no hay patrón específico, usar genéricos
        if result.price is None:
            # Patrones genéricos de precio
            price_patterns = [
                r'"price":\s*"?(\d+\.?\d*)',
                r'"Price":\s*"?(\d+\.?\d*)',
                r'precio["\s:]+(\d+[,.]?\d*)',
                r'(\d+[,.]?\d*)\s*€',
            ]
            for pattern in price_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    try:
                        price_str = match.group(1).replace(",", ".")
                        result.price = float(price_str)
                        break
                    except ValueError:
                        continue
        
        # Extraer marca
        # Primero intentar patrones específicos
        brand_pattern = retailer_config.get("brand_pattern")
        if brand_pattern:
            match = re.search(brand_pattern, content, re.IGNORECASE)
            if match:
                result.brand = match.group(1).strip()
        
        # Si no, usar patrones genéricos de marcas conocidas
        if not result.brand:
            for pattern in self.BRAND_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    result.brand = match.group(1).strip()
                    break
        
        # Extraer título/modelo del <title> o meta tags
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
            # El título a menudo contiene marca - modelo - retailer
            # Intentar extraer el modelo
            if result.brand and result.brand.lower() in title.lower():
                # Buscar lo que viene después de la marca
                brand_idx = title.lower().find(result.brand.lower())
                after_brand = title[brand_idx + len(result.brand):].strip()
                # Limpiar separadores comunes
                after_brand = re.sub(r'^[\s\-\|:]+', '', after_brand)
                # Tomar hasta el próximo separador
                model_match = re.match(r'^([^|\-\–]+)', after_brand)
                if model_match:
                    result.model = model_match.group(1).strip()[:100]
            
            if not result.model:
                # Usar el título completo (truncado)
                result.model = title[:100]
        
        # Determinar categoría
        result.category = retailer_config.get("category", self._detect_category(content))
        
        # Determinar segmento de precio
        if result.price:
            result.price_segment = self._determine_price_segment(result.price, result.category)
    
    def _detect_category(self, content: str) -> str:
        """Detecta la categoría del producto basándose en el contenido"""
        content_lower = content.lower()
        
        categories = {
            "gpu": ["graphics card", "tarjeta gráfica", "rtx", "radeon", "geforce"],
            "cpu": ["processor", "procesador", "ryzen", "core i", "cpu"],
            "laptop": ["laptop", "portátil", "notebook", "macbook", "thinkpad"],
            "smartphone": ["smartphone", "móvil", "iphone", "galaxy", "pixel"],
            "monitor": ["monitor", "pantalla", "display", "27\"", "32\""],
            "mouse": ["mouse", "ratón", "gaming mouse", "wireless mouse"],
            "keyboard": ["keyboard", "teclado", "mechanical", "mecánico"],
            "headset": ["headset", "auriculares", "headphones", "gaming headset"],
            "mini_pc": ["mini pc", "nuc", "minisforum", "beelink"],
            "console": ["console", "consola", "playstation", "xbox", "switch", "steam deck"],
            "storage": ["ssd", "hdd", "nvme", "disco duro", "storage"],
            "ram": ["ram", "memoria", "ddr4", "ddr5"],
        }
        
        for category, keywords in categories.items():
            if any(kw in content_lower for kw in keywords):
                return category
        
        return "general"
    
    def _determine_price_segment(self, price: float, category: str) -> str:
        """Determina el segmento de precio basándose en la categoría"""
        # Umbrales por categoría (aproximados, en EUR)
        thresholds = {
            "gpu": {"budget": 200, "mid": 500, "premium": 1000},
            "cpu": {"budget": 150, "mid": 350, "premium": 600},
            "laptop": {"budget": 500, "mid": 1000, "premium": 1800},
            "smartphone": {"budget": 300, "mid": 600, "premium": 1000},
            "monitor": {"budget": 200, "mid": 400, "premium": 800},
            "mouse": {"budget": 30, "mid": 70, "premium": 120},
            "keyboard": {"budget": 50, "mid": 120, "premium": 200},
            "mini_pc": {"budget": 250, "mid": 500, "premium": 900},
            "default": {"budget": 100, "mid": 300, "premium": 700}
        }
        
        t = thresholds.get(category, thresholds["default"])
        
        if price < t["budget"]:
            return "budget"
        elif price < t["mid"]:
            return "mid-range"
        elif price < t["premium"]:
            return "premium"
        else:
            return "luxury"
    
    def _enrich_with_perplexity(self, result: ProductAnalysis):
        """
        Enriquece el análisis usando Perplexity.
        
        Args:
            result: ProductAnalysis a enriquecer
        """
        if not self.perplexity_key:
            result.errors.append("Perplexity API key no configurada")
            return
        
        # Construir query para Perplexity
        product_desc = f"{result.brand} {result.model}".strip() or result.url
        
        prompt = f"""Analiza este producto: {product_desc}
        
URL: {result.url}
Categoría detectada: {result.category}
Precio: {result.price} EUR

Proporciona un análisis de mercado estructurado con:

1. POSICIÓN DE MERCADO: ¿Es líder, challenger, nicho o emergente en su categoría?

2. COMPETIDORES DIRECTOS: Lista los 3-5 principales competidores (solo nombres de productos similares)

3. PÚBLICO OBJETIVO: Describe brevemente el perfil del comprador típico

4. FORTALEZAS: Lista 2-3 puntos fuertes del producto

5. DEBILIDADES: Lista 2-3 puntos débiles o críticas comunes

6. OPORTUNIDADES: Lista 2-3 oportunidades de mercado o tendencias favorables

Responde de forma concisa y estructurada."""

        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": "Eres un analista de mercado experto en tecnología y retail. Proporciona análisis concisos y accionables."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Parsear la respuesta
                self._parse_perplexity_response(result, content)
                result.analysis_source = "perplexity"
                
            else:
                result.errors.append(f"Perplexity error: HTTP {response.status_code}")
                
        except Exception as e:
            result.errors.append(f"Error en Perplexity: {str(e)[:100]}")
    
    def _parse_perplexity_response(self, result: ProductAnalysis, content: str):
        """Parsea la respuesta de Perplexity y actualiza el resultado"""
        content_lower = content.lower()
        
        # Detectar posición de mercado
        if "líder" in content_lower or "leader" in content_lower:
            result.market_position = "líder"
        elif "challenger" in content_lower or "retador" in content_lower:
            result.market_position = "challenger"
        elif "nicho" in content_lower or "niche" in content_lower:
            result.market_position = "nicho"
        elif "emergente" in content_lower or "emerging" in content_lower:
            result.market_position = "emergente"
        else:
            result.market_position = "establecido"
        
        # Extraer secciones (búsqueda simple por patrones)
        sections = {
            "competitors": [r"competidores?[:\s]+([^\n]+(?:\n(?![A-Z0-9])[^\n]+)*)", r"competitors?[:\s]+([^\n]+)"],
            "strengths": [r"fortalezas?[:\s]+([^\n]+(?:\n[-•*][^\n]+)*)", r"puntos?\s+fuertes?[:\s]+([^\n]+)"],
            "weaknesses": [r"debilidades?[:\s]+([^\n]+(?:\n[-•*][^\n]+)*)", r"puntos?\s+débiles?[:\s]+([^\n]+)"],
            "opportunities": [r"oportunidades?[:\s]+([^\n]+(?:\n[-•*][^\n]+)*)"],
            "audience": [r"público\s+objetivo[:\s]+([^\n]+)", r"target[:\s]+([^\n]+)"]
        }
        
        for section, patterns in sections.items():
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
                if match:
                    text = match.group(1).strip()
                    
                    if section == "competitors":
                        # Extraer lista de competidores
                        items = re.split(r'[,\n•\-\*]+', text)
                        result.competitors = [i.strip() for i in items if len(i.strip()) > 2][:5]
                    elif section == "strengths":
                        items = re.split(r'[\n•\-\*]+', text)
                        result.strengths = [i.strip() for i in items if len(i.strip()) > 5][:3]
                    elif section == "weaknesses":
                        items = re.split(r'[\n•\-\*]+', text)
                        result.weaknesses = [i.strip() for i in items if len(i.strip()) > 5][:3]
                    elif section == "opportunities":
                        items = re.split(r'[\n•\-\*]+', text)
                        result.opportunities = [i.strip() for i in items if len(i.strip()) > 5][:3]
                    elif section == "audience":
                        result.target_audience = text[:200]
                    
                    break
    
    def _extract_trend_data(self, result: ProductAnalysis):
        """
        Extrae datos de tendencia para la marca/producto.
        
        Por ahora es un placeholder - se puede conectar con GoogleTrendsModule.
        """
        # TODO: Integrar con GoogleTrendsModule
        # Por ahora dejamos vacío - se puede implementar llamando a:
        # from modules.google_trends import GoogleTrendsModule
        pass
    
    def analyze_multiple(
        self, 
        urls: List[str],
        use_perplexity: bool = True
    ) -> List[ProductAnalysis]:
        """
        Analiza múltiples URLs.
        
        Args:
            urls: Lista de URLs a analizar
            use_perplexity: Si usar Perplexity
            
        Returns:
            Lista de ProductAnalysis
        """
        results = []
        for url in urls:
            try:
                result = self.analyze_url(url, use_perplexity=use_perplexity)
                results.append(result)
            except Exception as e:
                # Crear resultado con error
                error_result = ProductAnalysis(
                    url=url,
                    domain=self._extract_domain(url),
                    errors=[str(e)]
                )
                results.append(error_result)
        
        return results
    
    def compare_products(
        self,
        analyses: List[ProductAnalysis]
    ) -> Dict[str, Any]:
        """
        Compara múltiples productos analizados.
        
        Args:
            analyses: Lista de ProductAnalysis
            
        Returns:
            Dict con comparación
        """
        if len(analyses) < 2:
            return {"error": "Se necesitan al menos 2 productos para comparar"}
        
        # Extraer marcas únicas
        brands = list(set(a.brand for a in analyses if a.brand))
        
        # Comparar precios
        prices = [(a.brand, a.model, a.price) for a in analyses if a.price]
        prices.sort(key=lambda x: x[2])
        
        # Comparar posiciones de mercado
        positions = {}
        for a in analyses:
            if a.market_position:
                positions[f"{a.brand} {a.model}".strip()] = a.market_position
        
        # Todos los competidores mencionados
        all_competitors = []
        for a in analyses:
            all_competitors.extend(a.competitors)
        
        return {
            "products_analyzed": len(analyses),
            "brands": brands,
            "price_ranking": [
                {"brand": b, "model": m, "price": p} 
                for b, m, p in prices
            ],
            "market_positions": positions,
            "mentioned_competitors": list(set(all_competitors)),
            "categories": list(set(a.category for a in analyses if a.category))
        }


# =============================================================================
# FUNCIONES DE AYUDA
# =============================================================================

def get_url_analyzer() -> Optional[URLProductAnalyzer]:
    """
    Factory para obtener analizador configurado.
    
    Returns:
        URLProductAnalyzer si Perplexity está configurado
    """
    perplexity_key = st.secrets.get("PERPLEXITY_API_KEY", "")
    
    if perplexity_key and perplexity_key.startswith("pplx-"):
        return URLProductAnalyzer(perplexity_key)
    
    # Devolver analizador sin Perplexity (solo extracción básica)
    return URLProductAnalyzer()


def render_url_analyzer_form() -> Optional[ProductAnalysis]:
    """
    Renderiza formulario de análisis de URL en Streamlit.
    
    Returns:
        ProductAnalysis si se analizó, None si no
    """
    st.markdown("### 🔗 Analizar URL de Producto")
    
    url = st.text_input(
        "URL del producto",
        placeholder="https://www.pccomponentes.com/producto-ejemplo",
        help="Introduce la URL de un producto para extraer marca, modelo y análisis de mercado"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        use_perplexity = st.checkbox("Enriquecer con IA", value=True, help="Usa Perplexity para análisis de mercado")
    with col2:
        extract_trends = st.checkbox("Extraer tendencias", value=False, help="Conectar con Google Trends")
    
    if st.button("🔍 Analizar", type="primary"):
        if not url:
            st.error("Introduce una URL")
            return None
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        analyzer = get_url_analyzer()
        
        with st.spinner("Analizando producto..."):
            result = analyzer.analyze_url(
                url,
                use_perplexity=use_perplexity,
                extract_trends=extract_trends
            )
        
        # Mostrar resultados
        if result.errors:
            for error in result.errors:
                st.warning(f"⚠️ {error}")
        
        # Datos básicos
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Marca", result.brand or "No detectada")
        with col2:
            st.metric("Precio", f"{result.price:.2f} €" if result.price else "N/A")
        with col3:
            st.metric("Segmento", result.price_segment.title() if result.price_segment else "N/A")
        
        if result.model:
            st.info(f"**Modelo:** {result.model}")
        
        # Análisis de mercado
        if result.market_position or result.competitors:
            st.markdown("#### 📊 Análisis de Mercado")
            
            col1, col2 = st.columns(2)
            with col1:
                if result.market_position:
                    position_colors = {
                        "líder": "🟢",
                        "challenger": "🟡",
                        "nicho": "🔵",
                        "emergente": "🟣",
                        "establecido": "⚪"
                    }
                    icon = position_colors.get(result.market_position, "⚪")
                    st.markdown(f"**Posición:** {icon} {result.market_position.title()}")
                
                if result.target_audience:
                    st.markdown(f"**Audiencia:** {result.target_audience}")
            
            with col2:
                if result.competitors:
                    st.markdown("**Competidores:**")
                    for comp in result.competitors[:5]:
                        st.markdown(f"- {comp}")
        
        # SWOT simplificado
        if result.strengths or result.weaknesses or result.opportunities:
            st.markdown("#### 💡 Insights")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if result.strengths:
                    st.markdown("**✅ Fortalezas**")
                    for s in result.strengths:
                        st.markdown(f"- {s}")
            with col2:
                if result.weaknesses:
                    st.markdown("**⚠️ Debilidades**")
                    for w in result.weaknesses:
                        st.markdown(f"- {w}")
            with col3:
                if result.opportunities:
                    st.markdown("**🚀 Oportunidades**")
                    for o in result.opportunities:
                        st.markdown(f"- {o}")
        
        # Botón para analizar esta marca
        if result.brand:
            st.markdown("---")
            if st.button(f"📈 Analizar tendencia de '{result.brand}'"):
                st.session_state["search_query"] = result.brand
                st.rerun()
        
        return result
    
    return None
