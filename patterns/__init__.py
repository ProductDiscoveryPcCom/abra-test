"""
=============================================================================
PATTERNS - Sistema de Detección de Productos e Intención de Compra
=============================================================================

ARQUITECTURA DE DETECCIÓN (3 NIVELES):

┌─────────────────────────────────────────────────────────────────────────┐
│  NIVEL 1: MARCAS CONOCIDAS                                              │
│  - Alta precisión (99%+)                                                │
│  - Baja cobertura (solo marcas listadas)                                │
│  - Ejemplos: "RTX 4090", "Ryzen 9 7950X", "Minisforum UM790"           │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  NIVEL 2: PATRONES ESTRUCTURALES GENÉRICOS                              │
│  - Media precisión (70-80%)                                             │
│  - Alta cobertura (detecta marcas desconocidas)                         │
│  - Detecta: "[Palabra][Espacio][Código]" → "NucBox K8"                  │
│  - Detecta: "[SIGLAS][números]" → "UM790", "SER7"                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  NIVEL 3: DETECCIÓN POR IA (OPCIONAL)                                   │
│  - Alta precisión (90%+)                                                │
│  - Alto costo (requiere API calls)                                      │
│  - Para: casos difíciles, validación, enriquecimiento                   │
└─────────────────────────────────────────────────────────────────────────┘

ÚLTIMA ACTUALIZACIÓN: 2024-12
=============================================================================
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Pattern, Set
from enum import Enum
from datetime import datetime


# =============================================================================
# ENUMS Y DATACLASSES
# =============================================================================

class ProductCategory(Enum):
    """Categorías de productos"""
    GPU = "gpu"
    CPU = "cpu"
    MINI_PC = "mini_pc"
    LAPTOP = "laptop"
    MONITOR = "monitor"
    STORAGE = "storage"
    SMARTPHONE = "smartphone"
    AUDIO = "audio"
    PERIPHERAL = "peripheral"
    CONSOLE = "console"
    NETWORKING = "networking"
    UNKNOWN = "unknown"


class DetectionLevel(Enum):
    """Nivel de detección que encontró el producto"""
    KNOWN_BRAND = 1      # Marca conocida, alta confianza
    STRUCTURAL = 2       # Patrón estructural, media confianza
    AI_DETECTED = 3      # Detectado por IA
    CONTEXT = 4          # Inferido por contexto


class SignalType(Enum):
    """Tipos de señal de compra"""
    WHERE_TO_BUY = "where_to_buy"
    PRICE_CHECK = "price_check"
    AVAILABILITY = "availability"
    RETAILER = "retailer"
    SHIPPING = "shipping"
    URGENCY = "urgency"


class Market(Enum):
    """Mercados objetivo de PCComponentes"""
    ES = "ES"
    PT = "PT"
    FR = "FR"
    IT = "IT"
    DE = "DE"
    GLOBAL = "GLOBAL"


@dataclass
class DetectedProduct:
    """Producto detectado con metadatos"""
    name: str
    original_match: str
    category: ProductCategory
    detection_level: DetectionLevel
    confidence: float  # 0.0 - 1.0
    brand: Optional[str] = None
    pattern_name: Optional[str] = None


@dataclass
class BuyingSignal:
    """Señal de intención de compra"""
    phrase: str
    signal_type: SignalType
    market: Market
    weight: int = 5  # 1-10


# =============================================================================
# NIVEL 1: PATRONES DE MARCAS CONOCIDAS
# =============================================================================

KNOWN_BRAND_PATTERNS: Dict[str, Tuple[str, ProductCategory, int]] = {
    # GPU - NVIDIA (captura completa: RTX 4090, GTX 1660 Ti)
    "nvidia_rtx": (r'\b(RTX\s*\d{4})\s*(Ti|SUPER|Super)?\b', ProductCategory.GPU, 10),
    "nvidia_gtx": (r'\b(GTX\s*\d{3,4})\s*(Ti)?\b', ProductCategory.GPU, 10),
    # GPU - AMD (captura completa: RX 7900 XTX)
    "amd_rx": (r'\b(RX\s*\d{4})\s*(XT|XTX)?\b', ProductCategory.GPU, 10),
    # GPU - Intel
    "intel_arc": (r'\b(Arc\s*[AB]\d{3,4})\b', ProductCategory.GPU, 10),
    
    # CPU - AMD (captura completa: Ryzen 9 7950X)
    "amd_ryzen": (r'\b(Ryzen\s*[3579]\s*\d{4}[A-Z]*)\b', ProductCategory.CPU, 10),
    "amd_threadripper": (r'\b(Threadripper\s*(?:PRO\s*)?\d{4}[A-Z]*)\b', ProductCategory.CPU, 10),
    # CPU - Intel (captura completa: Core i9-14900K)
    "intel_core": (r'\b(Core\s*i[3579][-\s]?\d{4,5}[A-Z]*)\b', ProductCategory.CPU, 10),
    "intel_ultra": (r'\b((?:Intel\s*)?Ultra\s*[579]\s*\d{3}[A-Z]*)\b', ProductCategory.CPU, 10),
    
    # MINI PC - Marcas emergentes (PRIORIDAD MÁXIMA)
    # Captura: "Minisforum UM790 Pro"
    "minisforum": (r'\b(Minisforum\s+[A-Z]{2,}\d*\s*(?:Pro|Plus|Max)?)\b', ProductCategory.MINI_PC, 15),
    "gmktec": (r'\b(GMKtec\s+[A-Za-z]+\s*[A-Z]*\d*)\b', ProductCategory.MINI_PC, 15),
    "beelink": (r'\b(Beelink\s+[A-Z]{2,}\d*)\b', ProductCategory.MINI_PC, 15),
    "geekom": (r'\b(GEEKOM\s+[A-Za-z]+\s*\d*)\b', ProductCategory.MINI_PC, 15),
    "acemagic": (r'\b(ACEMAGIC\s+[A-Za-z]+\d*)\b', ProductCategory.MINI_PC, 15),
    "trigkey": (r'\b(TRIGKEY\s+[A-Za-z]+\s*\d*)\b', ProductCategory.MINI_PC, 14),
    "chuwi": (r'\b(CHUWI\s+[A-Za-z]+\s*[A-Z]*\d*)\b', ProductCategory.MINI_PC, 14),
    "intel_nuc": (r'\b(NUC\s*\d{1,2}\s*(?:Pro|Extreme|Performance)?)\b', ProductCategory.MINI_PC, 10),
    
    # SMARTPHONES
    "iphone": (r'\b(iPhone\s*\d{1,2}\s*(?:Pro|Plus|Pro\s*Max|Mini|SE)?)\b', ProductCategory.SMARTPHONE, 10),
    "galaxy_s": (r'\b(Galaxy\s*S\d{2}\s*(?:Ultra|\+|Plus|FE)?)\b', ProductCategory.SMARTPHONE, 10),
    "galaxy_z": (r'\b(Galaxy\s*Z\s*(?:Fold|Flip)\s*\d?)\b', ProductCategory.SMARTPHONE, 10),
    "pixel": (r'\b(Pixel\s*\d[a]?\s*(?:Pro|XL)?)\b', ProductCategory.SMARTPHONE, 10),
    "xiaomi": (r'\b(Xiaomi\s*\d{1,2}\s*(?:Ultra|Pro|T)?)\b', ProductCategory.SMARTPHONE, 10),
    
    # CONSOLAS
    "steam_deck": (r'\b(Steam\s*Deck\s*(?:OLED|LCD)?)\b', ProductCategory.CONSOLE, 12),
    "rog_ally": (r'\b(ROG\s*Ally(?:\s*[A-Za-z]+)?)\b', ProductCategory.CONSOLE, 12),
    "legion_go": (r'\b(Legion\s*Go)\b', ProductCategory.CONSOLE, 12),
    "ps5": (r'\b(PS5|PlayStation\s*5)\s*(Slim|Pro|Digital)?\b', ProductCategory.CONSOLE, 10),
    "xbox": (r'\b(Xbox\s*Series\s*[XS])\b', ProductCategory.CONSOLE, 10),
    
    # LAPTOPS
    "macbook": (r'\b(MacBook\s*(?:Air|Pro)?\s*(?:M[1234]\s*(?:Pro|Max|Ultra)?)?)\b', ProductCategory.LAPTOP, 10),
    "thinkpad": (r'\b(ThinkPad\s*[A-Z]\d{2,3}[a-z]?)\b', ProductCategory.LAPTOP, 10),
    "framework": (r'\b(Framework\s*(?:Laptop)?\s*\d{2}?)\b', ProductCategory.LAPTOP, 12),
}


# =============================================================================
# NIVEL 2: PATRONES ESTRUCTURALES GENÉRICOS
# =============================================================================

"""
Estos patrones detectan productos SIN conocer la marca.
Basados en la ESTRUCTURA del nombre, no en marcas específicas.

