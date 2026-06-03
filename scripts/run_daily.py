"""毎日1本投稿するメインスクリプト"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from compose_image import compose
from post_instagram import upload_to_imgbb
from send_line import send_line_image

# 投稿開始日（この日を #01 とする）
START_DATE = date(2026, 6, 3)

HASHTAGS = (
    "#不動産あるある #賃貸あるある #マイホームあるある\n"
    "#不動産 #賃貸 #一人暮らし #マイホーム #住宅購入\n"
    "#引っ越し #新生活 #あるある漫画"
)


def build_caption(story: dict, episode_num: int) -> str:
    return (
        f"不動産あるある #{episode_num:02d}\n"
        f"「{story['title']}」\n\n"
        f"{HASHTAGS}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="不動産あるある 自動生成＆LINE送信")
    parser.add_argument("--test", action="store_true",
                        help="画像生成のみ。LINEへの送信はスキップ")
    parser.add_argument("--episode", type=int, default=None,
                        help="強制的に指定したエピソード番号を使用 (1始まり)")
    args = parser.parse_args()

    stories = json.loads((ROOT / "content" / "stories.json").read_text(encoding="utf-8"))

    # エピソード番号を決定
    if args.episode is not None:
        episode_num = args.episode
    else:
        days = (date.today() - START_DATE).days
        if days < 0:
            print(f"開始日 {START_DATE} まで待機中です。")
            return
        episode_num = days + 1

    idx   = (episode_num - 1) % len(stories)
    story = stories[idx]

    print(f"📅 今日のエピソード: #{episode_num:02d}「{story['title']}」({story['category']})")

    # 画像生成
    image_path = compose(story, episode_num)
    print(f"🖼  画像生成完了: {image_path}")

    if args.test:
        print("✅ テストモード: 送信をスキップしました。")
        return

    # imgbbにアップロード → LINE送信
    import os
    print("📤 imgbbに画像をアップロード中...")
    image_url = upload_to_imgbb(image_path, os.environ["IMGBB_API_KEY"])
    print(f"   URL: {image_url}")

    caption = build_caption(story, episode_num)
    send_line_image(image_url, caption)


if __name__ == "__main__":
    main()
