"""
=============================================================================
AI PRODUCT DETECTION - Detección de Productos por IA (Opcional)
=============================================================================

Este módulo proporciona detección de productos usando modelos de IA
como capa adicional sobre los patrones regex.

CUÁNDO USAR:
- Cuando los patrones estructurales no son suficientes
- Para validar productos detectados por regex
- Para enriquecer con categoría/marca
- Para productos muy nuevos o nichos específicos

COSTO:
- Requiere API calls (OpenAI, Claude, etc.)
- ~0.01-0.05 USD por análisis
- Recomendado solo para productos con alto hype score

USO:
    from patterns.ai_detection import extract_products_with_ai
    
    products = extract_products_with_ai(
        text="Review del nuevo XYZTech SuperBox Pro",
        provider="openai",  # o "claude"
        validate_regex=True  # Validar con regex primero
    )

ÚLTIMA ACTUALIZACIÓN: 2024-12
=============================================================================
"""

import os
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

# Intentar importar clientes de IA
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class AIDetectedProduct:
    """Producto detectado por IA"""
    name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    category: Optional[str] = None
    confidence: float = 0.0
    reasoning: str = ""


# Prompt para extracción de productos
EXTRACTION_PROMPT = """Analiza el siguiente texto y extrae TODOS los productos tecnológicos mencionados.

Para cada producto, proporciona:
- name: Nombre completo del producto (ej: "Minisforum UM790 Pro")
- brand: Marca (ej: "Minisforum")  
- model: Modelo (ej: "UM790 Pro")
- category: Categoría (gpu/cpu/mini_pc/laptop/smartphone/console/peripheral/storage/monitor/audio/other)
- confidence: 0.0-1.0 qué tan seguro estás
- reasoning: Por qué crees que es un producto

IMPORTANTE:
- Solo productos tecnológicos (hardware, dispositivos, componentes)
- NO incluyas: servicios, software, marcas sin modelo específico
- Si no hay productos, retorna lista vacía

Retorna JSON válido con esta estructura:
{
    "products": [
        {
            "name": "...",
            "brand": "...",
            "model": "...",
            "category": "...",
            "confidence": 0.0,
            "reasoning": "..."
        }
    ]
}

TEXTO A ANALIZAR:
"""


def extract_products_with_openai(
    text: str,
    model: str = "gpt-4o-mini",
    max_tokens: int = 1000
) -> List[AIDetectedProduct]:
    """
    Extrae productos usando OpenAI API
    
    Args:
        text: Texto a analizar
        model: Modelo de OpenAI a usar
        max_tokens: Máximo de tokens en respuesta
    
    Returns:
        Lista de AIDetectedProduct
    """
    if not OPENAI_AVAILABLE:
        raise ImportError("openai package not installed. Run: pip install openai")
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Eres un experto en productos tecnológicos y hardware."},
                {"role": "user", "content": EXTRACTION_PROMPT + text}
            ],
            max_tokens=max_tokens,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        products = []
        for p in data.get("products", []):
            products.append(AIDetectedProduct(
                name=p.get("name", ""),
                brand=p.get("brand"),
                model=p.get("model"),
                category=p.get("category"),
                confidence=float(p.get("confidence", 0.5)),
                reasoning=p.get("reasoning", "")
            ))
        
        return products
        
    except Exception as e:
        print(f"Error en OpenAI API: {e}")
        return []


def extract_products_with_claude(
    text: str,
    model: str = "claude-3-haiku-20240307",
    max_tokens: int = 1000
) -> List[AIDetectedProduct]:
    """
    Extrae productos usando Claude API
    
    Args:
        text: Texto a analizar
        model: Modelo de Claude a usar
        max_tokens: Máximo de tokens en respuesta
    
    Returns:
        Lista de AIDetectedProduct
    """
    if not ANTHROPIC_AVAILABLE:
        raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": EXTRACTION_PROMPT + text}
            ]
        )
        
        content = response.content[0].text
        
        # Extraer JSON de la respuesta
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if not json_match:
            return []
        
        data = json.loads(json_match.group())
        
        products = []
        for p in data.get("products", []):
            products.append(AIDetectedProduct(
                name=p.get("name", ""),
                brand=p.get("brand"),
                model=p.get("model"),
                category=p.get("category"),
                confidence=float(p.get("confidence", 0.5)),
                reasoning=p.get("reasoning", "")
            ))
        
        return products
        
    except Exception as e:
        print(f"Error en Claude API: {e}")
        return []


