"""imgbb + Instagram Graph API で画像を投稿する"""
import base64
import os
import time
import requests


# ── imgbb アップロード ──────────────────────────────────────
def upload_to_imgbb(image_path: str, api_key: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    resp = requests.post(
        "https://api.imgbb.com/1/upload",
        data={"key": api_key, "image": b64},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"imgbb upload failed: {data}")
    return data["data"]["url"]


# ── Instagram Graph API ───────────────────────────────────
def _ig_post(url: str, **params) -> dict:
    resp = requests.post(url, params=params, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Instagram API error {resp.status_code}: {resp.text}")
    return resp.json()


def create_media_container(ig_user_id: str, access_token: str,
                            image_url: str, caption: str) -> str:
    data = _ig_post(
        f"https://graph.instagram.com/v21.0/{ig_user_id}/media",
        image_url=image_url,
        caption=caption,
        access_token=access_token,
    )
    return data["id"]


def publish_container(ig_user_id: str, access_token: str, creation_id: str) -> str:
    data = _ig_post(
        f"https://graph.instagram.com/v21.0/{ig_user_id}/media_publish",
        creation_id=creation_id,
        access_token=access_token,
    )
    return data["id"]


# ── メイン関数 ────────────────────────────────────────────
def post_to_instagram(image_path: str, caption: str) -> str:
    """
    1. imgbb に画像をアップロード
    2. Instagram メディアコンテナを作成
    3. 公開 → media_id を返す
    """
    ig_user_id   = os.environ["INSTAGRAM_USER_ID"]
    access_token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
    imgbb_key    = os.environ["IMGBB_API_KEY"]

    print("📤 imgbb に画像をアップロード中...")
    image_url = upload_to_imgbb(image_path, imgbb_key)
    print(f"   URL: {image_url}")

    print("📦 Instagram コンテナを作成中...")
    creation_id = create_media_container(ig_user_id, access_token, image_url, caption)

    # Instagram はコンテナ生成後、数秒の処理待ちが必要な場合がある
    time.sleep(3)

    print("🚀 Instagram に公開中...")
    media_id = publish_container(ig_user_id, access_token, creation_id)
    print(f"   ✅ 公開完了! media_id={media_id}")

    return media_id
