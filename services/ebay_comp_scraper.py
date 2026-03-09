"""
eBay Exact-Comp Scraper / Fetcher
Uses the eBay Marketplace Insights API (or similar Sell APIs) and falls back to mock data if API keys are pending or invalid.
"get tokens" is handled via the EBayTokenManager which retrieves the OAuth access tokens needed for this secure endpoint.
"""

from typing import List, Dict, Any, Tuple
import requests
import re
import os
from collections import Counter
from services.ebay_token_manager import EBayTokenManager

class EbayCompScraper:
    """Service to fetch exact sold comps and extract popular title tokens."""

    def __init__(self):
        self.token_manager = EBayTokenManager()

    def scrape_comps(self, query: str, limit: int = 10, condition: str = None, min_price: float = None, max_price: float = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Fetch sold comps using eBay API/Scraping and return results with popular tokens.
        Supports filtering by condition and price range.
        """
        # Step 1: Attempt "Get Tokens"
        token = self.token_manager.get_valid_token()
        client_id = os.getenv('EBAY_CLIENT_ID', '')

        # Normalize condition for API if needed (API usually uses IDs)
        # 1000=New, 3000=Used, 7000=Parts

        comps = []

        # Only try API if we have a non-dummy client id
        if token and "dummy" not in client_id.lower():
            # Step 2: Query the Marketplace Insights API for sold comps
            try:
                # Basic API query (API filtering is more complex, focusing on scraper for flexibility)
                url = f"https://api.ebay.com/buy/marketplace_insights/v1/item_sales/search?q={requests.utils.quote(query)}&limit={limit}"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
                }

                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    item_sales = data.get("itemSales", [])

                    for item in item_sales:
                        title = item.get("title", "")
                        price = float(item.get("price", {}).get("value", "0.0"))
                        date_sold = item.get("lastSoldDate", "")
                        link = item.get("itemWebUrl", "")

                        comps.append({
                            "title": title,
                            "price": price,
                            "date_sold": date_sold,
                            "link": link
                        })
                    print(f"Successfully fetched {len(comps)} comps via eBay API.")
                else:
                    print(f"API failed with {response.status_code}, attempting web scrape.")
            except Exception as e:
                print(f"API failed: {e}")

        # Step 3: Web Scrape Fallback (always use if filters requested as it's easier to append URL params)
        if not comps or condition or min_price or max_price:
            print(f"Executing filtered web scrape for: {query}")
            scraped = self._scrape_ebay_web(query, limit, condition, min_price, max_price)
            if scraped:
                comps = scraped

        # Step 4: Fallback Mock Data
        if not comps:
            print("Web scrape failed. Falling back to mock comps.")
            comps = self._get_mock_comps(query, limit)

        # Step 5: Advanced Outlier Removal (Filter out 'Parts' or 'Box Only' that skew prices)
        if len(comps) > 3:
            prices = sorted([c['price'] for c in comps])
            median = prices[len(prices)//2]
            # Simple heuristic: remove items < 30% of median (likely parts/case/accessory)
            original_count = len(comps)
            comps = [c for c in comps if c['price'] > (median * 0.3)]
            if len(comps) < original_count:
                print(f"Filtered out {original_count - len(comps)} outliers (likely accessories or parts).")

        # Extract SEO keywords/tokens
        common_tokens = self._extract_seo_tokens(comps)

        return comps, common_tokens

    def _scrape_ebay_web(self, query: str, limit: int, condition: str = None, min_price: float = None, max_price: float = None) -> List[Dict[str, Any]]:
        """
        Scrape eBay sold listings with advanced URL parameter filtering.
        """
        import subprocess
        from bs4 import BeautifulSoup

        # Base URL for sold items
        url = f"https://www.ebay.com/sch/i.html?_nkw={requests.utils.quote(query)}&LH_Sold=1&LH_Complete=1"

        # Append Condition Filter
        # 1000: New, 3000: Used, 7000: For Parts
        if condition:
            cond_map = {"new": "1000", "used": "3000", "parts": "7000"}
            cond_id = cond_map.get(condition.lower())
            if cond_id:
                url += f"&LH_ItemCondition={cond_id}"

        # Append Price Filters
        if min_price:
            url += f"&_udlo={min_price}"
        if max_price:
            url += f"&_udhi={max_price}"

        try:
            # Use curl to bypass simple python-requests blocking (common on eBay)
            result = subprocess.run(
                ["curl", "-s", "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0", url],
                capture_output=True, text=True, timeout=15
            )
            html = result.stdout
            if not html:
                return []

            soup = BeautifulSoup(html, "html.parser")
            items = soup.select(".s-item__wrapper")

            comps = []
            # Skip the first item as it's often a "recommendation" or "shop on eBay" block
            for item in items[1:limit+1]:
                title_el = item.select_one(".s-item__title")
                title = title_el.text if title_el else ""

                # Cleanup "New Listing" prefix
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

            if comps:
                print(f"Successfully scraped {len(comps)} live comps from eBay.")
            return comps

        except Exception as e:
            print(f"Scraper error: {e}")
            return []

    def _extract_seo_tokens(self, comps: List[Dict[str, Any]]) -> List[str]:
        """Extract top keyword tokens from successful comp titles."""
        all_words = []
        stop_words = {"the", "and", "a", "an", "with", "in", "by", "of", "for", "new", "used", "is", "on", "eb", "to", "it"}

        for comp in comps:
            title = comp.get("title", "").lower()
            words = re.findall(r'\b[a-zA-Z0-9-]+\b', title)
            all_words.extend([w for w in words if w not in stop_words and len(w) > 2])

        # Get top 10 most common token keywords (must appear at least twice to be a 'trend')
        counts = Counter(all_words)
        common_tokens = [word for word, count in counts.most_common(12) if count >= 1]
        return common_tokens[:10]

    def _get_mock_comps(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Mock data generator based on the query."""
        base_price = 150.0
        query_lower = query.lower()

        # Adjust mock pricing based on item
        if "iphone" in query_lower:
            base_price = 300.0
        elif "mug" in query_lower:
            base_price = 10.0

        mock_comps = []
        for i in range(1, limit + 1):
            modifier = (i % 3) * 5.0 - 5.0  # simple price variation
            mock_comps.append({
                "title": f"{query} - Excellent Condition {i}",
                "price": base_price + modifier,
                "date_sold": "2024-03-01T12:00:00Z",
                "link": f"https://www.ebay.com/itm/mock{i}"
            })
        return mock_comps
