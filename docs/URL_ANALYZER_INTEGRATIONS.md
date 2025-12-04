# Guía de Integraciones - URL Analyzer

## Arquitectura Actual

El módulo `url_analyzer.py` proporciona análisis de productos desde URLs con:

- **Extracción básica**: Marca, modelo, precio, categoría
- **Análisis de mercado**: Vía Perplexity (posición, competidores, SWOT)
- **Preparado para expansión**: Campos para Semrush, Ahrefs, etc.

## Uso Actual

```python
from modules.url_analyzer import get_url_analyzer, render_url_analyzer_form

# Opción 1: Formulario en Streamlit
result = render_url_analyzer_form()

# Opción 2: Análisis programático
analyzer = get_url_analyzer()
result = analyzer.analyze_url("https://www.pccomponentes.com/producto")

# Datos disponibles
print(result.brand)           # "Logitech"
print(result.model)           # "G Pro X Superlight"
print(result.price)           # 129.99
print(result.category)        # "mouse"
print(result.market_position) # "líder"
print(result.competitors)     # ["Razer DeathAdder", "Pulsar X2", ...]
print(result.strengths)       # ["Peso ultraligero", "Sensor HERO 25K", ...]
```

## Integraciones Futuras

### 1. Semrush API

**Endpoint**: `https://api.semrush.com/`

**Datos que obtendríamos**:
- Domain Authority
- Tráfico orgánico mensual
- Keywords posicionadas
- Backlinks
- Posición en SERPs

**Implementación sugerida**:

```python
# En url_analyzer.py, añadir método:

def _enrich_with_semrush(self, result: ProductAnalysis):
    """Enriquece con datos de Semrush"""
    if not self.semrush_key:
        return
    
    domain = result.domain
    
    # API de Domain Overview
    response = requests.get(
        "https://api.semrush.com/",
        params={
            "type": "domain_ranks",
            "key": self.semrush_key,
            "domain": domain,
            "database": "es"  # España
        }
    )
    
    if response.status_code == 200:
        data = response.text.split(";")
        result.domain_authority = int(data[0])
        result.monthly_visits = int(data[1])
        result.organic_keywords = int(data[2])
```

**Configuración secrets.toml**:
```toml
SEMRUSH_API_KEY = "xxxxxxxxxxxxxxxxxxxxx"
```

**Precios Semrush API** (aprox.):
- Pro: $119.95/mes (10,000 unidades/mes)
- Guru: $229.95/mes (30,000 unidades/mes)
- Business: $449.95/mes (50,000 unidades/mes)

---

### 2. Ahrefs API

**Endpoint**: `https://apiv2.ahrefs.com`

**Datos que obtendríamos**:
- Domain Rating (DR)
- URL Rating (UR)
- Backlinks
- Referring domains
- Tráfico orgánico

**Implementación sugerida**:

```python
def _enrich_with_ahrefs(self, result: ProductAnalysis):
    """Enriquece con datos de Ahrefs"""
    if not self.ahrefs_key:
        return
    
    response = requests.get(
        "https://apiv2.ahrefs.com",
        params={
            "token": self.ahrefs_key,
            "from": "domain_rating",
            "target": result.domain,
            "mode": "domain"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        result.domain_authority = data.get("domain_rating")
```

**Precios Ahrefs API**:
- Lite: $99/mes
- Standard: $199/mes
- Advanced: $399/mes

---

### 3. SimilarWeb API

**Datos que obtendríamos**:
- Visitas mensuales estimadas
- Tiempo en sitio
- Bounce rate
- Fuentes de tráfico
- Geografía de visitantes

**Implementación sugerida**:

```python
def _enrich_with_similarweb(self, result: ProductAnalysis):
    """Enriquece con datos de SimilarWeb"""
    response = requests.get(
        f"https://api.similarweb.com/v1/website/{result.domain}/total-traffic-and-engagement/visits",
        headers={"api-key": self.similarweb_key}
    )
    
    if response.status_code == 200:
        data = response.json()
        result.monthly_visits = data.get("visits")
```

---

