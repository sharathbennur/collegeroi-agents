from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import requests
from bs4 import BeautifulSoup

@tool
def web_search(query: str) -> str:
    """Searches the web for information using DuckDuckGo."""
    try:
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://html.duckduckgo.com/"
        }
        
        resp = requests.post(url, data=data, headers=headers, timeout=10)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        results = []
        # Select result links (titles) and snippets
        for result in soup.select(".result"):
            title_tag = result.select_one(".result__a")
            snippet_tag = result.select_one(".result__snippet")
            
            if title_tag and snippet_tag:
                title = title_tag.get_text(strip=True)
                link = title_tag['href']
                snippet = snippet_tag.get_text(strip=True)
                results.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}\n")
                
                if len(results) >= 5:
                    break
                    
        return "\n---\n".join(results) if results else "No results found."
        
    except Exception as e:
        return f"Search failed: {e}"

@tool
def scrape_webpage(url: str) -> str:
    """Scrapes the text content from a given URL."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Kill all script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Limit text length to avoid context window issues
        return text[:10000] 
        
    except Exception as e:
        return f"Error scraping {url}: {str(e)}"
