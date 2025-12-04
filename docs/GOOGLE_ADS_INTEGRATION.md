# Integración con Google Ads y Google Shopping APIs

## Resumen

Este documento describe cómo integrar las APIs de Google para obtener datos REALES de volúmenes de búsqueda y productos.

---

## 1. Google Ads API (Keyword Planner) - VOLÚMENES REALES

### ¿Qué proporciona?
- **Volúmenes de búsqueda mensuales EXACTOS** (no estimaciones)
- Datos de competencia
- CPC (coste por clic) estimado
- Tendencias históricas

### Requisitos
1. **Cuenta de Google Ads** con historial de gasto (mínimo ~10€)
2. **Developer Token** (solicitar a Google)
3. **OAuth 2.0 credentials**

### Pasos para configurar

#### 1. Crear cuenta de Google Ads
```
1. Ir a https://ads.google.com
2. Crear cuenta
3. Configurar método de pago
4. Crear al menos una campaña pequeña (~10€)
5. Esperar 24-48h para activación completa
```

#### 2. Obtener Developer Token
```
1. Ir a Google Ads API Center
2. Solicitar token de desarrollo
3. Esperar aprobación (1-2 días laborables)
```

#### 3. Configurar OAuth 2.0
```
1. Ir a Google Cloud Console
2. Crear proyecto
3. Habilitar Google Ads API
4. Crear credenciales OAuth 2.0
5. Descargar client_secrets.json
```

### Código de ejemplo

```python
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

class GoogleAdsKeywordPlanner:
    """Obtiene volúmenes reales de Google Ads Keyword Planner"""
    
    def __init__(self, config_path: str):
        self.client = GoogleAdsClient.load_from_storage(config_path)
    
    def get_keyword_volumes(
        self,
        keywords: list,
        language_id: str = "1003",  # Español
        location_ids: list = ["2724"]  # España
    ) -> dict:
        """
        Obtiene volúmenes de búsqueda reales
        
        Args:
            keywords: Lista de keywords
            language_id: ID de idioma (1003=español, 1000=inglés)
            location_ids: IDs de ubicación (2724=España, 2840=USA)
        
        Returns:
            Dict con volúmenes mensuales reales
        """
        keyword_plan_idea_service = self.client.get_service(
            "KeywordPlanIdeaService"
        )
        
        request = self.client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = self.customer_id
        request.language = self.client.get_service(
            "GoogleAdsService"
        ).language_constant_path(language_id)
        
        request.geo_target_constants.extend([
            self.client.get_service(
                "GoogleAdsService"
            ).geo_target_constant_path(loc_id)
            for loc_id in location_ids
        ])
        
        request.keyword_seed.keywords.extend(keywords)
        
        results = {}
        
        try:
            response = keyword_plan_idea_service.generate_keyword_ideas(
                request=request
            )
            
            for idea in response:
                keyword = idea.text
                metrics = idea.keyword_idea_metrics
                
                results[keyword] = {
                    "avg_monthly_searches": metrics.avg_monthly_searches,
                    "competition": metrics.competition.name,
                    "competition_index": metrics.competition_index,
                    "low_top_of_page_bid_micros": metrics.low_top_of_page_bid_micros,
                    "high_top_of_page_bid_micros": metrics.high_top_of_page_bid_micros,
                    "monthly_search_volumes": [
                        {
                            "month": vol.month.name,
                            "year": vol.year,
                            "searches": vol.monthly_searches
                        }
                        for vol in metrics.monthly_search_volumes
                    ]
                }
                
        except GoogleAdsException as ex:
            print(f"Error: {ex}")
            
        return results
```

### Configuración en secrets.toml

```toml
# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN = "xxx"
GOOGLE_ADS_CLIENT_ID = "xxx.apps.googleusercontent.com"
GOOGLE_ADS_CLIENT_SECRET = "xxx"
GOOGLE_ADS_REFRESH_TOKEN = "xxx"
GOOGLE_ADS_CUSTOMER_ID = "123-456-7890"
```

### Instalación

```bash
pip install google-ads==21.0.0
```

---

## 2. Google Shopping API (Content API for Shopping)

### ¿Qué proporciona?
- Productos reales de tu cuenta Merchant Center
- Precios actualizados
- Stock disponible
- Rendimiento de productos

### Requisitos
1. **Cuenta de Google Merchant Center**
2. **Credenciales API** de Google Cloud
3. Productos subidos al Merchant Center

### Código de ejemplo