def extract_products_with_ai(
    text: str,
    provider: str = "openai",
    validate_with_regex: bool = True,
    **kwargs
) -> List[AIDetectedProduct]:
    """
    Extrae productos usando IA con el proveedor especificado.
    
    Args:
        text: Texto a analizar
        provider: "openai" o "claude"
        validate_with_regex: Si validar primero con regex
        **kwargs: Argumentos adicionales para el proveedor
    
    Returns:
        Lista de AIDetectedProduct
    """
    # Validar primero con regex si se solicita
    if validate_with_regex:
        try:
            from patterns import extract_products
            regex_products = extract_products(text, use_structural=True)
            
            # Si regex ya encontró productos con alta confianza, no usar IA
            high_confidence = [p for p in regex_products if p.confidence >= 0.9]
            if len(high_confidence) >= 3:
                # Convertir a AIDetectedProduct para compatibilidad
                return [
                    AIDetectedProduct(
                        name=p.name,
                        category=p.category.value if hasattr(p.category, 'value') else str(p.category),
                        confidence=p.confidence,
                        reasoning="Detected by regex patterns"
                    )
                    for p in regex_products
                ]
        except ImportError:
            pass
    
    # Usar IA
    if provider == "openai":
        return extract_products_with_openai(text, **kwargs)
    elif provider == "claude":
        return extract_products_with_claude(text, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'openai' or 'claude'")


# =============================================================================
# UTILIDADES
# =============================================================================

def estimate_cost(
    num_texts: int,
    avg_chars_per_text: int = 500,
    provider: str = "openai",
    model: str = None
) -> Dict[str, float]:
    """
    Estima el costo de usar detección por IA
    
    Args:
        num_texts: Número de textos a analizar
        avg_chars_per_text: Caracteres promedio por texto
        provider: "openai" o "claude"
        model: Modelo específico (usa default si None)
    
    Returns:
        Dict con estimaciones de costo
    """
    # Estimaciones de tokens (1 token ≈ 4 caracteres)
    input_tokens_per_text = (len(EXTRACTION_PROMPT) + avg_chars_per_text) / 4
    output_tokens_per_text = 200  # Estimado
    
    # Precios por 1M tokens (diciembre 2024)
    prices = {
        "openai": {
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4o": {"input": 2.50, "output": 10.00},
        },
        "claude": {
            "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
            "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
        }
    }
    
    if model is None:
        model = "gpt-4o-mini" if provider == "openai" else "claude-3-haiku-20240307"
    
    if provider not in prices or model not in prices[provider]:
        return {"error": "Unknown provider/model"}
    
    price = prices[provider][model]
    
    total_input_tokens = input_tokens_per_text * num_texts
    total_output_tokens = output_tokens_per_text * num_texts
    
    input_cost = (total_input_tokens / 1_000_000) * price["input"]
    output_cost = (total_output_tokens / 1_000_000) * price["output"]
    
    return {
        "provider": provider,
        "model": model,
        "num_texts": num_texts,
        "estimated_input_tokens": int(total_input_tokens),
        "estimated_output_tokens": int(total_output_tokens),
        "input_cost_usd": round(input_cost, 4),
        "output_cost_usd": round(output_cost, 4),
        "total_cost_usd": round(input_cost + output_cost, 4),
        "cost_per_text_usd": round((input_cost + output_cost) / num_texts, 6)
    }


# =============================================================================
# EJEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Ejemplo de estimación de costo
    estimate = estimate_cost(100, provider="openai")
    print("Estimación de costo para 100 textos:")
    print(json.dumps(estimate, indent=2))
    
    # Ejemplo de extracción (requiere API key)
    # products = extract_products_with_ai(
    #     "Review del Minisforum UM790 Pro vs GMKtec NucBox K8",
    #     provider="openai"
    # )
    # for p in products:
    #     print(f"- {p.name} ({p.category}): {p.confidence:.0%}")
