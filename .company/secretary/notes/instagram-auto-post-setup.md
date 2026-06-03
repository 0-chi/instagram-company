---
created: "2026-06-03"
topic: "Instagram自動投稿システム セットアップ手順"
type: note
tags: [instagram, setup, github-actions]
---

# Instagram自動投稿システム セットアップ手順

## システム概要

```
GitHub Actions (毎朝JST9時)
  → stories.jsonから今日の台本を選択
  → いらすとや画像 + テキストで4コマ画像生成
  → imgbbに画像アップロード
  → Instagram Graph APIで投稿
```

---

## STEP 1: Instagramアカウントをビジネス/クリエイターに切り替え

1. Instagramアプリ → プロフィール → ≡メニュー → 設定とアクティビティ
2. 「アカウントの種類とツール」→「プロアカウントに切り替える」
3. 「クリエイター」または「ビジネス」を選択

---

## STEP 2: FacebookページとDeveloper Appを作成

### 2-1. Facebookページを作成（持っていない場合）
- https://www.facebook.com/pages/create からページを作成

### 2-2. InstagramとFacebookページを連携
- Instagramアプリ → プロフィール → プロフィールを編集
  → 「プロフィール情報」→「Facebookページをリンク」

### 2-3. Facebook Developer Appを作成
1. https://developers.facebook.com/apps/ にアクセス
2. 「アプリを作成」→「その他」→「ビジネス」を選択
3. アプリ名を入力して作成

### 2-4. Instagram Graph APIを有効化
1. 作成したアプリのダッシュボード
2. 「製品を追加」→「Instagram Graph API」→「設定」
3. 「Instagram基本表示」も追加

### 2-5. アクセストークンを取得
1. https://developers.facebook.com/tools/explorer/
2. 「Graph APIエクスプローラー」でアプリを選択
3. 「ユーザートークンを生成」→ 権限: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
4. 「長期トークンに変換」（有効期限60日）

### 2-6. Instagram User IDを確認
```
GET https://graph.instagram.com/me?fields=id,username&access_token=YOUR_TOKEN
```
→ レスポンスの `id` が INSTAGRAM_USER_ID

---

## STEP 3: imgbbのAPIキーを取得

1. https://imgbb.com/ でアカウント作成
2. https://api.imgbb.com/ → APIキーを取得（無料）

---

## STEP 4: いらすとや画像をダウンロード

`images/image_map.json` に記載のキー名で画像を保存:

```
images/irasutoya/
  happy_person.png      ← 笑顔の人
  shocked_person.png    ← 驚いた人
  sad_person.png        ← 悲しんでいる人
  ...（image_map.json 参照）
```

ダウンロード先: https://www.irasutoya.com/

---

## STEP 5: GitHubにリポジトリを作成してプッシュ

```bash
cd instagram-company
git init
git add .
git commit -m "初期コミット"
# GitHubで新規リポジトリ作成後:
git remote add origin https://github.com/YOUR_USERNAME/instagram-company.git
git push -u origin main
```

---

## STEP 6: GitHub Secretsを登録

リポジトリの「Settings」→「Secrets and variables」→「Actions」→「New repository secret」

| シークレット名 | 値 |
|---|---|
| `INSTAGRAM_USER_ID` | STEP 2-6 で取得したID |
| `INSTAGRAM_ACCESS_TOKEN` | STEP 2-5 で取得したトークン |
| `IMGBB_API_KEY` | STEP 3 で取得したキー |

---

## STEP 7: 動作確認

GitHub → Actions → 「不動産あるある 毎日自動投稿」→「Run workflow」
- `test_mode: true` で画像だけ生成（Artifactsでダウンロード確認）
- `test_mode: false` で実際に投稿

---

## アクセストークンの更新（60日ごと）

Instagram アクセストークンは60日で期限切れになります。
期限前に以下で更新:

```
GET https://graph.instagram.com/refresh_access_token
  ?grant_type=ig_refresh_token
  &access_token=YOUR_CURRENT_TOKEN
```

→ GitHub Secrets の `INSTAGRAM_ACCESS_TOKEN` を新しいトークンに更新

---

## ネクストアクション
- [ ] STEP 1: IGアカウント切り替え
- [ ] STEP 2: FB Developer App作成＋トークン取得
- [ ] STEP 3: imgbb APIキー取得
- [ ] STEP 4: いらすとや画像15枚ダウンロード
- [ ] STEP 5: GitHubリポジトリ作成＋プッシュ
- [ ] STEP 6: Secrets登録
- [ ] STEP 7: テスト実行
