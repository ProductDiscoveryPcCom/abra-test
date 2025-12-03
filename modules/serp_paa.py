"""
People Also Ask & AutoComplete Module
Obtiene preguntas y sugerencias de búsqueda usando SerpAPI

APIs utilizadas:
- Google SERP: engine=google (para PAA y related_searches)
- Google Autocomplete: engine=google_autocomplete (para sugerencias)
"""

import requests
from typing import Optional, List
import streamlit as st


class PeopleAlsoAskModule:
    """Módulo para obtener PAA, autocomplete y related searches"""
    
    BASE_URL = "https://serpapi.com/search.json"
    
    # Dominios de Google por país
    GOOGLE_DOMAINS = {
        "ES": "google.es",
        "PT": "google.pt",
        "FR": "google.fr",
        "IT": "google.it",
        "DE": "google.de"
    }
    
    # Idiomas por país
    LANGUAGES = {
        "ES": "es",
        "PT": "pt",
        "FR": "fr",
        "IT": "it",
        "DE": "de"
    }
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_serp_data(
        self,
        keyword: str,
        country: str = "ES",
        num_results: int = 10
    ) -> dict:
        """
        Obtiene datos completos de SERP incluyendo PAA y related searches
        Usa: engine=google
        """
        params = {
            "engine": "google",
            "q": keyword,
            "google_domain": self.GOOGLE_DOMAINS.get(country, "google.com"),
            "gl": country.lower(),
            "hl": self.LANGUAGES.get(country, "en"),
            "num": num_results,
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "people_also_ask": data.get("related_questions", []),
                "related_searches": data.get("related_searches", []),
                "organic_results": data.get("organic_results", []),
                "knowledge_graph": data.get("knowledge_graph", {}),
                "keyword": keyword,
                "country": country
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "people_also_ask": [],
                "related_searches": []
            }
    
    def get_autocomplete(
        self,
        keyword: str,
        country: str = "ES"
    ) -> dict:
        """
        Obtiene sugerencias de autocompletado de Google
        Usa: engine=google_autocomplete
        """
        params = {
            "engine": "google_autocomplete",
            "q": keyword,
            "gl": country.lower(),
            "hl": self.LANGUAGES.get(country, "en"),
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            suggestions = data.get("suggestions", [])
            
            return {
                "success": True,
                "suggestions": [s.get("value", "") for s in suggestions],
                "raw_suggestions": suggestions,
                "keyword": keyword,
                "country": country
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "suggestions": []
            }
    
    def expand_related_questions(
        self,
        next_page_token: str
    ) -> dict:
        """
        Expande el bloque "People Also Ask" para obtener más preguntas
        Usa: engine=google_related_questions
        
        Simula el clic en una pregunta del PAA para cargar más preguntas relacionadas.
        
        Args:
            next_page_token: Token obtenido de una pregunta del PAA inicial
                            (viene en el campo 'serpapi_link' de cada pregunta)
        
        Returns:
            dict con más preguntas relacionadas
        """
        params = {
            "engine": "google_related_questions",
            "next_page_token": next_page_token,
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "related_questions": data.get("related_questions", []),
                "search_metadata": data.get("search_metadata", {})
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "related_questions": []
            }
    
    def get_expanded_questions(
        self,
        keyword: str,
        country: str = "ES",
        max_depth: int = 2,
        max_questions: int = 20
    ) -> dict:
        """
        Obtiene preguntas PAA expandidas recursivamente
        
        Primero obtiene las preguntas iniciales, luego expande cada una
        para obtener más preguntas relacionadas.
        
        Args:
            keyword: Término de búsqueda
            country: Código de país
            max_depth: Profundidad máxima de expansión (1-3 recomendado)
            max_questions: Número máximo de preguntas a recolectar
        
        Returns:
            dict con todas las preguntas recolectadas
        """
        all_questions = []
        seen_questions = set()
        tokens_to_process = []
        
        # 1. Obtener PAA inicial
        serp_data = self.get_serp_data(keyword, country)
        
        if not serp_data.get("success"):
            return {
                "success": False,
                "error": serp_data.get("error", "Error obteniendo SERP"),
                "questions": []
            }
        
        initial_questions = serp_data.get("people_also_ask", [])
        
        for q in initial_questions:
            question_text = q.get("question", "")
            if question_text and question_text not in seen_questions:
                seen_questions.add(question_text)
                all_questions.append({
                    "question": question_text,
                    "snippet": q.get("snippet", ""),
                    "source": q.get("source", {}).get("name", ""),
                    "link": q.get("link", ""),
                    "depth": 0
                })
                
                # Guardar token para expansión
                serpapi_link = q.get("serpapi_link", "")
                if serpapi_link and max_depth > 0:
                    # Extraer token del link
                    if "next_page_token=" in serpapi_link:
                        token = serpapi_link.split("next_page_token=")[-1].split("&")[0]
                        tokens_to_process.append((token, 1))
        
        # 2. Expandir preguntas recursivamente
        while tokens_to_process and len(all_questions) < max_questions:
            token, depth = tokens_to_process.pop(0)
            
            if depth > max_depth:
                continue
            
            expanded = self.expand_related_questions(token)
            
            if expanded.get("success"):
                for q in expanded.get("related_questions", []):
                    if len(all_questions) >= max_questions:
                        break
                    
                    question_text = q.get("question", "")
                    if question_text and question_text not in seen_questions:
                        seen_questions.add(question_text)
                        all_questions.append({
                            "question": question_text,
                            "snippet": q.get("snippet", ""),
                            "source": q.get("source", {}).get("name", ""),
                            "link": q.get("link", ""),
                            "depth": depth
                        })
                        
                        # Añadir token para siguiente nivel
                        serpapi_link = q.get("serpapi_link", "")
                        if serpapi_link and depth < max_depth:
                            if "next_page_token=" in serpapi_link:
                                next_token = serpapi_link.split("next_page_token=")[-1].split("&")[0]
                                tokens_to_process.append((next_token, depth + 1))
        
        return {
            "success": True,
            "questions": all_questions,
            "total_count": len(all_questions),
            "keyword": keyword,
            "country": country
        }
    
    def get_questions(
        self,
        keyword: str,
        country: str = "ES"
    ) -> List[dict]:
        """
        Extrae solo las preguntas de PAA con formato limpio
        """
        serp_data = self.get_serp_data(keyword, country)
        
        questions = []
        if serp_data["success"]:
            for item in serp_data.get("people_also_ask", []):
                questions.append({
                    "question": item.get("question", ""),
                    "snippet": item.get("snippet", ""),
                    "source": item.get("source", {}).get("name", ""),
                    "link": item.get("link", "")
                })
        
        return questions
    
    def categorize_searches(
        self,
        keyword: str,
        country: str = "ES"
    ) -> dict:
        """
        Categoriza las búsquedas relacionadas en:
        - Preguntas (contienen ?, qué, cómo, cuál, etc.)
        - Comparativas (vs, mejor, comparar)
        - Productos (modelo específico, número)
        - Marcas (otras marcas mencionadas)
        - Otros
        """
        autocomplete = self.get_autocomplete(keyword, country)
        serp_data = self.get_serp_data(keyword, country)
        
        # Combinar todas las sugerencias
        all_searches = autocomplete.get("suggestions", [])
        for item in serp_data.get("related_searches", []):
            query = item.get("query", "")
            if query and query not in all_searches:
                all_searches.append(query)
        
        # Palabras clave para categorización
        question_words = ["?", "qué", "que", "cómo", "como", "cuál", "cual", 
                         "dónde", "donde", "cuándo", "cuando", "por qué", "quién",
                         "what", "how", "which", "where", "when", "why", "who", "is", "are"]
        comparative_words = ["vs", "versus", "mejor", "mejor que", "comparar", 
                            "diferencia", "o ", "mejor", "peor", "comparison"]
        
        categorized = {
            "questions": [],
            "comparatives": [],
            "products": [],
            "brands": [],
            "others": [],
            "all": all_searches
        }
        
        for search in all_searches:
            search_lower = search.lower()
            
            # Es una pregunta?
            if any(word in search_lower for word in question_words):
                categorized["questions"].append(search)
            # Es una comparativa?
            elif any(word in search_lower for word in comparative_words):
                categorized["comparatives"].append(search)
            else:
                categorized["others"].append(search)
        
        return {
            "success": True,
            "categorized": categorized,
            "total_count": len(all_searches),
            "keyword": keyword
        }
    
    def get_brand_perception(
        self,
        brand: str,
        country: str = "ES"
    ) -> dict:
        """
        Analiza la percepción de marca basándose en las preguntas que hace la gente
        
        Busca patrones como:
        - "es [brand] bueno/malo"
        - "[brand] opiniones"
        - "[brand] problemas"
        """
        perception_queries = [
            f"{brand} opiniones",
            f"{brand} review",
            f"es {brand} bueno",
            f"{brand} problemas",
            f"{brand} calidad"
        ]
        
        perception_data = {
            "positive_signals": [],
            "negative_signals": [],
            "neutral_signals": [],
            "questions": []
        }
        
        # Obtener preguntas principales
        questions = self.get_questions(brand, country)
        perception_data["questions"] = questions
        
        # Obtener autocomplete para queries de percepción
        for query in perception_queries[:2]:  # Limitar llamadas API
            autocomplete = self.get_autocomplete(query, country)
            for suggestion in autocomplete.get("suggestions", []):
                suggestion_lower = suggestion.lower()
                
                positive_words = ["bueno", "mejor", "calidad", "recomendado", "good", "best", "quality"]
                negative_words = ["malo", "problema", "fallo", "error", "bad", "issue", "problem"]
                
                if any(word in suggestion_lower for word in positive_words):
                    perception_data["positive_signals"].append(suggestion)
                elif any(word in suggestion_lower for word in negative_words):
                    perception_data["negative_signals"].append(suggestion)
                else:
                    perception_data["neutral_signals"].append(suggestion)
        
        return {
            "success": True,
            "perception": perception_data,
            "brand": brand,
            "country": country
        }


def test_module():
    """Test básico del módulo"""
    api_key = st.secrets.get("SERPAPI_KEY", "")
    if not api_key:
        print("No API key found")
        return
    
    module = PeopleAlsoAskModule(api_key)
    
    # Test autocomplete
    result = module.get_autocomplete("arozzi", "ES")
    print(f"Autocomplete success: {result['success']}")
    print(f"Suggestions: {result['suggestions'][:5]}")
    
    # Test categorization
    cats = module.categorize_searches("arozzi", "ES")
    print(f"Total searches: {cats['total_count']}")
    print(f"Questions: {len(cats['categorized']['questions'])}")


if __name__ == "__main__":
    test_module()
