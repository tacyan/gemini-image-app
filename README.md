# Gemini AI チャットアプリケーション

Google Geminiを使用した多機能チャットアプリケーションです。テキストだけでなく、画像のアップロードにも対応し、画像に関する質問や分析も可能です。

## 特徴

- 🤖 Google Gemini 1.5 Flash APIを使用した高性能AI会話
- 🖼️ 画像のアップロードと分析に対応
- 💾 ブラウザのLocalStorageを利用した会話履歴の保存
- 🔒 安全なAPIキー管理
- 📱 レスポンシブデザイン

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/tacyan/gemini-image-app.git
cd gemini-image-app
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. Google Gemini APIキーの設定

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセスしてAPIキーを取得します
2. `.env.example` ファイルを `.env` にコピーします

```bash
cp .env.example .env
```

3. `.env` ファイルを編集し、実際のAPIキーを設定します

```
GEMINI_API_KEY=あなたのAPIキー
```

### 4. アプリケーションの起動

```bash
streamlit run app.py
```

## 使用方法

1. ブラウザで `http://localhost:8501` にアクセスします
2. サイドバーでAPIキーを設定します（初回のみ）
3. 画像をアップロードするには、上部の「画像のアップロード」セクションを使用します
4. テキスト入力欄に質問を入力し、送信します
5. 画像について質問する場合は、画像をアップロードしてから質問します

## 主要ファイル

- `app.py`: メインアプリケーションファイル
- `gemini_api.py`: Gemini APIとの通信を処理するクラス
- `utils.py`: ユーティリティ関数
- `.env`: 環境変数（APIキーなど）
- `requirements.txt`: 依存パッケージリスト

## セキュリティ注意事項

- APIキーは `.env` ファイルに保存し、Gitリポジトリにコミットしないでください
- `.gitignore` ファイルに `.env` が含まれていることを確認してください
- 公開サーバーにデプロイする場合は、適切なセキュリティ対策を講じてください

## ライセンス

MITライセンス

## 作者

あなたの名前

## 謝辞

- [Google Gemini API](https://ai.google.dev/)
- [Streamlit](https://streamlit.io/)
