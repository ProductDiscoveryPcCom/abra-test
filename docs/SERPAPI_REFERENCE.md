# SerpAPI - Google Trends Reference

Documentación de las APIs de Google Trends disponibles en SerpAPI.

## Endpoints Disponibles

### 1. Interest over Time (TIMESERIES)
```
GET https://serpapi.com/search.json
  ?engine=google_trends
  &q=keyword
  &data_type=TIMESERIES
  &geo=ES
  &date=today 12-m
  &cat=0
  &api_key=xxx
```

**Respuesta:**
```json
{
  "interest_over_time": {
    "timeline_data": [
      {
        "date": "Dec 2023",
        "values": [{"query": "keyword", "value": "75", "extracted_value": 75}]
      }
    ],
    "averages": [{"query": "keyword", "value": 62}]
  }
}
```

---

### 2. Interest by Region (GEO_MAP_0) - Single Query
```
GET https://serpapi.com/search.json
  ?engine=google_trends
  &q=keyword
  &data_type=GEO_MAP_0
  &geo=ES
  &date=today 12-m
  &api_key=xxx
```

**Respuesta:**
```json
{
  "interest_by_region": [
    {
      "geo": "ES-CT",
      "location": "Catalonia",
      "coordinates": {"lat": 41.59, "lng": 1.52},
      "value": "100",
      "extracted_value": 100,
      "max_value_index": 0
    }
  ]
}
```

---

### 3. Compared Breakdown by Region (GEO_MAP) - Multiple Queries
```
GET https://serpapi.com/search.json
  ?engine=google_trends
  &q=nvidia,amd
  &data_type=GEO_MAP
  &geo=ES
  &date=today 12-m
  &api_key=xxx
```

**Respuesta:**
```json
{
  "compared_breakdown_by_region": [
    {
      "geo": "ES-CT",
      "location": "Catalonia",
      "coordinates": {"lat": 41.59, "lng": 1.52},
      "max_value_index": 0,
      "values": [
        {"query": "nvidia", "value": "100", "extracted_value": 100},
        {"query": "amd", "value": "67", "extracted_value": 67}
      ]
    }
  ]
}
```

---

### 4. Related Queries (RELATED_QUERIES)
```
GET https://serpapi.com/search.json
  ?engine=google_trends
  &q=keyword
  &data_type=RELATED_QUERIES
  &geo=ES
  &date=today 12-m
  &api_key=xxx
```

**Respuesta:**
```json
{
  "related_queries": {
    "rising": [
      {
        "query": "keyword gaming",
        "value": "+500%",
        "extracted_value": 500,
        "link": "https://trends.google.com/..."
      }
    ],
    "top": [
      {
        "query": "keyword amazon",
        "value": "100",
        "extracted_value": 100,
        "link": "https://trends.google.com/..."
      }
    ]
  }
}
```

---

### 5. Related Topics (RELATED_TOPICS)
```
GET https://serpapi.com/search.json
  ?engine=google_trends
  &q=keyword
  &data_type=RELATED_TOPICS
  &geo=ES
  &date=today 12-m
  &api_key=xxx
```

**Respuesta:**
```json
{
  "related_topics": {
    "rising": [
      {
        "topic": {
          "mid": "/m/0k8z",
          "title": "Gaming",
          "type": "Topic"
        },
        "value": "Breakout",
        "extracted_value": "Breakout",
        "link": "https://trends.google.com/..."
      }
    ],
    "top": [
      {
        "topic": {
          "mid": "/m/04n3q",
          "title": "Computer hardware",
          "type": "Topic"
        },
        "value": "100",
        "extracted_value": 100,
        "link": "https://trends.google.com/..."
      }
    ]
  }
}
```

---

### 6. Trending Now
```
GET https://serpapi.com/search.json
  ?engine=google_trends_trending_now
  &geo=ES
  &hours=24
  &category_id=5
  &only_active=true
  &api_key=xxx
```

**Respuesta:**
```json
{
  "trending_searches": [
    {
      "query": "iPhone 16",
      "timestamp": "2024-09-10T12:00:00Z",
      "is_active": true,
      "search_volume": 500000,
      "increase_percentage": 2500,
      "categories": ["Technology"],
      "serpapi_link": "https://serpapi.com/..."
    }
  ]
}
```

---

### 7. Google Trends Autocomplete
```
GET https://serpapi.com/search.json
  ?engine=google_trends_autocomplete
  &q=keyword
  &api_key=xxx
```

**Respuesta:**
```json
{
  "suggestions": [
    {
      "q": "keyword gaming",
      "title": "Keyword Gaming",
      "type": "topic",
      "serpapi_link": "https://serpapi.com/...",
      "google_trends_link": "https://trends.google.com/..."
    }
  ]
}
```

---

