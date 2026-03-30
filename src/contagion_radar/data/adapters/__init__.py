"""Data source adapters."""

from .base import AdapterError, DataAdapter
from .defillama import DeFiLlamaAdapter
from .etherscan import EtherscanAdapter
from .news import NewsAdapter
from .social import SocialAdapter
from .yahoo_finance import YahooFinanceAdapter

__all__ = [
    "DataAdapter",
    "AdapterError",
    "DeFiLlamaAdapter",
    "EtherscanAdapter",
    "YahooFinanceAdapter",
    "SocialAdapter",
    "NewsAdapter",
]
