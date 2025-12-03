"""
Smoke tests para Abra Trend Hunter
Verifica que todos los módulos cargan y las funciones básicas funcionan
"""
import sys
sys.path.insert(0, '.')

def test_imports():
    """Test que todos los módulos se pueden importar"""
    errors = []
    
    # Modules
    try:
        from modules.google_trends import GoogleTrendsModule, calculate_growth_rate, calculate_seasonality
    except Exception as e:
        errors.append(f"google_trends: {e}")
    
    try:
        from modules.related_queries import RelatedQueriesModule
    except Exception as e:
        errors.append(f"related_queries: {e}")
    
    try:
        from modules.serp_paa import PeopleAlsoAskModule
    except Exception as e:
        errors.append(f"serp_paa: {e}")
    
    try:
        from modules.google_news import GoogleNewsModule
    except Exception as e:
        errors.append(f"google_news: {e}")
    
    try:
        from modules.product_analysis import ProductAnalyzer
    except Exception as e:
        errors.append(f"product_analysis: {e}")
    
    try:
        from modules.scoring import ScoringEngine
    except Exception as e:
        errors.append(f"scoring: {e}")
    
    try:
        from modules.ai_analysis import AIAnalyzer
    except Exception as e:
        errors.append(f"ai_analysis: {e}")
    
    # Utils
    try:
        from utils.validation import (
            sanitize_html, sanitize_for_query, safe_float, safe_int,
            safe_divide, safe_get, validate_url
        )
    except Exception as e:
        errors.append(f"validation: {e}")
    
    if errors:
        print("❌ Import errors:")
        for err in errors:
            print(f"  - {err}")
        return False
    
    print("✅ All imports successful")
    return True


def test_validation_functions():
    """Test funciones de validación"""
    from utils.validation import (
        sanitize_html, sanitize_for_query, safe_float, safe_int,
        safe_divide, safe_get, safe_list, safe_dict
    )
    
    errors = []
    
    # Test sanitize_html
    if sanitize_html("<script>alert('xss')</script>") != "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;":
        errors.append("sanitize_html failed")
    
    # Test safe_float
    if safe_float(None) != 0.0:
        errors.append("safe_float(None) failed")
    if safe_float("invalid") != 0.0:
        errors.append("safe_float('invalid') failed")
    if safe_float(3.14) != 3.14:
        errors.append("safe_float(3.14) failed")
    
    # Test safe_int
    if safe_int(None) != 0:
        errors.append("safe_int(None) failed")
    if safe_int(3.7) != 3:
        errors.append("safe_int(3.7) failed")
    
    # Test safe_divide
    if safe_divide(10, 2) != 5.0:
        errors.append("safe_divide(10, 2) failed")
    if safe_divide(10, 0) != 0.0:
        errors.append("safe_divide(10, 0) failed")
    if safe_divide(10, 0, default=-1) != -1:
        errors.append("safe_divide with default failed")
    
    # Test safe_get
    test_dict = {"a": 1, "b": {"c": 2}}
    if safe_get(test_dict, "a") != 1:
        errors.append("safe_get failed")
    if safe_get(test_dict, "x", default=99) != 99:
        errors.append("safe_get with default failed")
    
    # Test safe_list
    if safe_list(None) != []:
        errors.append("safe_list(None) failed")
    if safe_list([1, 2]) != [1, 2]:
        errors.append("safe_list([1,2]) failed")
    
    # Test safe_dict
    if safe_dict(None) != {}:
        errors.append("safe_dict(None) failed")
    
    if errors:
        print("❌ Validation function errors:")
        for err in errors:
            print(f"  - {err}")
        return False
    
    print("✅ All validation functions working")
    return True


def test_scoring_engine():
    """Test básico del motor de scoring"""
    from modules.scoring import ScoringEngine
    
    engine = ScoringEngine()
    
    # Test con datos vacíos (no debe fallar)
    try:
        result = engine.calculate_trend_score(timeline_data=[])
    except Exception as e:
        print(f"❌ ScoringEngine raised exception: {e}")
        return False
    
    if result is None:
        print("❌ ScoringEngine returned None for empty data")
        return False
    
    print("✅ ScoringEngine handles empty data correctly")
    return True


def test_growth_rate_calculation():
    """Test cálculo de growth rate"""
    from modules.google_trends import calculate_growth_rate
    
    # Test con datos vacíos
    result = calculate_growth_rate([])
    if result.get("growth_rate") != 0:
        print("❌ calculate_growth_rate failed with empty data")
        return False
    
    # Test con datos mínimos
    timeline = [
        {"date": "Jan 2024", "values": [{"extracted_value": 50}]},
        {"date": "Feb 2024", "values": [{"extracted_value": 60}]},
        {"date": "Mar 2024", "values": [{"extracted_value": 70}]},
        {"date": "Apr 2024", "values": [{"extracted_value": 80}]},
    ]
    result = calculate_growth_rate(timeline)
    
    if "growth_rate" not in result:
        print("❌ calculate_growth_rate missing growth_rate key")
        return False
    
    print("✅ calculate_growth_rate working correctly")
    return True


def test_product_analyzer():
    """Test básico del analizador de productos"""
    from modules.product_analysis import ProductAnalyzer
    
    analyzer = ProductAnalyzer(api_key="test")
    
    # Test detección de productos
    rising_queries = [
        {"query": "Beelink SER5 Pro review", "value": 100},
        {"query": "Minisforum UM790 Pro specs", "value": 80},
    ]
    top_queries = [
        {"query": "mini pc comparison", "value": 60}
    ]
    
    related_queries = {
        "rising": rising_queries,
        "top": top_queries
    }
    
    products = analyzer.detect_products("mini pc", related_queries)
    
    if not isinstance(products, list):
        print("❌ detect_products should return a list")
        return False
    
    print(f"✅ ProductAnalyzer detected {len(products)} products")
    return True


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "="*50)
    print("🧪 ABRA TREND HUNTER - SMOKE TESTS")
    print("="*50 + "\n")
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Validation Functions", test_validation_functions()))
    results.append(("Scoring Engine", test_scoring_engine()))
    results.append(("Growth Rate", test_growth_rate_calculation()))
    results.append(("Product Analyzer", test_product_analyzer()))
    
    print("\n" + "="*50)
    print("📊 RESULTADOS")
    print("="*50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print("="*50 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
