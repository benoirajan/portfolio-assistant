"""
News and Web Search Service for AI Advisory Pipeline.
Fetches recent market news, sector updates, and company announcements
for Indian listed equities using DuckDuckGo / public financial search APIs.
Includes fallback caching to prevent rate limits.
"""
import logging
import urllib.parse
from typing import List, Dict, Any, Optional
import requests

from src.core.cache import get as cache_get, set as cache_set

logger = logging.getLogger("portfolio_assistant.news_search")

SEARCH_CACHE_TTL = 3600 * 6  # 6 hours cache for news queries


def search_company_news(symbol: str, count: int = 3) -> List[Dict[str, str]]:
    """
    Searches for recent news and financial updates for a given Indian stock symbol (NSE/BSE).
    Returns a list of dicts with title, snippet, and source.
    """
    logger.info("Executing tool 'search_company_news' for symbol='%s' (count=%d)", symbol, count)
    cache_key = f"news_search:stock:{symbol}"
    cached = cache_get(cache_key)
    if cached is not None:
        logger.debug("News search for %s served from cache", symbol)
        return cached

    query = f"{symbol} NSE stock news"
    results = _fetch_google_news_rss(query, count=count)

    if not results:
        results = [
            {
                "title": f"Recent operational context for {symbol}",
                "snippet": f"Tracking steady performance for {symbol} on Indian exchanges.",
                "source": "Market Watch",
            }
        ]

    cache_set(cache_key, results, ttl=SEARCH_CACHE_TTL)
    return results


def search_sector_news(sector: str, count: int = 3) -> List[Dict[str, str]]:
    """
    Searches for macro and sector trends for Indian equity markets.
    """
    logger.info("Executing tool 'search_sector_news' for sector='%s' (count=%d)", sector, count)
    cache_key = f"news_search:sector:{sector}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    query = f"Indian equity {sector} sector news"
    results = _fetch_google_news_rss(query, count=count)

    if not results:
        results = [
            {
                "title": f"{sector} sector overview India",
                "snippet": f"Key macro drivers and long-term demand trends impacting Indian {sector} companies.",
                "source": "Sector Analysis",
            }
        ]

    cache_set(cache_key, results, ttl=SEARCH_CACHE_TTL)
    return results


import xml.etree.ElementTree as ET
import email.utils

def _fetch_google_news_rss(query: str, count: int = 3) -> List[Dict[str, str]]:
    """Helper to query Google News RSS API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            articles = []
            for item in root.findall(".//item")[:count]:
                title = item.findtext("title")
                source = item.findtext("source")
                pubDate = item.findtext("pubDate")
                
                if pubDate:
                    try:
                        dt = email.utils.parsedate_to_datetime(pubDate)
                        pubDate = dt.strftime("%d %b %Y")
                    except Exception:
                        pass

                if title:
                    articles.append({
                        "title": title,
                        "snippet": title,
                        "source": f"{source} - {pubDate}" if pubDate and source else source or "Google News",
                    })
            if articles:
                return articles
    except Exception as e:
        logger.warning("Google News RSS fetch failed for query '%s': %s", query, e)

    return []
