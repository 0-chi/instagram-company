"""いらすとやから画像を検索・ダウンロードする"""
import re
import time
import hashlib
import requests
from pathlib import Path
from bs4 import BeautifulSoup

CACHE_DIR = Path("/tmp/irasutoya")
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def fetch(keyword: str) -> Path | None:
    """キーワードでいらすとやを検索し、画像のPathを返す。失敗時はNone。"""
    CACHE_DIR.mkdir(exist_ok=True)
    cache_path = CACHE_DIR / f"{hashlib.md5(keyword.encode()).hexdigest()}.png"
    if cache_path.exists():
        return cache_path

    try:
        url = f"https://www.irasutoya.com/search?q={requests.utils.quote(keyword)}"
        resp = requests.get(url, headers=_HEADERS, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        img_url = None
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if "bp.blogspot.com" in src or "googleusercontent.com" in src:
                img_url = re.sub(r"/s\d+(-c)?/", "/s600/", src)
                break

        if not img_url:
            print(f"⚠️  画像が見つかりませんでした: [{keyword}]")
            return None

        time.sleep(0.5)
        img_resp = requests.get(
            img_url,
            headers={**_HEADERS, "Referer": "https://www.irasutoya.com/"},
            timeout=30,
        )
        img_resp.raise_for_status()
        cache_path.write_bytes(img_resp.content)
        return cache_path

    except Exception as e:
        print(f"⚠️  いらすとや取得失敗 [{keyword}]: {e}")
        return None
