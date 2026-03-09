import subprocess
from bs4 import BeautifulSoup
import re
from collections import Counter

def scrape_ebay_comps_with_tokens(query: str):
    url = f"https://www.ebay.com/sch/i.html?_nkw={query.replace(' ', '+')}&LH_Sold=1&LH_Complete=1"
    
    # Use curl to bypass simple python-requests blocking
    try:
        result = subprocess.run(
            ["curl", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0", url],
            capture_output=True, text=True, timeout=15
        )
        html = result.stdout
    except Exception as e:
        print(f"Failed to curl: {e}")
        return [], []

    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".s-item__wrapper")
    
    comps = []
    all_words = []
    
    # Skip the first item as it's usually a recommendation
    for item in items[1:11]: 
        title_el = item.select_one(".s-item__title")
        title = title_el.text if title_el else ""
        
        if title.startswith("New Listing"):
            title = title[len("New Listing"):]
            
        price_el = item.select_one(".s-item__price")
        price_text = price_el.text if price_el else ""
        
        date_el = item.select_one(".s-item__title--tagblock .POSITIVE")
        date_sold = date_el.text if date_el else ""
        
        link_el = item.select_one(".s-item__link")
        link = link_el["href"] if link_el and "href" in link_el.attrs else ""
        
        price = 0.0
        price_match = re.search(r'\$?([0-9,]+\.[0-9]{2})', price_text)
        if price_match:
            price = float(price_match.group(1).replace(',', ''))
            
        if title and price > 0:
            comps.append({
                "title": title.strip(),
                "price": price,
                "date_sold": date_sold,
                "link": link
            })
            # Tokenize title
            words = re.findall(r'\b[a-zA-Z0-9-]+\b', title.lower())
            stop_words = {"the", "and", "a", "an", "with", "in", "by", "of", "for", "new", "used"}
            all_words.extend([w for w in words if w not in stop_words and len(w) > 1])
            
    # Get top tokens
    common_tokens = [word for word, count in Counter(all_words).most_common(10)]
    
    return comps, common_tokens

if __name__ == "__main__":
    comps, tokens = scrape_ebay_comps_with_tokens("Sony WH-1000XM4 Headphones")
    print(f"Found {len(comps)} comps.")
    for c in comps[:3]:
        print(c)
    print("Top SEO Tokens:", tokens)