### 8. Google Trends News
```
GET https://serpapi.com/search.json
  ?engine=google_trends_news
  &q=keyword
  &geo=ES
  &api_key=xxx
```

**Respuesta:**
```json
{
  "news_results": [
    {
      "title": "Keyword Launches New Product",
      "link": "https://example.com/...",
      "source": "TechCrunch",
      "date": "2 hours ago",
      "thumbnail": "https://..."
    }
  ]
}
```

---

### 9. Google Related Questions (Expandir PAA)
```
GET https://serpapi.com/search.json
  ?engine=google_related_questions
  &next_page_token=TOKEN_FROM_PAA
  &api_key=xxx
```

**Uso:** Cuando obtienes el PAA inicial del SERP, cada pregunta tiene un `serpapi_link` con un `next_page_token`. Usar ese token con esta API simula hacer clic en la pregunta para cargar más preguntas relacionadas.

**Respuesta:**
```json
{
  "related_questions": [
    {
      "question": "¿Qué es mejor X o Y?",
      "snippet": "Según expertos...",
      "title": "Comparativa X vs Y",
      "link": "https://example.com/...",
      "source": {
        "name": "TechReview",
        "link": "https://techreview.com"
      },
      "serpapi_link": "https://serpapi.com/search.json?engine=google_related_questions&next_page_token=..."
    }
  ],
  "search_metadata": {
    "status": "Success",
    "total_time_taken": 0.45
  }
}
```

**Estrategia de expansión recursiva:**
1. Obtener PAA inicial con `engine=google`
2. Por cada pregunta, extraer `next_page_token` de `serpapi_link`
3. Llamar a `engine=google_related_questions` con ese token
4. Repetir hasta alcanzar profundidad o cantidad deseada

---

### 10. Google News (Búsqueda de noticias)
```
GET https://serpapi.com/search.json
  ?engine=google_news
  &q=keyword
  &gl=es
  &hl=es
  &api_key=xxx
```

**Parámetros opcionales:**
- `topic_token`: Para categorías específicas (Technology, Business, etc.)
- `publication_token`: Para noticias de un medio específico
- `kgmid`: ID del Knowledge Graph para entidades
- `section_token`: Para secciones específicas dentro de topics

**Topic tokens disponibles:**
| Topic | Token |
|-------|-------|
| Technology | `CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnpHZ0pGVXlnQVAB` |
| Business | `CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnpHZ0pGVXlnQVAB` |
| Science | `CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnpHZ0pGVXlnQVAB` |
| Entertainment | `CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnpHZ0pGVXlnQVAB` |
| Sports | `CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnpHZ0pGVXlnQVAB` |
| Health | `CAAqJggKIiBDQkFTRWdvSUwyMHZNR3QwTlRFU0FtVnpHZ0pGVXlnQVAB` |

**Respuesta:**
```json
{
  "news_results": [
    {
      "position": 1,
      "title": "NVIDIA Launches New RTX 5090",
      "link": "https://example.com/...",
      "source": {
        "name": "TechCrunch",
        "icon": "https://..."
      },
      "date": "2 hours ago",
      "thumbnail": "https://...",
      "snippet": "NVIDIA announced today..."
    }
  ]
}
```

**Casos de uso:**
- `q=NVIDIA` → Noticias sobre NVIDIA
- `topic_token=...` → Noticias de categoría Tecnología
- Sin params → Titulares principales (homepage)

---

## Parámetros Comunes

| Parámetro | Descripción | Valores |
|-----------|-------------|---------|
| `engine` | Motor de búsqueda | `google_trends`, `google_trends_trending_now`, etc. |
| `q` | Keyword(s) | String o comma-separated |
| `data_type` | Tipo de datos | `TIMESERIES`, `GEO_MAP`, `GEO_MAP_0`, `RELATED_QUERIES`, `RELATED_TOPICS` |
| `geo` | Código de país | `ES`, `PT`, `FR`, `IT`, `DE`, `US`, etc. |
| `date` | Rango temporal | `now 1-H`, `now 7-d`, `today 1-m`, `today 12-m`, `today 5-y` |
| `cat` | Categoría | `0` (todas), `5` (tecnología), `78` (electrónica), etc. |
| `hl` | Idioma | `es`, `en`, `pt`, `fr`, `it`, `de` |

---

## Categorías Útiles para Hardware/Tech

| ID | Categoría |
|----|-----------|
| 0 | Todas las categorías |
| 5 | Informática y electrónica |
| 78 | Electrónica de consumo |
| 18 | Compras |
| 13 | Internet y telecomunicaciones |
| 30 | Videojuegos |

---

## Notas

- **Breakout**: Cuando `extracted_value` es `"Breakout"`, indica crecimiento >5000%
- **Values**: El índice 0-100 es relativo al punto máximo en el período seleccionado
- **Rate Limits**: SerpAPI tiene límites según tu plan (100-30,000 búsquedas/mes)
