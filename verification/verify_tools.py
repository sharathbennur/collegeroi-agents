from src.tools import web_search, scrape_webpage
import sys

def test_tools():
    print("Testing Search Tool...")
    try:
        search_result = web_search.invoke("University of California Berkeley tuition")
        print(f"Search Result (first 100 chars): {search_result[:100]}...")
    except Exception as e:
        print(f"Search Tool Failed: {e}")
        sys.exit(1)

    print("\nTesting Scrape Tool...")
    # We'll scrape a known stable(ish) page, or just google.com to test connectivity and parsing
    try:
        scrape_result = scrape_webpage.invoke("https://www.example.com")
        print(f"Scrape Result: {scrape_result[:100]}...")
        if "Example Domain" not in scrape_result:
            print("Scrape tool didn't return expected content.")
            # Not strictly failing as content might change, but good warning
    except Exception as e:
        print(f"Scrape Tool Failed: {e}")
        sys.exit(1)
        
    print("\nTools verification successful!")

if __name__ == "__main__":
    test_tools()
