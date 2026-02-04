import logging
from duckduckgo_search import DDGS

logging.basicConfig(level=logging.DEBUG)

print("Starting search...")
try:
    results = DDGS().text("test", max_results=1)
    print(f"Results: {results}")
    print(f"List: {list(results)}")
except Exception as e:
    print(f"Error: {e}")
