# 🔮 Abra Trend Hunter

> Detecta marcas y productos emergentes en hardware antes que la competencia

**Abra Trend Hunter** es una herramienta de análisis de tendencias diseñada para Product Discovery, inspirada en Glimpse, Google Trends y Exploding Topics de Semrush.

![Abra](https://img.shields.io/badge/Pokemon-Abra-F5C518?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square)

## ✨ Características

### 📊 Análisis de Tendencias
- 📈 **Gráfico de tendencia temporal** con línea de trayectoria suavizada
- 🎯 **Sistema de Scoring dual**:
  - Trend Score: Qué tan "hot" está ahora
  - Potential Score: Predicción de explosión futura
- 📅 **Panel de estacionalidad** con análisis mensual
- 🔍 **Related Queries y Topics** con badges de crecimiento
- ❓ **"La gente también busca" (PAA)** expandido recursivamente

### 🛍️ Análisis de Productos
- 🚀 **Matriz de oportunidad** tipo BCG (Emergente/Estrella/Consolidado/Nicho)
- 📊 **Ranking de productos** con sparklines y volumen de búsqueda
- 🔄 **Ciclo de vida** del producto (Introducción → Crecimiento → Madurez → Declive)
- 📈 **Comparativa visual** entre productos detectados
- 💡 **Insights automáticos** con recomendaciones

### 🤖 Inteligencia Artificial
- 🔮 **Análisis IA** con Claude, GPT-4 o Perplexity (a elección)
- 📝 **Ideas para blog** generadas automáticamente
- 🎯 **Recomendaciones estratégicas** personalizadas

### 📰 Noticias y Contexto
- 📰 **Google News** integrado con análisis de sentimiento
- 🌍 **Comparativa por países** (ES, PT, FR, IT, DE)
- 🏷️ **Detección de marcas competidoras**

### 🔒 Seguridad
- ✅ Sanitización XSS en todos los inputs
- ✅ Protección contra división por cero
- ✅ Validación de datos robusta
- ✅ Manejo de errores completo

## 🚀 Quick Start

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/abra-trend-hunter.git
cd abra-trend-hunter
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar secrets

Crea el archivo `.streamlit/secrets.toml`:

```toml
# API Requerida
SERPAPI_KEY = "tu_serpapi_key"

# APIs de IA (al menos una)
ANTHROPIC_API_KEY = "tu_anthropic_key"   # Para Claude
OPENAI_API_KEY = "tu_openai_key"          # Para GPT-4
PERPLEXITY_API_KEY = "tu_perplexity_key"  # Para Perplexity
```

### 4. Ejecutar

```bash
streamlit run app.py
```

## 📦 Despliegue en Streamlit Cloud

1. Sube el repo a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repo
4. En **Advanced settings > Secrets**, añade tus API keys:

```toml
SERPAPI_KEY = "xxx"
ANTHROPIC_API_KEY = "xxx"
OPENAI_API_KEY = "xxx"
PERPLEXITY_API_KEY = "xxx"
```

5. ¡Deploy!

## 🔑 API Keys necesarias

| API | Uso | Requerida | Obtener |
|-----|-----|-----------|---------|
| SerpAPI | Google Trends, SERP, PAA | ✅ Sí | [serpapi.com](https://serpapi.com) |
| Anthropic | Análisis con Claude | ⭕ Opcional | [console.anthropic.com](https://console.anthropic.com) |
| OpenAI | Análisis con GPT-4 | ⭕ Opcional | [platform.openai.com](https://platform.openai.com) |
| Perplexity | Análisis con búsqueda real-time | ⭕ Opcional | [perplexity.ai](https://www.perplexity.ai) |

> 💡 Necesitas **SerpAPI** obligatoriamente y **al menos una IA** para el análisis completo.

## 🏗️ Arquitectura

```
abra-trend-hunter/
├── app.py                    # Aplicación principal (490 líneas)
├── requirements.txt
├── .streamlit/
│   └── config.toml           # Configuración de Streamlit
│
├── modules/                  # Módulos de datos (~3,500 líneas)
│   ├── google_trends.py      # Google Trends via SerpAPI
│   ├── related_queries.py    # Queries y topics relacionados
│   ├── serp_paa.py          # People Also Ask expandido
│   ├── google_news.py       # Noticias + análisis de sentimiento
│   ├── product_analysis.py  # Análisis de productos
│   ├── scoring.py           # Motor de scoring dual
│   ├── ai_analysis.py       # Orquestador de IA
│   └── providers/           # Proveedores de IA
│       ├── claude_provider.py
│       ├── openai_provider.py
│       └── perplexity_provider.py
│
├── components/              # Componentes UI (~2,800 líneas)
│   ├── trend_chart.py       # Gráficos temporales
│   ├── seasonality.py       # Panel estacional
│   ├── score_cards.py       # Cards de scoring
│   ├── related_cards.py     # Related queries/topics
│   ├── keyword_table.py     # Tabla de keywords + PAA
│   ├── geo_map.py           # Mapa y comparativa países
│   ├── news_panel.py        # Panel de noticias
│   └── product_matrix.py    # Matriz BCG + ciclo vida
│
├── utils/                   # Utilidades (~550 líneas)
│   ├── __init__.py          # Helpers generales
│   └── validation.py        # Sanitización y validación
│
└── assets/
    └── custom.css           # Estilos personalizados
```

**Total: ~7,600 líneas de código Python**
│       ├── claude_provider.py
│       ├── openai_provider.py
│       └── perplexity_provider.py
├── components/              # Componentes UI
│   ├── trend_chart.py       # Gráfico principal
│   ├── seasonality.py       # Panel estacionalidad
│   ├── score_cards.py       # Cards de scoring
│   ├── related_cards.py     # Cards relacionadas
│   ├── keyword_table.py     # Tabla de keywords
│   └── geo_map.py           # Mapa geográfico
├── utils/                   # Utilidades
│   └── __init__.py
└── assets/
    └── custom.css           # Estilos personalizados
```

## 🎨 Personalización

### Cambiar tema

Edita `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#F5C518"      # Color principal (dorado Abra)
backgroundColor = "#FAFAFA"    # Fondo
secondaryBackgroundColor = "#F0F2F6"
textColor = "#1A1A2E"
```

### Añadir nuevas fuentes de datos

1. Crea un nuevo módulo en `modules/`
2. Implementa los métodos necesarios
3. Impórtalo en `app.py`

Ejemplo para YouTube:
```python
# modules/youtube_trends.py
class YouTubeTrendsModule:
    def get_video_trends(self, keyword: str) -> dict:
        # Tu implementación
        pass
```

## 📊 Scoring

### Trend Score (0-100)
Mide qué tan "trendy" es la marca ahora:
- **Valor actual vs media** (25%)
- **Tasa de crecimiento** (30%)
- **Momentum** (25%)
- **Consistencia** (20%)

### Potential Score (0-100)
Predice probabilidad de explosión:
- **Aceleración del crecimiento** (30%)
- **Etapa temprana** (25%)
- **Rising queries** (25%)
- **Espacio de crecimiento** (20%)

### Nivel de Oportunidad
- 🔥 **ALTA** (≥75): Actuar ahora
- ⚡ **MEDIA** (55-74): Monitorizar
- 👀 **BAJA** (35-54): Observar
- ❄️ **MUY BAJA** (<35): No prioritario

## 🔮 Roadmap

- [ ] Alertas automáticas (integración n8n)
- [ ] Datos de YouTube
- [ ] Datos de Amazon
- [ ] Tracking de competidores
- [ ] Dashboard de múltiples marcas
- [ ] Exportación de informes PDF

## 🤝 Contribuir

1. Fork el repo
2. Crea tu rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit (`git commit -m 'Añade nueva funcionalidad'`)
4. Push (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE)

---

<p align="center">
  <b>🔮 Abra Trend Hunter</b><br>
  <i>Detecta el futuro antes que nadie</i><br><br>
  Hecho con ❤️ para PCComponentes
</p>
