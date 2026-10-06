import sys
sys.path.append('backend')
from src.services.news_search import search_company_news

results = search_company_news("RELIANCE")
for r in results:
    print(f"- [{r['source']}] {r['title']}")
