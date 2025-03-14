import os
import base64
import mimetypes
import time
import google.generativeai as genai
from google.generativeai import types
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv
from PIL import Image
from io import BytesIO
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import pathlib

# .envファイルから環境変数を読み込む
load_dotenv()

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("gemini_api")

# Gemini APIキーを環境変数から取得
api_key = os.getenv("GEMINI_API_KEY", "")

# APIキーの状態をチェック
if not api_key:
    logger.warning("⚠️ APIキーが設定されていません。.envファイルまたは環境変数を確認してください。")
elif len(api_key) < 30:  # 最小の長さをチェック
    logger.warning(f"⚠️ APIキーが短すぎる可能性があります。正しいGemini APIキーであることを確認してください。")
else:
    # APIキーの先頭と末尾のみを安全に表示
    masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) >= 8 else "****"
    logger.info(f"APIキーが読み込まれました: {masked_key}")

# Gemini APIの設定
genai.configure(api_key=api_key)

class GeminiAPI:
    """
    Gemini APIを利用するためのクラス
    
    このクラスはGoogle Generative AIのGeminiモデルとの通信を処理します。
    画像と文章を含むマルチモーダルなプロンプトを処理できます。
    
    Attributes:
        model_name (str): 使用するGeminiモデルの名前
        generation_config (dict): レスポンス生成の設定
        safety_settings (dict): コンテンツ安全性のフィルタリング設定
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """
        GeminiAPIクラスの初期化
        
        Args:
            model_name (str): 使用するGeminiモデルの名前（デフォルト: "gemini-1.5-flash"）
        """
        # APIキーを環境変数から取得
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        
        # APIキーの検証
        if not self.api_key:
            logger.warning("⚠️ Gemini APIキーが設定されていません。各種機能が動作しません。")
            print("⚠️ Gemini APIキーが設定されていません。Streamlitサイドバーで設定してください。")
        elif len(self.api_key) < 30:  # 一般的なGoogleのAPIキーは39文字程度
            # APIキーの最初の4文字と最後の4文字を表示（セキュリティのため）
            masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "[不正なキー]"
            logger.warning(f"⚠️ APIキーが短すぎる可能性があります: {masked_key}")
            print(f"⚠️ APIキーが短すぎる可能性があります: {masked_key}")
        else:
            # APIキーの最初の4文字と最後の4文字を表示（セキュリティのため）
            masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}"
            logger.info(f"APIキーが設定されています: {masked_key}")
        
        # Google Generative AI の設定
        genai.configure(api_key=self.api_key)
        
        # モデル設定
        self.model_name = model_name
        
        # 生成設定
        self.generation_config = {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        # 安全性設定
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # クライアント初期化（再試行ロジック付き）
        self.model = None
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                break
            except Exception as e:
                logger.error(f"モデル初期化エラー（試行 {attempt+1}/{max_retries}）: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数バックオフ
                else:
                    logger.error(f"Geminiモデルの初期化に失敗しました: {str(e)}")
                    print(f"⚠️ Geminiモデルの初期化に失敗しました: {str(e)}")
        
    def generate_content(self, prompt, response_modalities=None, image_data=None, mime_type=None):
        """
        Gemini APIを使用してコンテンツを生成する
        
        Args:
            prompt (str): 生成のための入力テキスト
            response_modalities (list, optional): 応答のモダリティリスト
            image_data (bytes, optional): 画像データ（画像を含む場合）
            mime_type (str, optional): 画像のMIMEタイプ
            
        Returns:
            str: 生成されたテキスト
            
        Raises:
            Exception: API呼び出し中にエラーが発生した場合
        """
        # APIキーが設定されているか確認
        if not self.api_key:
            error_msg = "APIキーが設定されていません。Streamlitサイドバーで有効なAPIキーを設定してください。"
            logger.error(error_msg)
            return {"error": error_msg}
            
        # モデルが正しく初期化されているか確認
        if self.model is None:
            error_msg = "Geminiモデルが初期化されていません。APIキーを確認してください。"
            logger.error(error_msg)
            return {"error": error_msg}
        
        generation_config = {
            "temperature": 0.9,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        retry_count = 0
        max_retries = 3
        retry_delay = 1  # 初期リトライ待機時間（秒）
        
        while retry_count < max_retries:
            try:
                if image_data:
                    # MIMEタイプが指定されていなければ、推測を試みる
                    if not mime_type:
                        detected_mime_type = self.detect_mime_type(image_data)
                        mime_type = detected_mime_type if detected_mime_type else "image/jpeg"
                    
                    # 画像とテキストを含むマルチモーダルプロンプト
                    multimodal_prompt = [
                        {
                            "role": "user",
                            "parts": [
                                {"mime_type": mime_type, "data": image_data},
                                {"text": prompt}
                            ]
                        }
                    ]
                    
                    response = self.model.generate_content(
                        contents=multimodal_prompt,
                        generation_config=generation_config
                    )
                else:
                    # テキストのみのプロンプト
                    response = self.model.generate_content(
                        contents=prompt,
                        generation_config=generation_config
                    )
                
                return response.text
                
            except Exception as e:
                error_str = str(e)
                logger.error(f"Gemini API呼び出しエラー: {error_str}")
                
                # エラーの種類に基づいた処理
                if "API_KEY_INVALID" in error_str:
                    error_msg = "APIキーが無効です。Google AI Studioで新しいAPIキーを取得し、正しく設定してください。"
                    logger.error(error_msg)
                    return {"error": error_msg}
                elif "API key not found" in error_str or "API key not valid" in error_str:
                    error_msg = "APIキーが見つからないか無効です。APIキーが正しく設定されているか確認してください。"
                    logger.error(error_msg)
                    return {"error": error_msg}
                elif "PERMISSION_DENIED" in error_str:
                    error_msg = "APIキーの権限が不足しています。Google AI Studioでキーの権限を確認してください。"
                    logger.error(error_msg)
                    return {"error": error_msg}
                elif "RESOURCE_EXHAUSTED" in error_str:
                    error_msg = "APIキーの利用制限に達しました。しばらく待つか、別のAPIキーを使用してください。"
                    logger.error(error_msg)
                    return {"error": error_msg}
                elif "UNAVAILABLE" in error_str or "DEADLINE_EXCEEDED" in error_str:
                    # 一時的なエラーの場合はリトライ
                    retry_count += 1
                    if retry_count < max_retries:
                        logger.info(f"一時的なエラー、{retry_delay}秒後に再試行します（{retry_count}/{max_retries}）")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # 指数バックオフ
                    else:
                        error_msg = "サービスが一時的に利用できません。しばらくしてから再度お試しください。"
                        logger.error(error_msg)
                        return {"error": error_msg}
                else:
                    # その他のエラー
                    error_msg = f"Gemini APIでエラーが発生しました: {error_str}"
                    logger.error(error_msg)
                    return {"error": error_msg}
        
        error_msg = "最大リトライ回数に達しました。しばらくしてから再度お試しください。"
        logger.error(error_msg)
        return {"error": error_msg}
    
    def detect_mime_type(self, image_data):
        """
        画像データからMIMEタイプを検出します
        
        Args:
            image_data (bytes): 画像のバイナリデータ
            
        Returns:
            str: 検出されたMIMEタイプ、または検出できない場合はNone
        """
        try:
            # PILを使用して画像フォーマットを検出
            image = Image.open(BytesIO(image_data))
            if image.format:
                return f"image/{image.format.lower()}"
            
            # mimetypesモジュールで試行
            mime_type, _ = mimetypes.guess_type("dummy." + image.format.lower()) if image.format else (None, None)
            if mime_type:
                return mime_type
                
            return "image/jpeg"  # デフォルト
        except Exception as e:
            logger.error(f"MIMEタイプ検出エラー: {str(e)}")
            return None

    def generate_with_image(self, prompt, image_path, response_modalities=None):
        """
        画像とプロンプトを使用してGemini APIからコンテンツを生成します
        
        Args:
            prompt (str): テキストプロンプト
            image_path (str): 画像ファイルのパス
            response_modalities (list, optional): 応答のモダリティリスト
            
        Returns:
            dict: 生成されたレスポンス（テキストまたはエラー情報）
        """
        try:
            # 画像ファイルが存在するか確認
            if not os.path.exists(image_path):
                error_msg = f"画像ファイルが見つかりません: {image_path}"
                logger.error(error_msg)
                return {"error": error_msg}
                
            # 画像ファイルを読み込む
            with open(image_path, "rb") as f:
                image_data = f.read()
                
            # MIMEタイプを推測
            mime_type = self.detect_mime_type(image_data)
            
            # Gemini APIにリクエストを送信
            return self.generate_content(prompt, response_modalities, image_data, mime_type)
            
        except Exception as e:
            error_msg = f"画像処理中にエラーが発生しました: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def is_api_key_valid(self):
        """
        APIキーが有効かどうかを確認します
        
        Returns:
            bool: APIキーが有効な場合はTrue、そうでない場合はFalse
        """
        if not self.api_key or len(self.api_key) < 30:
            return False
            
        try:
            # 簡単なテストリクエストを送信
            response = self.generate_content("こんにちは")
            return not isinstance(response, dict) or not response.get("error")
        except Exception as e:
            logger.error(f"APIキー検証エラー: {str(e)}")
            return False
    
    def image_to_base64(self, image_path):
        """
        画像ファイルをBase64エンコードする
        
        Args:
            image_path (str): 画像ファイルのパス
        
        Returns:
            str: Base64エンコードされた画像データ
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def base64_to_image(self, base64_data):
        """
        Base64エンコードされたデータをPIL Imageに変換する
        
        Args:
            base64_data (str): Base64エンコードされた画像データ
        
        Returns:
            PIL.Image: 画像オブジェクト
        """
        image_data = base64.b64decode(base64_data)
        return Image.open(BytesIO(image_data))
    
    def save_image(self, base64_data, output_path):
        """
        Base64エンコードされた画像データをファイルに保存する
        
        Args:
            base64_data (str): Base64エンコードされた画像データ
            output_path (str): 出力ファイルパス
        
        Returns:
            bool: 保存が成功したかどうか
        """
        try:
            image = self.base64_to_image(base64_data)
            image.save(output_path)
            return True
        except Exception as e:
            print(f"画像の保存中にエラーが発生しました: {e}")
            return False
