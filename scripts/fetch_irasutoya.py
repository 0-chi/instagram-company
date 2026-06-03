"""いらすとやから画像を検索・ダウンロードする（Blogger API使用）"""
import re
import hashlib
import shutil
import requests
from pathlib import Path

CACHE_DIR = Path("/tmp/irasutoya")
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}
_API_BASE = "https://www.irasutoya.com/feeds/posts/default"


def _is_real_illustration(url: str) -> bool:
    filename = url.split("/")[-1].split("\\")[0]
    if filename.startswith("thumbnail_"):
        return False
    if any(x in filename for x in ["banner", "button", "logo", "navi", "pyoko", "searchbtn"]):
        return False
    return True


def _search_one(keyword: str) -> Path | None:
    """1キーワードで検索してダウンロード。キャッシュあれば即返す。"""
    cache_path = CACHE_DIR / f"{hashlib.md5(keyword.encode()).hexdigest()}.png"
    if cache_path.exists():
        return cache_path

    try:
        resp = requests.get(
            _API_BASE,
            params={"q": keyword, "max-results": 20, "alt": "json"},
            headers=_HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        entries = data.get("feed", {}).get("entry", [])
        if not entries:
            return None

        img_url = None
        for entry in entries:
            thumb = entry.get("media$thumbnail", {})
            url = thumb.get("url", "")
            if url and _is_real_illustration(url):
                img_url = re.sub(r"/s\d+-c/", "/s600/", url)
                break

        if not img_url:
            return None

        img_resp = requests.get(
            img_url,
            headers={**_HEADERS, "Referer": "https://www.irasutoya.com/"},
            timeout=30,
        )
        img_resp.raise_for_status()
        cache_path.write_bytes(img_resp.content)
        return cache_path

    except Exception:
        return None


def fetch(keyword: str) -> Path | None:
    """キーワードで検索。ヒットしなければ単語を減らして再試行する。"""
    CACHE_DIR.mkdir(exist_ok=True)

    # 元のキーワードそのままでキャッシュを確認
    final_cache = CACHE_DIR / f"{hashlib.md5(keyword.encode()).hexdigest()}.png"
    if final_cache.exists():
        return final_cache

    words = keyword.split()
    for n in range(len(words), 0, -1):
        search = " ".join(words[:n])
        result = _search_one(search)
        if result:
            if result != final_cache:
                shutil.copy(result, final_cache)
            print(f"✅ いらすとや取得: [{search}]")
            return final_cache

    print(f"⚠️  いらすとや取得失敗: [{keyword}]")
    return None
