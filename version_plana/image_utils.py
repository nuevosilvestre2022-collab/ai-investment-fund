import os
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent
IMG_CACHE_DIR = BASE_DIR / "output" / "cache" / "images"
IMG_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def download_context_image(keyword: str, width: int = 800, height: int = 400) -> str:
    """
    Downloads a contextual image for the PDF report.
    Tries loremflickr with the keyword. If it fails, uses picsum photos.
    Returns the absolute local path to the cached image.
    """
    safe_kw = keyword.replace(" ", ",").lower()
    # Cache key
    filepath = IMG_CACHE_DIR / f"img_{safe_kw}_{width}x{height}_{int(time.time())}.jpg"
    
    url = f"https://loremflickr.com/{width}/{height}/{safe_kw}"
    
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(res.content)
            return str(filepath)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        
    # Fallback
    fallback_url = f"https://picsum.photos/{width}/{height}?random={int(time.time())}"
    try:
        res = requests.get(fallback_url, timeout=5)
        if res.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(res.content)
            return str(filepath)
    except:
        pass
        
    return ""  # If both fail