Ejemplos que detecta:
- "XYZTech NanoBox Pro" → Marca + Producto + Variante
- "UM790 Pro" → Código alfanumérico + variante
- "K8 Plus" → Código corto + modificador
"""

STRUCTURAL_PATTERNS: List[Tuple[str, str, float]] = [
    # Patrón: [PalabraCapitalizada] [CódigoAlfanumérico] [Variante?]
    # Detecta: "NucBox K8", "HeroBox X5", "MiniPC N100"
    # NO detecta: artículos como "El", "La", "The"
    (
        "brand_product_code",
        r'(?<![A-Za-z])([A-Z][a-z]{2,}(?:[A-Z][a-z]+)?)\s+([A-Z]{1,3}\d{1,4}[A-Z]?)\s*(Pro|Plus|Max|Ultra|Lite|Mini)?(?![a-z])',
        0.75
    ),
    
    # Patrón: [SIGLAS mayúsculas 2-4 chars] [Números 2-4 digits] [Variante?]
    # Detecta: "UM790", "SER7", "GTR7", "HX99G"
    # Requiere que las siglas estén al inicio de palabra
    (
        "code_model",
        r'(?<![A-Za-z])([A-Z]{2,4})(\d{2,4}[A-Z]{0,2})\s*(Pro|Plus|Max|Ultra)?(?![a-z])',
        0.70
    ),
    
    # Patrón: Producto con guión: XX-XXXX o XXXX-XX
    # Detecta: "SN-850X", "WH-1000XM5", "X1-Carbon"
    (
        "hyphenated_model",
        r'\b([A-Z]{1,3}\d?)-(\d{3,4}[A-Z]{0,3})\b',
        0.70
    ),
    
    # Patrón: Número + Unidad de almacenamiento (para detectar variantes de producto)
    # Detecta: "1TB model", "512GB version"
    (
        "storage_variant",
        r'\b(\d{3,4})\s*(GB|TB)\s*(model|version|variant)?\b',
        0.40
    ),
]


# =============================================================================
# SEÑALES DE INTENCIÓN DE COMPRA POR MERCADO
# =============================================================================

BUYING_SIGNALS: Dict[Market, List[BuyingSignal]] = {
    Market.ES: [
        # Dónde comprar
        BuyingSignal("dónde comprar", SignalType.WHERE_TO_BUY, Market.ES, 10),
        BuyingSignal("donde comprar", SignalType.WHERE_TO_BUY, Market.ES, 10),
        BuyingSignal("dónde lo compro", SignalType.WHERE_TO_BUY, Market.ES, 10),
        BuyingSignal("comprarlo en españa", SignalType.WHERE_TO_BUY, Market.ES, 10),
        BuyingSignal("disponible en españa", SignalType.WHERE_TO_BUY, Market.ES, 9),
        # Precio
        BuyingSignal("cuánto cuesta", SignalType.PRICE_CHECK, Market.ES, 8),
        BuyingSignal("precio en españa", SignalType.PRICE_CHECK, Market.ES, 9),
        BuyingSignal("mejor precio", SignalType.PRICE_CHECK, Market.ES, 8),
        BuyingSignal("oferta", SignalType.PRICE_CHECK, Market.ES, 5),
        BuyingSignal("chollos", SignalType.PRICE_CHECK, Market.ES, 6),
        # Stock
        BuyingSignal("hay stock", SignalType.AVAILABILITY, Market.ES, 9),
        BuyingSignal("en stock", SignalType.AVAILABILITY, Market.ES, 8),
        BuyingSignal("agotado", SignalType.AVAILABILITY, Market.ES, 7),
        BuyingSignal("cuándo llega a españa", SignalType.AVAILABILITY, Market.ES, 10),
        # Retailers
        BuyingSignal("pccomponentes", SignalType.RETAILER, Market.ES, 10),
        BuyingSignal("pc componentes", SignalType.RETAILER, Market.ES, 10),
        BuyingSignal("amazon.es", SignalType.RETAILER, Market.ES, 9),
        BuyingSignal("mediamarkt", SignalType.RETAILER, Market.ES, 7),
        BuyingSignal("coolmod", SignalType.RETAILER, Market.ES, 8),
        # Envío
        BuyingSignal("envío a españa", SignalType.SHIPPING, Market.ES, 8),
        BuyingSignal("envío gratis", SignalType.SHIPPING, Market.ES, 6),
        # Urgencia
        BuyingSignal("vale la pena comprarlo", SignalType.URGENCY, Market.ES, 9),
        BuyingSignal("merece la pena", SignalType.URGENCY, Market.ES, 8),
    ],
    
    Market.PT: [
        BuyingSignal("onde comprar", SignalType.WHERE_TO_BUY, Market.PT, 10),
        BuyingSignal("comprar em portugal", SignalType.WHERE_TO_BUY, Market.PT, 10),
        BuyingSignal("quanto custa", SignalType.PRICE_CHECK, Market.PT, 8),
        BuyingSignal("melhor preço", SignalType.PRICE_CHECK, Market.PT, 8),
        BuyingSignal("em stock", SignalType.AVAILABILITY, Market.PT, 8),
        BuyingSignal("pcdiga", SignalType.RETAILER, Market.PT, 10),
        BuyingSignal("globaldata", SignalType.RETAILER, Market.PT, 9),
        BuyingSignal("worten", SignalType.RETAILER, Market.PT, 8),
        BuyingSignal("vale a pena comprar", SignalType.URGENCY, Market.PT, 9),
    ],
    
    Market.FR: [
        BuyingSignal("où acheter", SignalType.WHERE_TO_BUY, Market.FR, 10),
        BuyingSignal("acheter en france", SignalType.WHERE_TO_BUY, Market.FR, 10),
        BuyingSignal("combien coûte", SignalType.PRICE_CHECK, Market.FR, 8),
        BuyingSignal("meilleur prix", SignalType.PRICE_CHECK, Market.FR, 8),
        BuyingSignal("bon plan", SignalType.PRICE_CHECK, Market.FR, 7),
        BuyingSignal("en stock", SignalType.AVAILABILITY, Market.FR, 8),
        BuyingSignal("rupture de stock", SignalType.AVAILABILITY, Market.FR, 7),
        BuyingSignal("ldlc", SignalType.RETAILER, Market.FR, 10),
        BuyingSignal("materiel.net", SignalType.RETAILER, Market.FR, 10),
        BuyingSignal("amazon.fr", SignalType.RETAILER, Market.FR, 9),
        BuyingSignal("topachat", SignalType.RETAILER, Market.FR, 9),
        BuyingSignal("vaut le coup", SignalType.URGENCY, Market.FR, 9),
    ],
    
    Market.IT: [
        BuyingSignal("dove comprare", SignalType.WHERE_TO_BUY, Market.IT, 10),
        BuyingSignal("comprare in italia", SignalType.WHERE_TO_BUY, Market.IT, 10),
        BuyingSignal("quanto costa", SignalType.PRICE_CHECK, Market.IT, 8),
        BuyingSignal("miglior prezzo", SignalType.PRICE_CHECK, Market.IT, 8),
        BuyingSignal("disponibile", SignalType.AVAILABILITY, Market.IT, 6),
        BuyingSignal("amazon.it", SignalType.RETAILER, Market.IT, 9),
        BuyingSignal("drako.it", SignalType.RETAILER, Market.IT, 9),
        BuyingSignal("vale la pena comprare", SignalType.URGENCY, Market.IT, 9),
    ],
    
    Market.DE: [
        BuyingSignal("wo kaufen", SignalType.WHERE_TO_BUY, Market.DE, 10),
        BuyingSignal("kaufen in deutschland", SignalType.WHERE_TO_BUY, Market.DE, 10),
        BuyingSignal("was kostet", SignalType.PRICE_CHECK, Market.DE, 8),
        BuyingSignal("bester preis", SignalType.PRICE_CHECK, Market.DE, 8),
        BuyingSignal("auf lager", SignalType.AVAILABILITY, Market.DE, 8),
        BuyingSignal("lieferbar", SignalType.AVAILABILITY, Market.DE, 7),
        BuyingSignal("mindfactory", SignalType.RETAILER, Market.DE, 10),
        BuyingSignal("alternate", SignalType.RETAILER, Market.DE, 10),
        BuyingSignal("amazon.de", SignalType.RETAILER, Market.DE, 9),
        BuyingSignal("caseking", SignalType.RETAILER, Market.DE, 9),
        BuyingSignal("lohnt sich", SignalType.URGENCY, Market.DE, 9),
    ],
    
    Market.GLOBAL: [
        BuyingSignal("where to buy", SignalType.WHERE_TO_BUY, Market.GLOBAL, 10),
        BuyingSignal("how to buy", SignalType.WHERE_TO_BUY, Market.GLOBAL, 8),
        BuyingSignal("buy in europe", SignalType.WHERE_TO_BUY, Market.GLOBAL, 10),
        BuyingSignal("available in europe", SignalType.WHERE_TO_BUY, Market.GLOBAL, 9),
        BuyingSignal("best price", SignalType.PRICE_CHECK, Market.GLOBAL, 8),
        BuyingSignal("how much", SignalType.PRICE_CHECK, Market.GLOBAL, 7),
        BuyingSignal("in stock", SignalType.AVAILABILITY, Market.GLOBAL, 8),
        BuyingSignal("out of stock", SignalType.AVAILABILITY, Market.GLOBAL, 7),
        BuyingSignal("pre-order", SignalType.AVAILABILITY, Market.GLOBAL, 8),
        BuyingSignal("ships to europe", SignalType.SHIPPING, Market.GLOBAL, 9),
        BuyingSignal("eu shipping", SignalType.SHIPPING, Market.GLOBAL, 8),
        BuyingSignal("should i buy", SignalType.URGENCY, Market.GLOBAL, 9),
        BuyingSignal("worth buying", SignalType.URGENCY, Market.GLOBAL, 9),
        BuyingSignal("worth it", SignalType.URGENCY, Market.GLOBAL, 8),
    ],
}


# =============================================================================
# PALABRAS A EXCLUIR (falsos positivos comunes)
# =============================================================================

EXCLUDE_WORDS: Set[str] = {
    # Términos de video
    "review", "unboxing", "test", "hands on", "first look",
    "vs", "versus", "comparison", "compared",
    # Términos genéricos
    "best", "worst", "top", "ranking", "guide",
    "update", "news", "leak", "rumor", "specs",
    # Años
    "2023", "2024", "2025", "2026",
    # Monedas
    "usd", "eur", "gbp", "dollar", "euro",
    # Artículos (varios idiomas)
    "el", "la", "los", "las", "un", "una",
    "the", "a", "an",
    "le", "la", "les", "un", "une",
    "der", "die", "das", "ein", "eine",
    "il", "lo", "la", "i", "gli", "le",
    "o", "a", "os", "as", "um", "uma",
    # Otros
    "part", "episode", "chapter", "video",
    "new", "nuevo", "novo", "nouveau", "neu", "nuovo",
}

# Longitud mínima para considerar un match válido
MIN_PRODUCT_LENGTH = 4


# =============================================================================
# FUNCIONES DE DETECCIÓN
# =============================================================================

# Cache de patrones compilados
_COMPILED_KNOWN: List[Tuple[str, Pattern, ProductCategory, int]] = []
_COMPILED_STRUCTURAL: List[Tuple[str, Pattern, float]] = []


def _compile_patterns():
    """Compila todos los patrones regex una sola vez"""
    global _COMPILED_KNOWN, _COMPILED_STRUCTURAL
    
    if not _COMPILED_KNOWN:
        for name, (pattern, category, priority) in KNOWN_BRAND_PATTERNS.items():
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                _COMPILED_KNOWN.append((name, compiled, category, priority))
            except re.error as e:
                print(f"Error compilando patrón '{name}': {e}")
        
        # Ordenar por prioridad (mayor primero)
        _COMPILED_KNOWN.sort(key=lambda x: x[3], reverse=True)
    
    if not _COMPILED_STRUCTURAL:
        for name, pattern, confidence in STRUCTURAL_PATTERNS:
            try:
                compiled = re.compile(pattern, re.IGNORECASE)
                _COMPILED_STRUCTURAL.append((name, compiled, confidence))
            except re.error as e:
                print(f"Error compilando patrón estructural '{name}': {e}")


def _clean_match(match) -> str:
    """Limpia y normaliza un match de regex"""
    if isinstance(match, tuple):
        # Unir grupos, filtrar None/vacíos
        parts = [str(m).strip() for m in match if m]
        return " ".join(parts)
    return str(match).strip()


def _is_valid_product(name: str, main_keyword: Optional[str] = None) -> bool:
    """Valida si un nombre de producto es válido"""
    name_lower = name.lower()
    
    # Muy corto
    if len(name) < MIN_PRODUCT_LENGTH:
        return False
    
    # Es palabra excluida
    if name_lower in EXCLUDE_WORDS:
        return False
    
    # Contiene palabra excluida como componente principal
    for word in EXCLUDE_WORDS:
        if name_lower == word or name_lower.startswith(word + " ") or name_lower.endswith(" " + word):
            return False
    
    # Es el keyword principal de búsqueda
    if main_keyword and main_keyword.lower() in name_lower:
        return False
    
    # Solo números
    if name.replace(" ", "").isdigit():
        return False
    
    return True


def extract_products(
    text: str,
    main_keyword: Optional[str] = None,
    use_structural: bool = True,
    min_confidence: float = 0.5
) -> List[DetectedProduct]:
    """
    Extrae productos de un texto usando detección multinivel.
    
    Args:
        text: Texto a analizar (título, descripción, etc.)
        main_keyword: Keyword principal a excluir de resultados
        use_structural: Si usar patrones estructurales genéricos
        min_confidence: Confianza mínima para incluir (0.0-1.0)
    
    Returns:
        Lista de DetectedProduct ordenada por confianza
    """
    _compile_patterns()
    
    products: List[DetectedProduct] = []
    seen_names: Set[str] = set()
    
    # NIVEL 1: Marcas conocidas
    for name, compiled, category, priority in _COMPILED_KNOWN:
        matches = compiled.findall(text)
        for match in matches:
            product_name = _clean_match(match).upper()
            
            if not _is_valid_product(product_name, main_keyword):
                continue
            
            if product_name in seen_names:
                continue
            
            seen_names.add(product_name)
            
            # Extraer marca del nombre del patrón
            brand = name.split("_")[0].upper() if "_" in name else None
            
            products.append(DetectedProduct(
                name=product_name,
                original_match=_clean_match(match),
                category=category,
                detection_level=DetectionLevel.KNOWN_BRAND,
                confidence=0.95,  # Alta confianza para marcas conocidas
                brand=brand,
                pattern_name=name
            ))
    
    # NIVEL 2: Patrones estructurales
    if use_structural:
        for name, compiled, base_confidence in _COMPILED_STRUCTURAL:
            if base_confidence < min_confidence:
                continue
                
            matches = compiled.findall(text)
            for match in matches:
                product_name = _clean_match(match).upper()
                
                if not _is_valid_product(product_name, main_keyword):
                    continue
                
                if product_name in seen_names:
                    continue
                
                # Validación adicional para estructurales
                # Debe tener al menos una letra y un número
                has_letter = any(c.isalpha() for c in product_name)
                has_digit = any(c.isdigit() for c in product_name)
                
                if not (has_letter and has_digit):
                    continue
                
                seen_names.add(product_name)
                
                products.append(DetectedProduct(
                    name=product_name,
                    original_match=_clean_match(match),
                    category=ProductCategory.UNKNOWN,
                    detection_level=DetectionLevel.STRUCTURAL,
                    confidence=base_confidence,
                    pattern_name=name
                ))
    
    # Ordenar por confianza (mayor primero)
    products.sort(key=lambda p: p.confidence, reverse=True)
    
    return products


def analyze_buying_signals(
    text: str,
    markets: Optional[List[Market]] = None
) -> Dict:
    """
    Analiza señales de intención de compra en un texto.
    
    Args:
        text: Texto a analizar
        markets: Mercados a analizar (None = todos)
    
    Returns:
        Dict con análisis detallado
    """
    if markets is None:
        markets = list(Market)
    
    text_lower = text.lower()
    
    result = {
        "total_signals": 0,
        "total_weight": 0,
        "by_market": {},
        "by_type": {t.value: 0 for t in SignalType},
        "matches": [],
        "retailers_found": [],
    }
    
    for market in markets:
        if market not in BUYING_SIGNALS:
            continue
        
        market_signals = 0
        market_weight = 0
        
        for signal in BUYING_SIGNALS[market]:
            if signal.phrase.lower() in text_lower:
                market_signals += 1
                market_weight += signal.weight
                result["total_signals"] += 1
                result["total_weight"] += signal.weight
                result["by_type"][signal.signal_type.value] += 1
                
                result["matches"].append({
                    "phrase": signal.phrase,
                    "type": signal.signal_type.value,
                    "market": market.value,
                    "weight": signal.weight
                })
                
                if signal.signal_type == SignalType.RETAILER:
                    result["retailers_found"].append({
                        "name": signal.phrase,
                        "market": market.value
                    })
        
        if market_signals > 0:
            result["by_market"][market.value] = {
                "signals": market_signals,
                "weight": market_weight
            }
    
    return result


def get_all_signals() -> List[BuyingSignal]:
    """Retorna todas las señales de compra"""
    all_signals = []
    for market_signals in BUYING_SIGNALS.values():
        all_signals.extend(market_signals)
    return all_signals


def get_budget_keywords() -> List[str]:
    """Keywords que indican alternativa económica"""
    return [
        # Inglés
        "budget", "affordable", "cheap", "cheaper", "best value",
        "value for money", "bang for buck", "budget king", "budget killer",
        "alternative", "instead of", "better than", "beats",
        # Español
        "barato", "económico", "alternativa", "mejor valor",
        "relación calidad precio", "en lugar de",
        # Portugués
        "barato", "alternativa", "melhor valor",
        # Francés
        "pas cher", "alternative", "meilleur rapport",
        # Alemán
        "günstig", "alternative", "preis-leistung",
        # Italiano
        "economico", "alternativa", "miglior rapporto",
    ]


# =============================================================================
# SCORING DEFINITIONS
# =============================================================================

@dataclass
class ScoreDefinition:
    """Definición de un score con documentación"""
    id: str
    name: str
    description: str
    min_value: int
    max_value: int
    time_frame: str
    formula: str
    ranges: List[Tuple[int, int, str, str]]  # (min, max, label, action)


SCORE_DEFINITIONS: Dict[str, ScoreDefinition] = {
    "hype_score": ScoreDefinition(
        id="hype_score",
        name="Hype Score",
        description="Mide la intensidad del hype basándose en videos/semana desde el primer video",
        min_value=0,
        max_value=100,
        time_frame="Desde primer video detectado hasta hoy",
        formula="(videos_totales / semanas_desde_primero) * factor_recencia",
        ranges=[
            (80, 100, "EXPLOSIVO", "🔥 Máxima prioridad"),
            (60, 79, "CALIENTE", "🌡️ Alta actividad"),
            (40, 59, "TIBIO", "☀️ Actividad moderada"),
            (20, 39, "FRÍO", "❄️ Baja actividad"),
            (0, 19, "CONGELADO", "🧊 Sin actividad"),
        ]
    ),
    
    "buying_intent_score": ScoreDefinition(
        id="buying_intent_score",
        name="Buying Intent Score",
        description="Intensidad de intención de compra detectada en contenido",
        min_value=0,
        max_value=100,
        time_frame="Últimos 90 días de videos analizados",
        formula="sum(señales * peso) normalizado a 0-100",
        ranges=[
            (70, 100, "DEMANDA ALTA", "🛒 Demanda activa - gente quiere comprar"),
            (40, 69, "DEMANDA MODERADA", "🤔 Interés pero no urgente"),
            (20, 39, "DEMANDA BAJA", "😐 Poco interés en comprar"),
            (0, 19, "SIN DEMANDA", "ℹ️ Contenido informativo"),
        ]
    ),
    
    "product_opportunity_score": ScoreDefinition(
        id="product_opportunity_score",
        name="Product Opportunity Score",
        description="Score compuesto de oportunidad de negocio",
        min_value=0,
        max_value=100,
        time_frame="Combina datos de últimos 90 días",
        formula="hype(30%) + buying_intent(25%) + budget_alternatives(20%) + market_coverage(25%)",
        ranges=[
            (70, 100, "OPORTUNIDAD ALTA", "🎯 Priorizar para análisis"),
            (50, 69, "OPORTUNIDAD MEDIA", "📊 Monitorear"),
            (30, 49, "OPORTUNIDAD BAJA", "👁️ Mantener en radar"),
            (0, 29, "SIN OPORTUNIDAD", "⏸️ No relevante"),
        ]
    ),
}


def get_score_definition(score_id: str) -> Optional[ScoreDefinition]:
    """Obtiene la definición de un score"""
    return SCORE_DEFINITIONS.get(score_id)


def get_score_interpretation(score_id: str, value: int) -> Optional[Tuple[str, str]]:
    """Obtiene la interpretación de un valor de score"""
    definition = get_score_definition(score_id)
    if not definition:
        return None
    
    for min_val, max_val, label, action in definition.ranges:
        if min_val <= value <= max_val:
            return (label, action)
    
    return None


# =============================================================================
# EXPORTS
# =============================================================================

# Tipos
__all__ = [
    # Enums
    "ProductCategory",
    "DetectionLevel",
    "SignalType",
    "Market",
    # Dataclasses
    "DetectedProduct",
    "BuyingSignal",
    "ScoreDefinition",
    # Funciones principales
    "extract_products",
    "analyze_buying_signals",
    "get_all_signals",
    "get_budget_keywords",
    "get_score_definition",
    "get_score_interpretation",
    # Datos
    "BUYING_SIGNALS",
    "KNOWN_BRAND_PATTERNS",
    "STRUCTURAL_PATTERNS",
    "SCORE_DEFINITIONS",
    "EXCLUDE_WORDS",
]


# Compatibilidad con código existente
ALL_SIGNALS = get_all_signals()
ALL_PATTERNS = list(KNOWN_BRAND_PATTERNS.keys())

def compile_patterns():
    """Compatibilidad: compila y retorna patrones"""
    _compile_patterns()
    return _COMPILED_KNOWN

GLOBAL_EXCLUDE_WORDS = list(EXCLUDE_WORDS)
