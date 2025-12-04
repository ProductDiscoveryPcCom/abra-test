"""
Google News Module
Obtiene noticias de Google News usando SerpAPI

APIs utilizadas:
- Google News: engine=google_news
- Google Trends News: engine=google_trends_news (noticias de tendencias)
"""

import requests
from typing import Optional, List
from datetime import datetime
import streamlit as st


class GoogleNewsModule:
    """Módulo para obtener noticias de Google News via SerpAPI"""

    BASE_URL = "https://serpapi.com/search.json"

    # Topic tokens predefinidos para categorías
    TOPIC_TOKENS = {
        "technology": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGRqTVhZU0FtVnpHZ0pGVXlnQVAB",
        "business": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnpHZ0pGVXlnQVAB",
        "science": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp0Y1RjU0FtVnpHZ0pGVXlnQVAB",
        "entertainment": "CAAqJggKIiBDQkFTRWdvSUwyMHZNREpxYW5RU0FtVnpHZ0pGVXlnQVAB",
        "sports": "CAAqJggKIiBDQkFTRWdvSUwyMHZNRFp1ZEdvU0FtVnpHZ0pGVXlnQVAB",
        "health": "CAAqJggKIiBDQkFTRWdvSUwyMHZNR3QwTlRFU0FtVnpHZ0pGVXlnQVAB"
    }

    # Idiomas por país
    LANGUAGES = {
        "ES": "es",
        "PT": "pt",
        "FR": "fr",
        "IT": "it",
        "DE": "de",
        "US": "en",
        "GB": "en"
    }

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search_news(
        self,
        query: str,
        country: str = "ES",
        language: str = None,
        filter_relevance: bool = True
    ) -> dict:
        """
        Busca noticias por término/marca
        Usa: engine=google_news con parámetro q

        Args:
            query: Término de búsqueda (ej: "Beelink", "NVIDIA RTX")
            country: Código de país
            language: Idioma (si no se especifica, se deduce del país)
            filter_relevance: Si debe filtrar noticias que no contengan la marca

        Returns:
            dict con noticias incluyendo:
            - title, link, source, date, thumbnail
            - snippet (resumen)
        """
        lang = language or self.LANGUAGES.get(country, "es")

        # Usar comillas para búsqueda exacta
        search_query = f'"{query}"' if " " in query and not query.startswith('"') else query

        params = {
            "engine": "google_news",
            "q": search_query,
            "gl": country.lower(),
            "hl": lang,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Procesar resultados
            news_results = data.get("news_results", [])
            processed_news = self._process_news_results(news_results)

            # Filtrar por relevancia si está habilitado
            if filter_relevance and processed_news:
                processed_news = self._filter_relevant_news(processed_news, query)

            return {
                "success": True,
                "news": processed_news,
                "total_count": len(processed_news),
                "query": query,
                "query_used": search_query,
                "country": country,
                "filtered": filter_relevance
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "news": []
            }

    def _filter_relevant_news(self, news: list, brand: str) -> list:
        """
        Filtra noticias para mantener solo las relevantes a la marca.

        Args:
            news: Lista de noticias
            brand: Nombre de la marca

        Returns:
            Lista filtrada de noticias relevantes
        """
        if not news or not brand:
            return news

        brand_lower = brand.lower().strip()
        brand_words = set(brand_lower.split())

        # Palabras que podrían causar falsos positivos
        # (ej: "Attack Shark" no debe coincidir con "shark attack")
        word_order_matters = len(brand_words) >= 2

        relevant = []

        for item in news:
            title = item.get("title", "").lower()
            snippet = item.get("snippet", "").lower()
            combined_text = f"{title} {snippet}"

            # Verificar si contiene la marca exacta
            if brand_lower in combined_text:
                # Si el orden importa, verificar que aparezcan juntas
                if word_order_matters:
                    # Buscar la secuencia exacta de palabras
                    if brand_lower in combined_text:
                        relevant.append(item)
                else:
                    relevant.append(item)
            else:
                # Verificar si contiene todas las palabras de la marca
                if brand_words and all(word in combined_text for word in brand_words):
                    # Solo incluir si las palabras aparecen cerca
                    if self._words_are_close(combined_text, brand_words):
                        relevant.append(item)

        # Si no hay resultados relevantes, devolver los originales con advertencia
        if not relevant and news:
            # Marcar como posiblemente no relevantes
            for item in news:
                item["relevance_warning"] = True
            return news[:3]  # Devolver solo 3 con advertencia

        return relevant

    def _words_are_close(self, text: str, words: set, max_distance: int = 10) -> bool:
        """
        Verifica si las palabras aparecen cerca una de otra en el texto.

        Returns:
            True si las palabras están a menos de max_distance palabras de distancia
        """
        text_words = text.split()

        positions = {}
        for i, word in enumerate(text_words):
            if word in words:
                if word not in positions:
                    positions[word] = []
                positions[word].append(i)

        # Si no encontramos todas las palabras, no están cerca
        if len(positions) < len(words):
            return False

        # Verificar distancia mínima entre la primera y última palabra
        all_positions = []
        for pos_list in positions.values():
            all_positions.extend(pos_list)

        if not all_positions:
            return False

        min_pos = min(all_positions)
        max_pos = max(all_positions)

        return (max_pos - min_pos) <= max_distance

    def get_topic_news(
        self,
        topic: str = "technology",
        country: str = "ES",
        language: str = None
    ) -> dict:
        """
        Obtiene noticias de un tema/categoría específica
        Usa: engine=google_news con topic_token

        Args:
            topic: Tema (technology, business, science, entertainment, sports, health)
            country: Código de país

        Returns:
            dict con noticias del tema
        """
        topic_token = self.TOPIC_TOKENS.get(topic.lower())

        if not topic_token:
            return {
                "success": False,
                "error": f"Topic '{topic}' no reconocido. Usa: {list(self.TOPIC_TOKENS.keys())}",
                "news": []
            }

        lang = language or self.LANGUAGES.get(country, "es")

        params = {
            "engine": "google_news",
            "topic_token": topic_token,
            "gl": country.lower(),
            "hl": lang,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            news_results = data.get("news_results", [])
            processed_news = self._process_news_results(news_results)

            return {
                "success": True,
                "news": processed_news,
                "total_count": len(processed_news),
                "topic": topic,
                "country": country
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "news": []
            }

    def get_headlines(
        self,
        country: str = "ES",
        language: str = None
    ) -> dict:
        """
        Obtiene los titulares principales de Google News
        Usa: engine=google_news sin query ni topic (homepage)

        Returns:
            dict con titulares principales
        """
        lang = language or self.LANGUAGES.get(country, "es")

        params = {
            "engine": "google_news",
            "gl": country.lower(),
            "hl": lang,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            news_results = data.get("news_results", [])
            processed_news = self._process_news_results(news_results)

            return {
                "success": True,
                "headlines": processed_news,
                "total_count": len(processed_news),
                "country": country
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "headlines": []
            }

    def get_entity_news(
        self,
        kgmid: str,
        country: str = "ES",
        language: str = None
    ) -> dict:
        """
        Obtiene noticias de una entidad específica usando Knowledge Graph ID

        Args:
            kgmid: ID del Knowledge Graph (ej: "/m/0k8z" para gaming)
                   Puedes obtenerlo del Knowledge Graph de Google

        Returns:
            dict con noticias de la entidad
        """
        lang = language or self.LANGUAGES.get(country, "es")

        params = {
            "engine": "google_news",
            "kgmid": kgmid,
            "gl": country.lower(),
            "hl": lang,
            "api_key": self.api_key
        }

        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            news_results = data.get("news_results", [])
            processed_news = self._process_news_results(news_results)

            return {
                "success": True,
                "news": processed_news,
                "total_count": len(processed_news),
                "kgmid": kgmid,
                "country": country
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "news": []
            }

    def get_brand_mentions(
        self,
        brand: str,
        country: str = "ES",
        include_competitors: List[str] = None
    ) -> dict:
        """
        Obtiene menciones de una marca en noticias
        Útil para product discovery - ver qué se dice de la marca

        Args:
            brand: Nombre de la marca
            include_competitors: Lista de competidores para comparar cobertura

        Returns:
            dict con noticias de la marca y métricas
        """
        # Buscar noticias de la marca
        brand_news = self.search_news(brand, country)

        result = {
            "success": brand_news.get("success", False),
            "brand": brand,
            "brand_news": brand_news.get("news", []),
            "brand_count": len(brand_news.get("news", [])),
            "competitors": {}
        }

        # Si hay competidores, buscar también
        if include_competitors:
            for competitor in include_competitors[:3]:  # Limitar a 3 para no gastar muchas llamadas
                comp_news = self.search_news(competitor, country)
                result["competitors"][competitor] = {
                    "news": comp_news.get("news", [])[:5],  # Solo top 5
                    "count": len(comp_news.get("news", []))
                }

        return result

    def _process_news_results(self, news_results: list) -> list:
        """
        Procesa y normaliza los resultados de noticias
        """
        processed = []

        for item in news_results:
            # Manejar diferentes estructuras de respuesta
            if "stories" in item:
                # Es un bloque de historias relacionadas
                for story in item.get("stories", []):
                    processed.append(self._extract_news_item(story))
            else:
                processed.append(self._extract_news_item(item))

        return processed

    def _extract_news_item(self, item: dict) -> dict:
        """
        Extrae campos normalizados de un item de noticia
        """
        # Obtener source
        source_info = item.get("source", {})
        if isinstance(source_info, dict):
            source_name = source_info.get("name", "")
            source_icon = source_info.get("icon", "")
        else:
            source_name = str(source_info)
            source_icon = ""

        return {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "source": source_name,
            "source_icon": source_icon,
            "date": item.get("date", ""),
            "thumbnail": item.get("thumbnail", ""),
            "highlight": item.get("highlight", {})
        }

    def analyze_news_sentiment(
        self,
        news: list,
        keywords_positive: List[str] = None,
        keywords_negative: List[str] = None
    ) -> dict:
        """
        Análisis básico de sentimiento basado en keywords en títulos

        Returns:
            dict con conteo de noticias positivas/negativas/neutrales
        """
        if keywords_positive is None:
            keywords_positive = [
                "éxito", "crecimiento", "lanzamiento", "innovación", "mejor",
                "récord", "gana", "lidera", "nuevo", "revoluciona",
                "success", "growth", "launch", "innovation", "best",
                "record", "wins", "leads", "new", "revolutionary"
            ]

        if keywords_negative is None:
            keywords_negative = [
                "problema", "fallo", "error", "crisis", "pérdida",
                "demanda", "retira", "cierra", "cae", "fracaso",
                "problem", "failure", "error", "crisis", "loss",
                "lawsuit", "recall", "closes", "falls", "fails"
            ]

        positive = 0
        negative = 0
        neutral = 0

        for item in news:
            title = item.get("title", "").lower()
            snippet = item.get("snippet", "").lower()
            text = f"{title} {snippet}"

            has_positive = any(kw in text for kw in keywords_positive)
            has_negative = any(kw in text for kw in keywords_negative)

            if has_positive and not has_negative:
                positive += 1
            elif has_negative and not has_positive:
                negative += 1
            else:
                neutral += 1

        total = len(news) if news else 1

        return {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "positive_pct": round(positive / total * 100, 1),
            "negative_pct": round(negative / total * 100, 1),
            "neutral_pct": round(neutral / total * 100, 1),
            "sentiment_score": round((positive - negative) / total * 100, 1)
        }


def test_module():
    """Test básico del módulo"""
    api_key = st.secrets.get("SERPAPI_KEY", "")
    if not api_key:
        print("No API key found")
        return

    module = GoogleNewsModule(api_key)

    # Test búsqueda
    result = module.search_news("NVIDIA", "ES")
    print(f"Search success: {result['success']}")
    print(f"News count: {result.get('total_count', 0)}")

    # Test topic
    tech_news = module.get_topic_news("technology", "ES")
    print(f"Tech news count: {tech_news.get('total_count', 0)}")


if __name__ == "__main__":
    test_module()

