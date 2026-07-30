import os
import httpx
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Create a FastMCP server
mcp = FastMCP("QuickCommerce")

# QuickCommerce API Base URL
BASE_URL = "https://api.quickcommerceapi.com"

def get_api_key() -> str:
    api_key = os.environ.get("QUICKCOMMERCE_API_KEY")
    if not api_key:
        raise ValueError("QUICKCOMMERCE_API_KEY environment variable is not set")
    return api_key

@mcp.tool()
def search_quickcommerce(q: str, lat: float, lon: float, platforms: str = "BlinkIt,Zepto,Swiggy", pincode: Optional[str] = None) -> dict:
    """
    Search products across multiple quick commerce platforms in India (e.g., BlinkIt, Zepto, Swiggy Instamart).
    
    Args:
        q: The search query (e.g. "milk", "bread").
        lat: Latitude of the delivery location (e.g. 12.9716).
        lon: Longitude of the delivery location (e.g. 77.5946).
        platforms: Comma-separated list of platforms to search (e.g. "BlinkIt,Zepto,Swiggy").
        pincode: Pincode (required if searching on DMart, JioMart, or Minutes).
    """
    params = {
        "q": q,
        "lat": lat,
        "lon": lon,
        "platforms": platforms
    }
    if pincode:
        params["pincode"] = pincode
        
    headers = {"X-API-Key": get_api_key()}
    
    with httpx.Client(verify=False) as client:
        response = client.get(f"{BASE_URL}/v1/groupsearch", params=params, headers=headers)
        response.raise_for_status()
        return response.json()

@mcp.tool()
def compare_quickcommerce(product_id: str) -> dict:
    """
    Compare prices for a specific product ID across platforms.
    
    Args:
        product_id: The ID of the product returned by a previous search.
    """
    headers = {"X-API-Key": get_api_key()}
    
    with httpx.Client(verify=False) as client:
        response = client.get(f"{BASE_URL}/v1/compare", params={"product_id": product_id}, headers=headers)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    # Start the stdio server
    mcp.run()
