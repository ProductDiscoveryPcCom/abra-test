"""
Related Queries Module
Obtiene topics y queries relacionadas usando SerpAPI

APIs utilizadas:
- Related Queries: engine=google_trends, data_type=RELATED_QUERIES
- Related Topics: engine=google_trends, data_type=RELATED_TOPICS
"""

import requests
from typing import Optional
import streamlit as st


class RelatedQueriesModule:
    """Módulo para obtener queries y topics relacionados"""
    
    BASE_URL = "https://serpapi.com/search.json"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_related_queries(
        self,
        keyword: str,
        geo: str = "ES",
        timeframe: str = "today 12-m",
        category: int = 0
    ) -> dict:
        """
        Obtiene las búsquedas relacionadas (rising y top)
        Usa: engine=google_trends, data_type=RELATED_QUERIES
        
        Returns:
            dict con arrays 'rising' y 'top', cada elemento contiene:
            - query: texto de la consulta
            - value: porcentaje o 'Breakout'
            - extracted_value: valor numérico o 'Breakout'
            - link: enlace a Google Trends
        """
        params = {
            "engine": "google_trends",
            "q": keyword,
            "data_type": "RELATED_QUERIES",
            "geo": geo,
            "date": timeframe,
            "cat": category,
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            related = data.get("related_queries", {})
            
            return {
                "success": True,
                "rising": related.get("rising", []),
                "top": related.get("top", []),
                "keyword": keyword,
                "geo": geo
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "rising": [],
                "top": []
            }
    
    def get_related_topics(
        self,
        keyword: str,
        geo: str = "ES",
        timeframe: str = "today 12-m",
        category: int = 0
    ) -> dict:
        """
        Obtiene los topics relacionados (rising y top)
        Usa: engine=google_trends, data_type=RELATED_TOPICS
        
        Returns:
            dict con arrays 'rising' y 'top', cada elemento contiene:
            - topic: {mid (Freebase ID), title, type}
            - value: porcentaje o 'Breakout'
            - extracted_value: valor numérico o 'Breakout'
            - link: enlace a Google Trends
        """
        params = {
            "engine": "google_trends",
            "q": keyword,
            "data_type": "RELATED_TOPICS",
            "geo": geo,
            "date": timeframe,
            "cat": category,
            "api_key": self.api_key
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            related = data.get("related_topics", {})
            
            return {
                "success": True,
                "rising": related.get("rising", []),
                "top": related.get("top", []),
                "keyword": keyword,
                "geo": geo
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "rising": [],
                "top": []
            }
    
    def get_all_related(
        self,
        keyword: str,
        geo: str = "ES",
        timeframe: str = "today 12-m"
    ) -> dict:
        """
        Obtiene tanto queries como topics relacionados en una sola llamada
        """
        queries = self.get_related_queries(keyword, geo, timeframe)
        topics = self.get_related_topics(keyword, geo, timeframe)
        
        return {
            "success": queries.get("success", False) or topics.get("success", False),
            "queries": {
                "rising": queries.get("rising", []),
                "top": queries.get("top", [])
            },
            "topics": {
                "rising": topics.get("rising", []),
                "top": topics.get("top", [])
            },
            "keyword": keyword,
            "geo": geo
        }
    
    def format_growth(self, item: dict) -> str:
        """
        Formatea el crecimiento de un item para mostrar
        """
        if "extracted_value" in item:
            value = item["extracted_value"]
            if value == "Breakout" or value > 5000:
                return "🚀 Breakout"
            else:
                return f"↗ +{value}%"
        elif "value" in item:
            return item["value"]
        return "↗ Rising"
    
    def filter_by_growth(
        self,
        items: list,
        min_growth: int = 0
    ) -> list:
        """
        Filtra items por crecimiento mínimo
        """
        filtered = []
        for item in items:
            if "extracted_value" in item:
                if item["extracted_value"] == "Breakout" or item["extracted_value"] >= min_growth:
                    filtered.append(item)
            else:
                filtered.append(item)
        return filtered
    
    def get_competitor_brands(
        self,
        keyword: str,
        geo: str = "ES"
    ) -> list:
        """
        Intenta identificar marcas competidoras desde los topics relacionados
        """
        topics = self.get_related_topics(keyword, geo)
        
        brands = []
        if topics["success"]:
            for topic in topics.get("rising", []) + topics.get("top", []):
                topic_type = topic.get("topic", {}).get("type", "")
                if topic_type in ["Brand", "Product", "Company"]:
                    brands.append({
                        "name": topic.get("topic", {}).get("title", ""),
                        "type": topic_type,
                        "growth": self.format_growth(topic)
                    })
        
        return brands


def test_module():
    """Test básico del módulo"""
    api_key = st.secrets.get("SERPAPI_KEY", "")
    if not api_key:
        print("No API key found")
        return
    
    module = RelatedQueriesModule(api_key)
    result = module.get_all_related("arozzi")
    print(f"Success: {result['success']}")
    print(f"Rising queries: {len(result['queries']['rising'])}")
    print(f"Rising topics: {len(result['topics']['rising'])}")


if __name__ == "__main__":
    test_module()