```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

class GoogleShoppingAPI:
    """Obtiene productos de Google Merchant Center"""
    
    SCOPES = ['https://www.googleapis.com/auth/content']
    
    def __init__(self, credentials_path: str, merchant_id: str):
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=self.SCOPES
        )
        self.service = build('content', 'v2.1', credentials=credentials)
        self.merchant_id = merchant_id
    
    def list_products(self, max_results: int = 250) -> list:
        """Lista productos del Merchant Center"""
        request = self.service.products().list(
            merchantId=self.merchant_id,
            maxResults=max_results
        )
        
        products = []
        while request:
            response = request.execute()
            products.extend(response.get('resources', []))
            request = self.service.products().list_next(
                request, response
            )
        
        return products
    
    def get_product_performance(
        self,
        product_id: str,
        start_date: str,
        end_date: str
    ) -> dict:
        """Obtiene rendimiento de un producto"""
        # Requiere Reports API
        pass
```

---

## 3. Alternativas sin cuenta de Google Ads

### DataForSEO API (~50€/mes)
```python
import requests
import base64

class DataForSEOAPI:
    BASE_URL = "https://api.dataforseo.com/v3"
    
    def __init__(self, login: str, password: str):
        cred = base64.b64encode(f"{login}:{password}".encode()).decode()
        self.headers = {"Authorization": f"Basic {cred}"}
    
    def get_search_volume(
        self,
        keywords: list,
        location_code: int = 2724,  # España
        language_code: str = "es"
    ) -> dict:
        """Obtiene volúmenes de búsqueda"""
        endpoint = f"{self.BASE_URL}/keywords_data/google_ads/search_volume/live"
        
        payload = [{
            "keywords": keywords,
            "location_code": location_code,
            "language_code": language_code
        }]
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=self.headers
        )
        
        return response.json()
```

### Configuración en secrets.toml
```toml
DATAFORSEO_LOGIN = "tu_email@ejemplo.com"
DATAFORSEO_PASSWORD = "tu_password"
```

---

## 4. Integración en Abra Trend Hunter

### Añadir al módulo de search_volume.py

```python
# En search_volume.py

class RealVolumeProvider:
    """Proveedor de volúmenes reales"""
    
    def __init__(self):
        self.google_ads = None
        self.dataforseo = None
        
        # Intentar inicializar Google Ads
        if st.secrets.get("GOOGLE_ADS_DEVELOPER_TOKEN"):
            try:
                from .google_ads_provider import GoogleAdsKeywordPlanner
                self.google_ads = GoogleAdsKeywordPlanner()
            except Exception:
                pass
        
        # Fallback a DataForSEO
        if not self.google_ads and st.secrets.get("DATAFORSEO_LOGIN"):
            try:
                self.dataforseo = DataForSEOAPI(
                    st.secrets["DATAFORSEO_LOGIN"],
                    st.secrets["DATAFORSEO_PASSWORD"]
                )
            except Exception:
                pass
    
    def get_volume(self, keyword: str, geo: str = "ES") -> dict:
        """Obtiene volumen real de la mejor fuente disponible"""
        
        if self.google_ads:
            return self.google_ads.get_keyword_volumes([keyword])
        
        if self.dataforseo:
            return self.dataforseo.get_search_volume([keyword])
        
        # Sin proveedores reales, retornar None
        return None
    
    @property
    def source(self) -> str:
        if self.google_ads:
            return "Google Ads Keyword Planner"
        if self.dataforseo:
            return "DataForSEO"
        return "Estimación (sin API de volúmenes)"
```

---

## 5. Costes estimados

| Servicio | Coste | Volúmenes | Límites |
|----------|-------|-----------|---------|
| Google Ads API | Gratis* | Reales | Requiere gasto en ads |
| DataForSEO | ~50€/mes | Reales | 10,000 créditos |
| Semrush API | ~100€/mes | Reales | Según plan |
| Ahrefs API | ~100€/mes | Reales | Según plan |
| SerpAPI (actual) | ~50€/mes | Índice 0-100 | 5,000 búsquedas |

*Google Ads API es gratis pero requiere una cuenta con historial de gasto.

---

## 6. Recomendación

Para PCComponentes, la mejor opción sería:

1. **Corto plazo**: Usar DataForSEO (~50€/mes) para volúmenes reales
2. **Largo plazo**: Configurar Google Ads API (gratis si ya tenéis campañas)

La integración con SerpAPI seguirá funcionando para:
- Google Trends (índice relativo)
- Related Queries
- Google Shopping (productos)
- Google News

Los volúmenes reales complementarían los datos existentes.