### 4. Google Search Console API (Gratis)

Si tienes acceso a Search Console del dominio analizado:

**Datos que obtendríamos**:
- Impresiones y clics reales
- CTR
- Posición media
- Queries que traen tráfico

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

def _enrich_with_gsc(self, result: ProductAnalysis):
    """Enriquece con datos de Google Search Console"""
    credentials = service_account.Credentials.from_service_account_file(
        'service_account.json',
        scopes=['https://www.googleapis.com/auth/webmasters.readonly']
    )
    
    service = build('searchconsole', 'v1', credentials=credentials)
    
    response = service.searchanalytics().query(
        siteUrl=f"https://{result.domain}",
        body={
            "startDate": "2024-01-01",
            "endDate": "2024-12-01",
            "dimensions": ["query"],
            "rowLimit": 100
        }
    ).execute()
```

---

## Campos Preparados en ProductAnalysis

El dataclass ya tiene campos reservados para estas integraciones:

```python
@dataclass
class ProductAnalysis:
    # ... campos actuales ...
    
    # Métricas web (preparado para Semrush/Ahrefs)
    domain_authority: Optional[int] = None   # DA de Semrush o DR de Ahrefs
    monthly_visits: Optional[int] = None     # Visitas mensuales
    organic_keywords: Optional[int] = None   # Keywords posicionadas
```

---

## Roadmap Sugerido

### Fase 1 (Actual) ✅
- [x] Extracción básica (marca, precio, categoría)
- [x] Análisis con Perplexity (posición mercado, competidores)
- [x] UI en Streamlit

### Fase 2 (Corto plazo)
- [ ] Caché de análisis (evitar re-analizar URLs)
- [ ] Histórico de precios (si se analiza misma URL múltiples veces)
- [ ] Exportar análisis a CSV/JSON

### Fase 3 (Medio plazo)
- [ ] Integración Semrush (requiere suscripción)
- [ ] Integración Ahrefs (requiere suscripción)
- [ ] Dashboard de competidores

### Fase 4 (Largo plazo)
- [ ] Alertas de cambio de precio
- [ ] Tracking de posicionamiento
- [ ] Comparativas automáticas con competencia

---

## Ejemplo Completo de Análisis

```python
from modules.url_analyzer import URLProductAnalyzer

# Con Perplexity
analyzer = URLProductAnalyzer(perplexity_api_key="pplx-xxx")

# Analizar producto
result = analyzer.analyze_url(
    "https://www.pccomponentes.com/logitech-g-pro-x-superlight-2-raton-gaming"
)

# Resultado completo
{
    "url": "https://www.pccomponentes.com/...",
    "domain": "pccomponentes.com",
    "brand": "Logitech",
    "model": "G Pro X Superlight 2",
    "category": "mouse",
    "price": 159.99,
    "price_segment": "premium",
    "market_position": "líder",
    "competitors": ["Razer DeathAdder V3", "Pulsar X2", "Finalmouse UltralightX"],
    "target_audience": "Gamers competitivos y esports",
    "strengths": ["Peso ultraligero (60g)", "Sensor HERO 2", "Batería 95 horas"],
    "weaknesses": ["Precio elevado", "Sin Bluetooth"],
    "opportunities": ["Crecimiento esports", "Mercado premium en expansión"],
    
    # Campos para futuras integraciones (actualmente None)
    "domain_authority": None,
    "monthly_visits": None,
    "organic_keywords": None
}
```

---

## Notas de Implementación

1. **Rate Limiting**: Todas las APIs tienen límites. Implementar caché.

2. **Costes**: Semrush/Ahrefs son caros. Evaluar ROI antes de integrar.

3. **Alternativas gratuitas**:
   - Perplexity (ya integrado) - $20/mes
   - Google Search Console (gratis, pero solo tus dominios)
   - Ubersuggest API (más barato que Semrush)

4. **Prioridad sugerida**: 
   - Si solo quieres análisis de mercado → Perplexity (actual)
   - Si quieres SEO competitivo → Semrush o Ahrefs
   - Si quieres tráfico estimado → SimilarWeb
