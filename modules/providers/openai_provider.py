"""
OpenAI Provider
Integración con OpenAI GPT-4 API
"""

from typing import Optional
import json


class OpenAIProvider:
    """Proveedor de IA usando GPT-4 de OpenAI"""

    MODEL = "gpt-4-turbo-preview"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = None
        self._init_client()

    def _init_client(self):
        """Inicializa el cliente de OpenAI"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("Instala openai: pip install openai")

    def analyze_trend(self, trend_data: dict) -> dict:
        """
        Analiza los datos de tendencia y genera insights
        """
        prompt = self._build_analysis_prompt(trend_data)

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                max_tokens=1500,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analista de tendencias de mercado especializado en retail de tecnología. Proporcionas insights accionables y directos."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.choices[0].message.content

            return {
                "success": True,
                "analysis": content,
                "provider": "GPT-4"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "GPT-4"
            }

    def generate_blog_ideas(self, trend_data: dict, brand: str) -> dict:
        """
        Genera ideas para posts de blog basándose en los datos
        """
        prompt = f"""Basándote en estos datos de tendencia para "{brand}", genera 5 ideas de artículos para un blog de tecnología/hardware:

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

Responde SOLO con el JSON, sin texto adicional."""

        try:
            response = self.client.chat.completions.create(
                model=self.MODEL,
                max_tokens=1000,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "Respondes siempre en JSON válido."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            content = response.choices[0].message.content
            ideas = json.loads(content)

            return {
                "success": True,
                "ideas": ideas.get("ideas", []),
                "provider": "GPT-4"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "GPT-4"
            }

    def explain_seasonality(self, seasonality_data: dict, brand: str) -> str:
        """
        Genera una explicación del patrón de estacionalidad
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

            prompt = f"""En una sola frase, explica por qué "{brand}" podría tener más búsquedas en {month_names.get(peak_month, 'desconocido')} y menos en {month_names.get(low_month, 'desconocido')}.

Considera: Black Friday, Navidad, vuelta al cole, lanzamientos de productos, temporadas de gaming, etc.

Responde solo con la frase explicativa, sin introducción."""

            try:
                response = self.client.chat.completions.create(
                    model=self.MODEL,
                    max_tokens=200,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                return response.choices[0].message.content
            except Exception:
                return f"El interés en {brand} muestra un patrón estacional con picos en {month_names.get(peak_month, 'ciertos meses')}."

        return f"El interés en {brand} muestra variaciones estacionales."

    def _build_analysis_prompt(self, trend_data: dict) -> str:
        """Construye el prompt para análisis de tendencia"""
        return f"""Analiza estos datos de tendencia para product discovery en retail de tecnología:

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
1. Estado actual de la tendencia
2. Oportunidad para retail de tecnología (PCComponentes)
3. Recomendación accionable

Sé directo y orientado a la acción."""

    def is_available(self) -> bool:
        """Verifica si el proveedor está disponible"""
        return self.client is not None and self.api_key is not None

