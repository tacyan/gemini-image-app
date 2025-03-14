import os
import base64
import shutil
import logging
from pathlib import Path
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("utils")

# 静的ファイルディレクトリの作成
def create_static_directories():
    """
    アプリケーションに必要なディレクトリを作成する
    
    静的ファイル用、一時ファイル用のディレクトリを作成します。
    """
    directories = [
        "static/css",
        "static/js",
        "static/images",
        "temp",
        "temp_images"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"ディレクトリを作成しました: {directory}")

# LocalStorageとStreamlitを連携するためのHTML/JSコード
def get_localstorage_component():
    """
    LocalStorageとStreamlitを連携するためのJavaScriptコンポーネントを返す
    
    Returns:
        str: HTML/JavaScriptコード
    """
    js_path = os.path.join("static", "js", "localstorage.js")
    
    # JavaScriptファイルが存在しない場合は組み込みのJavaScriptを返す
    if not os.path.exists(js_path):
        logger.info("localstorage.jsが見つからないため、組み込みのJavaScriptを使用します")
        return """
        <div id="localstorage-bridge" style="display:none;">
            <script>
                // LocalStorageとStreamlitの連携用JavaScript
                // 会話履歴の保存と読み込み機能
                const sendMessageToStreamlit = (type, data = {}) => {
                    const message = {
                        type: type,
                        ...data
                    };
                    window.parent.postMessage(message, '*');
                };

                // LocalStorageからの会話履歴の読み込み
                const loadConversationFromStorage = () => {
                    try {
                        const data = localStorage.getItem('geminiConversation');
                        return data ? JSON.parse(data) : [];
                    } catch (e) {
                        console.error('LocalStorageからの読み込みエラー:', e);
                        return [];
                    }
                };

                // 初期化時に会話履歴を読み込んでStreamlitに送信
                document.addEventListener('DOMContentLoaded', () => {
                    const conversation = loadConversationFromStorage();
                    sendMessageToStreamlit('INIT_CONVERSATION', { conversation });
                });
            </script>
        </div>
        """
    
    # JavaScriptファイルの内容を読み込む（UTF-8エンコーディングを指定）
    try:
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
        
        # HTML/JSコンポーネントを返す
        return f"""
        <div id="localstorage-bridge" style="display:none;">
            <script>
                {js_content}
            </script>
        </div>
        """
    except Exception as e:
        logger.error(f"JavaScriptファイルの読み込み中にエラーが発生しました: {str(e)}")
        return "<div>LocalStorage連携機能の読み込みに失敗しました</div>"

# Base64エンコードされた画像をデコードして一時ファイルに保存
def save_base64_image(base64_data, filename):
    """
    Base64エンコードされた画像データを一時ファイルとして保存する
    
    Args:
        base64_data (str): Base64エンコードされた画像データ
        filename (str): 保存するファイル名
        
    Returns:
        str: 保存されたファイルのパス、または失敗した場合はNone
    """
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # ファイル名に日時を追加してユニークにする
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(temp_dir, safe_filename)
    
    try:
        # Base64データのヘッダー部分を削除（存在する場合）
        if "," in base64_data:
            base64_data = base64_data.split(",")[1]
            
        image_data = base64.b64decode(base64_data)
        with open(file_path, "wb") as f:
            f.write(image_data)
        logger.info(f"画像を保存しました: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"画像の保存中にエラーが発生しました: {str(e)}")
        return None

# アップロードされた画像を保存する
def save_uploaded_image(image_data, filename):
    """
    アップロードされた画像データを一時ディレクトリに保存する
    
    Args:
        image_data (bytes): 画像のバイナリデータ
        filename (str): ファイル名
        
    Returns:
        str: 保存されたファイルのパス
    """
    temp_dir = "temp_images"
    os.makedirs(temp_dir, exist_ok=True)
    
    # ファイル名に日時を追加してユニークにする
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(temp_dir, safe_filename)
    
    try:
        with open(file_path, "wb") as f:
            f.write(image_data)
        logger.info(f"アップロード画像を保存しました: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"画像の保存中にエラーが発生しました: {str(e)}")
        return None

# 一時ファイルをクリーンアップ
def cleanup_temp_files(max_age_hours=24):
    """
    一時ファイルをクリーンアップする
    
    指定した時間より古い一時ファイルを削除します。
    
    Args:
        max_age_hours (int): ファイルを保持する最大時間（時間単位）
    """
    temp_dirs = ["temp", "temp_images"]
    current_time = datetime.now()
    
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            logger.info(f"{temp_dir}ディレクトリのクリーンアップを開始します")
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                try:
                    if os.path.isfile(file_path):
                        # ファイルの最終更新時刻を取得
                        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                        age_hours = (current_time - file_mtime).total_seconds() / 3600
                        
                        # 指定した時間より古いファイルを削除
                        if age_hours > max_age_hours:
                            os.unlink(file_path)
                            logger.info(f"古いファイルを削除しました: {file_path}")
                except Exception as e:
                    logger.error(f"ファイルの削除中にエラーが発生しました: {str(e)}")
    
    logger.info("一時ファイルのクリーンアップが完了しました")
