"""
AI Providers
Proveedores de IA intercambiables: Claude, GPT-4, Perplexity

Todos heredan de BaseAIProvider para garantizar interfaz consistente.
"""

from .base_provider import BaseAIProvider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .perplexity_provider import PerplexityProvider

__all__ = [
    'BaseAIProvider',
    'ClaudeProvider', 
    'OpenAIProvider', 
    'PerplexityProvider'
]

