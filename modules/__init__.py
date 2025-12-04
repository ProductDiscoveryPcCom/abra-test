"""
Abra Trend Hunter - Data Modules
Módulos independientes para cada fuente de datos
"""

from .google_trends import GoogleTrendsModule
from .related_queries import RelatedQueriesModule
from .serp_paa import PeopleAlsoAskModule
from .google_news import GoogleNewsModule
from .product_analysis import ProductAnalyzer, ProductData, OpportunityCategory, LifecycleStage
from .scoring import ScoringEngine
from .ai_analysis import AIAnalyzer
from .search_volume import SearchVolumeEstimator, estimate_from_trends_data
from .aliexpress import AliExpressModule, check_aliexpress_config, get_aliexpress_module
from .youtube import YouTubeModule, YouTubeVideo, YouTubeMetrics, check_youtube_config, get_youtube_module
from .tiktok import TikTokModule, TikTokMetrics, check_tiktok_config, get_tiktok_module
from .social_score import SocialScoreCalculator, SocialMetrics, get_social_score_calculator

__all__ = [
    'GoogleTrendsModule',
    'RelatedQueriesModule',
    'PeopleAlsoAskModule',
    'GoogleNewsModule',
    'ProductAnalyzer',
    'ProductData',
    'OpportunityCategory',
    'LifecycleStage',
    'ScoringEngine',
    'AIAnalyzer',
    'SearchVolumeEstimator',
    'estimate_from_trends_data',
    'AliExpressModule',
    'check_aliexpress_config',
    'get_aliexpress_module',
    'YouTubeModule',
    'YouTubeVideo',
    'YouTubeMetrics',
    'check_youtube_config',
    'get_youtube_module',
    'TikTokModule',
    'TikTokMetrics',
    'check_tiktok_config',
    'get_tiktok_module',
    'SocialScoreCalculator',
    'SocialMetrics',
    'get_social_score_calculator'
]

