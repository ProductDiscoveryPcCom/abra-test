"""
Perplexity Provider
Integración con Perplexity API
"""

from typing import Optional
import json
import requests


class PerplexityProvider:
    """Proveedor de IA usando Perplexity API"""
    
    BASE_URL = "https://api.perplexity.ai/chat/completions"
    MODEL = "llama-3.1-sonar-large-128k-online"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def analyze_trend(self, trend_data: dict) -> dict:
        """
        Analiza los datos de tendencia y genera insights
        Perplexity puede buscar info adicional en tiempo real
        """
        prompt = self._build_analysis_prompt(trend_data)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un analista de tendencias de mercado especializado en retail de tecnología. Proporcionas insights accionables basados en datos y búsquedas en tiempo real."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1500
            }
            
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            return {
                "success": True,
                "analysis": content,
                "provider": "Perplexity",
                "citations": data.get("citations", [])
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "Perplexity"
            }
    
    def generate_blog_ideas(self, trend_data: dict, brand: str) -> dict:
        """
        Genera ideas para posts de blog basándose en los datos
        Perplexity busca tendencias actuales para mejorar las sugerencias
        """
        prompt = f"""Basándote en estos datos de tendencia para "{brand}" y buscando información actual sobre esta marca/producto, genera 5 ideas de artículos para un blog de tecnología/hardware:

DATOS:
- Crecimiento: {trend_data.get('growth_rate', 0)}%
- Score de tendencia: {trend_data.get('trend_score', 0)}/100
- Preguntas frecuentes: {trend_data.get('questions', [])}
- Búsquedas relacionadas: {trend_data.get('related_queries', [])[:10]}

Genera exactamente 5 ideas de artículos en formato JSON:
{{
    "ideas": [
        {{
            "titulo": "...",
            "enfoque": "...",
            "keywords_objetivo": ["...", "..."]
        }}
    ]
}}

Responde SOLO con el JSON, sin texto adicional ni explicaciones."""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000
            }
            
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Intentar parsear JSON
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                ideas = json.loads(content.strip())
                return {
                    "success": True,
                    "ideas": ideas.get("ideas", []),
                    "provider": "Perplexity"
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "ideas": [],
                    "raw_response": content,
                    "provider": "Perplexity"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "Perplexity"
            }
    
    def explain_seasonality(self, seasonality_data: dict, brand: str) -> str:
        """
        Genera una explicación del patrón de estacionalidad
        Perplexity busca información contextual
        """
        monthly_pattern = seasonality_data.get("monthly_pattern", {})
        is_seasonal = seasonality_data.get("is_seasonal", False)
        
        if not is_seasonal:
            return f"El interés en {brand} es relativamente estable a lo largo del año, sin patrones estacionales marcados."
        
        if monthly_pattern:
            peak_month = max(monthly_pattern, key=monthly_pattern.get)
            low_month = min(monthly_pattern, key=monthly_pattern.get)
            
            month_names = {
                1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
                5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
                9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
            }
            
            prompt = f"""Busca información sobre "{brand}" y en una sola frase, explica por qué podría tener más búsquedas en {month_names.get(peak_month, 'desconocido')} y menos en {month_names.get(low_month, 'desconocido')}.

Considera: Black Friday, Navidad, vuelta al cole, lanzamientos de productos, temporadas de gaming, ferias de tecnología, etc.

Responde solo con la frase explicativa, sin introducción ni fuentes."""

            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.MODEL,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 200
                }
                
                response = requests.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except Exception:
                return f"El interés en {brand} muestra un patrón estacional con picos en {month_names.get(peak_month, 'ciertos meses')}."
        
        return f"El interés en {brand} muestra variaciones estacionales."
    
    def search_brand_context(self, brand: str) -> dict:
        """
        Busca contexto adicional sobre la marca usando Perplexity
        (ventaja única de Perplexity: búsqueda en tiempo real)
        """
        prompt = f"""Proporciona información actual y relevante sobre "{brand}" para retail de tecnología:
1. ¿Qué es y qué productos ofrece?
2. ¿Hay noticias o lanzamientos recientes?
3. ¿Cuál es su posicionamiento vs competidores?

Sé breve y directo (máximo 200 palabras)."""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500
            }
            
            response = requests.post(
                self.BASE_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "context": data["choices"][0]["message"]["content"],
                "citations": data.get("citations", []),
                "provider": "Perplexity"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "Perplexity"
            }
    
    def _build_analysis_prompt(self, trend_data: dict) -> str:
        """Construye el prompt para análisis de tendencia"""
        return f"""Analiza estos datos de tendencia para product discovery en retail de tecnología y busca información adicional actual sobre la marca:

MARCA/TÉRMINO: {trend_data.get('keyword', 'N/A')}

MÉTRICAS:
- Valor actual (índice 0-100): {trend_data.get('current_value', 'N/A')}
- Crecimiento reciente: {trend_data.get('growth_rate', 'N/A')}%
- Trend Score: {trend_data.get('trend_score', 'N/A')}/100
- Potential Score: {trend_data.get('potential_score', 'N/A')}/100
- Estacionalidad: {'Alta' if trend_data.get('is_seasonal') else 'Baja'}

QUERIES EN CRECIMIENTO:
{trend_data.get('rising_queries', [])}

PREGUNTAS DE USUARIOS:
{trend_data.get('questions', [])}

Genera un análisis ejecutivo breve (máximo 3 párrafos) que incluya:
1. Estado actual de la tendencia (con contexto de mercado actual)
2. Oportunidad para retail de tecnología (PCComponentes)
3. Recomendación accionable

Sé directo y orientado a la acción."""
    
    def is_available(self) -> bool:
        """Verifica si el proveedor está disponible"""
        return self.api_key is not None
