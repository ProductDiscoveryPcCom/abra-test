#!/usr/bin/env python3
"""
Test de verificación de YouTube API
Ejecutar: python tests/test_youtube_api.py

Este script verifica:
1. Conexión a la API de YouTube
2. Correcta estructura de respuestas
3. Parsing de datos
4. Flujo completo
"""

import os
import sys
import json

# Añadir path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_ok(msg):
    print(f"{Colors.GREEN}✓{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.END} {msg}")

def print_warn(msg):
    print(f"{Colors.YELLOW}⚠{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.END} {msg}")


def test_youtube_endpoints():
    """Verifica que los endpoints de YouTube son correctos"""
    print("\n" + "="*60)
    print("TEST 1: Verificación de Endpoints")
    print("="*60)

    endpoints = {
        "Search": "https://www.googleapis.com/youtube/v3/search",
        "Videos": "https://www.googleapis.com/youtube/v3/videos",
        "Channels": "https://www.googleapis.com/youtube/v3/channels"
    }

    for name, url in endpoints.items():
        try:
            # Solo verificar que el endpoint existe (sin API key dará 400, no 404)
            response = requests.get(url, timeout=5)
            if response.status_code in [400, 403]:
                # 400 = falta API key, 403 = API key inválida
                # Ambos significan que el endpoint es correcto
                print_ok(f"{name}: {url} - Endpoint válido")
            elif response.status_code == 404:
                print_error(f"{name}: {url} - Endpoint no encontrado")
            else:
                print_info(f"{name}: {url} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print_error(f"{name}: Error de conexión - {str(e)}")


def test_api_key_format():
    """Verifica el formato de API key esperado"""
    print("\n" + "="*60)
    print("TEST 2: Formato de API Key")
    print("="*60)

    # API keys de YouTube tienen este formato
    example_formats = [
        "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # 39 chars
    ]

    print_info("Las API keys de YouTube Data API v3 tienen formato:")
    print_info("  - Empiezan con 'AIza'")
    print_info("  - Tienen ~39 caracteres")
    print_info("  - Solo letras, números y guiones bajos")
    print("")

    # Intentar cargar desde secrets.toml
    try:
        import streamlit as st
        api_key = st.secrets.get("YOUTUBE_API_KEY", "")
        if api_key:
            if api_key.startswith("AIza") and len(api_key) >= 35:
                print_ok(f"API key encontrada: {api_key[:10]}...{api_key[-4:]}")
            else:
                print_warn(f"API key tiene formato inusual: {api_key[:10]}...")
        else:
            print_warn("No se encontró YOUTUBE_API_KEY en secrets.toml")
    except Exception as e:
        print_warn(f"No se pudo leer secrets.toml: {e}")
        print_info("Para probar, configura: YOUTUBE_API_KEY='tu_api_key'")


def test_search_response_structure():
    """Verifica la estructura esperada de respuestas"""
    print("\n" + "="*60)
    print("TEST 3: Estructura de Respuestas Esperada")
    print("="*60)

    # Estructura esperada de Search API
    search_structure = {
        "kind": "youtube#searchListResponse",
        "etag": "string",
        "nextPageToken": "string (opcional)",
        "pageInfo": {
            "totalResults": "int",
            "resultsPerPage": "int"
        },
        "items": [
            {
                "kind": "youtube#searchResult",
                "id": {
                    "kind": "youtube#video",
                    "videoId": "string (11 chars)"
                },
                "snippet": {
                    "title": "string",
                    "description": "string",
                    "channelId": "string",
                    "channelTitle": "string",
                    "publishedAt": "ISO 8601 datetime",
                    "thumbnails": {
                        "default": {"url": "string", "width": "int", "height": "int"},
                        "medium": {"url": "string"},
                        "high": {"url": "string"}
                    }
                }
            }
        ]
    }

    print_info("Search API Response Structure:")
    print(json.dumps(search_structure, indent=2))

    # Estructura esperada de Videos API
    videos_structure = {
        "items": [
            {
                "id": "string (videoId)",
                "statistics": {
                    "viewCount": "string (número)",
                    "likeCount": "string (número)",
                    "commentCount": "string (número)"
                },
                "contentDetails": {
                    "duration": "ISO 8601 duration (PT1H2M3S)"
                }
            }
        ]
    }

    print("")
    print_info("Videos API Response Structure:")
    print(json.dumps(videos_structure, indent=2))

    print_ok("Estructuras documentadas correctamente")


def test_module_implementation():
    """Verifica la implementación del módulo"""
    print("\n" + "="*60)
    print("TEST 4: Implementación del Módulo")
    print("="*60)

    try:
        from modules.youtube import YouTubeModule, YouTubeVideo, YouTubeMetrics

        # Verificar clases
        print_ok("YouTubeModule importado correctamente")
        print_ok("YouTubeVideo dataclass disponible")
        print_ok("YouTubeMetrics dataclass disponible")

        # Verificar métodos principales
        module = YouTubeModule(api_key="test_key")

        methods = [
            "search_videos",
            "search_brand",
            "get_recent_videos",
            "calculate_metrics",
            "_search_video_ids",
            "_get_video_statistics",
            "_combine_data"
        ]

        for method in methods:
            if hasattr(module, method):
                print_ok(f"Método {method}() existe")
            else:
                print_error(f"Método {method}() NO existe")

        # Verificar URLs
        if module.SEARCH_URL == "https://www.googleapis.com/youtube/v3/search":
            print_ok("SEARCH_URL correcto")
        else:
            print_error(f"SEARCH_URL incorrecto: {module.SEARCH_URL}")

        if module.VIDEOS_URL == "https://www.googleapis.com/youtube/v3/videos":
            print_ok("VIDEOS_URL correcto")
        else:
            print_error(f"VIDEOS_URL incorrecto: {module.VIDEOS_URL}")

    except ImportError as e:
        print_error(f"Error importando módulo: {e}")


def test_data_flow():
    """Verifica el flujo de datos completo"""
    print("\n" + "="*60)
    print("TEST 5: Flujo de Datos")
    print("="*60)

    try:
        from modules.youtube import YouTubeModule, YouTubeVideo

        # Simular datos de respuesta
        mock_snippets = {
            "dQw4w9WgXcQ": {
                "title": "Test Video Title",
                "channelTitle": "Test Channel",
                "channelId": "UC12345",
                "publishedAt": "2024-01-15T10:30:00Z",
                "description": "Test description",
                "thumbnails": {
                    "high": {"url": "https://example.com/thumb.jpg"}
                }
            }
        }

        mock_stats = {
            "dQw4w9WgXcQ": {
                "statistics": {
                    "viewCount": "1000000",
                    "likeCount": "50000",
                    "commentCount": "1000"
                },
                "contentDetails": {
                    "duration": "PT3M45S"
                }
            }
        }

        # Probar combinación de datos
        module = YouTubeModule(api_key="test")
        videos = module._combine_data(
            video_ids=["dQw4w9WgXcQ"],
            snippets=mock_snippets,
            stats=mock_stats
        )

        if videos:
            v = videos[0]
            print_ok(f"Video creado: {v.title}")
            print_ok(f"Views parseados: {v.views} ({v.views_formatted})")
            print_ok(f"Duration parseado: {v.duration}")
            print_ok(f"Channel: {v.channel}")
            print_ok(f"Link: {v.link}")
            print_ok(f"Engagement rate: {v.engagement_rate:.2f}%")
        else:
            print_error("No se crearon videos")

    except Exception as e:
        print_error(f"Error en flujo de datos: {e}")


def test_live_api(api_key: str = None):
    """Prueba real contra la API (requiere API key)"""
    print("\n" + "="*60)
    print("TEST 6: Prueba Real de API")
    print("="*60)

    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("YOUTUBE_API_KEY", "")
        except Exception:
            pass

    if not api_key:
        print_warn("No hay API key disponible. Saltando prueba real.")
        print_info("Para probar: python tests/test_youtube_api.py YOUR_API_KEY")
        return

    print_info(f"Usando API key: {api_key[:10]}...{api_key[-4:]}")

    try:
        from modules.youtube import YouTubeModule

        module = YouTubeModule(api_key=api_key)

        # Prueba de búsqueda simple
        print_info("Buscando: 'Beelink mini pc'...")

        videos = module.search_videos(
            query="Beelink mini pc",
            max_results=5,
            order="relevance",
            region="ES"
        )

        if videos:
            print_ok(f"Se encontraron {len(videos)} videos")
            for i, v in enumerate(videos[:3], 1):
                print_info(f"  {i}. {v.title[:50]}... ({v.views_formatted} views)")
        else:
            error = module.get_last_error()
            if error:
                print_error(f"Error de API: {error}")
            else:
                print_warn("No se encontraron videos (puede ser normal)")

        # Prueba de búsqueda de marca completa
        print("")
        print_info("Búsqueda completa de marca: 'Beelink'...")

        videos_by_type = module.search_brand("Beelink", geo="ES")

        total = sum(len(v) for v in videos_by_type.values())
        print_ok(f"Total videos encontrados: {total}")
        for vtype, vlist in videos_by_type.items():
            print_info(f"  - {vtype}: {len(vlist)} videos")

        # Calcular métricas
        metrics = module.calculate_metrics("Beelink", videos_by_type)
        print_ok(f"Content Score: {metrics.content_score}/100")
        print_ok(f"Total Views: {metrics.total_views:,}")
        print_ok(f"Videos recientes (30d): {metrics.recent_videos_30d}")

    except Exception as e:
        print_error(f"Error en prueba real: {e}")
        import traceback
        traceback.print_exc()


def test_component_rendering():
    """Verifica que los componentes pueden renderizar los datos"""
    print("\n" + "="*60)
    print("TEST 7: Verificación de Componentes")
    print("="*60)

    try:
        from components.youtube_panel import render_youtube_panel, render_youtube_mini
        from modules.youtube import YouTubeVideo, YouTubeMetrics

        # Verificar imports
        print_ok("render_youtube_panel importado")
        print_ok("render_youtube_mini importado")

        # Verificar que las funciones aceptan los tipos correctos
        import inspect

        sig = inspect.signature(render_youtube_panel)
        params = list(sig.parameters.keys())

        if "keyword" in params and "videos_by_type" in params and "metrics" in params:
            print_ok("render_youtube_panel tiene parámetros correctos")
        else:
            print_error(f"Parámetros inesperados: {params}")

        # Verificar YouTubeVideo tiene los atributos que se usan en el render
        required_attrs = [
            "thumbnail", "title", "link", "views_formatted",
            "duration", "channel", "published"
        ]

        video = YouTubeVideo(
            video_id="test",
            title="Test",
            channel="Test Channel"
        )

        for attr in required_attrs:
            if hasattr(video, attr):
                print_ok(f"YouTubeVideo.{attr} existe")
            else:
                print_error(f"YouTubeVideo.{attr} NO existe")

    except Exception as e:
        print_error(f"Error verificando componentes: {e}")


def print_summary():
    """Imprime resumen y recomendaciones"""
    print("\n" + "="*60)
    print("RESUMEN Y RECOMENDACIONES")
    print("="*60)

    print("""
╔══════════════════════════════════════════════════════════════╗
║  YouTube Data API v3 - Checklist de Configuración            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Crear proyecto en Google Cloud Console                   ║
║     https://console.cloud.google.com                         ║
║                                                              ║
║  2. Habilitar YouTube Data API v3                            ║
║     APIs & Services > Library > YouTube Data API v3          ║
║                                                              ║
║  3. Crear API Key                                            ║
║     APIs & Services > Credentials > Create Credentials       ║
║                                                              ║
║  4. Configurar en secrets.toml:                              ║
║     YOUTUBE_API_KEY = "AIzaSy..."                            ║
║                                                              ║
║  5. Cuota diaria: 10,000 unidades                            ║
║     - Search = 100 unidades                                  ║
║     - Videos = 1 unidad                                      ║
║     - ~95 búsquedas completas/día                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    print("\n" + "🔍 YouTube API Verification Test")
    print("=" * 60)

    # Ejecutar tests
    test_youtube_endpoints()
    test_api_key_format()
    test_search_response_structure()
    test_module_implementation()
    test_data_flow()
    test_component_rendering()

    # Si se pasa API key como argumento
    if len(sys.argv) > 1:
        test_live_api(sys.argv[1])
    else:
        test_live_api()

    print_summary()

    print("\n✅ Verificación completada")
