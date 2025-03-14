import os
import json
import time
import re
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components
from gemini_api import GeminiAPI
from utils import create_static_directories, get_localstorage_component, save_base64_image, cleanup_temp_files, save_uploaded_image

# 環境変数の読み込み
load_dotenv()

# 静的ディレクトリの作成
create_static_directories()

# ページ設定
st.set_page_config(
    page_title="Gemini AI イメージ変換アプリ",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSSスタイルの適用
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .conversation-container {
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .user-message {
        background-color: #f0f2f6;
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 8px;
    }
    .ai-message {
        background-color: #e1f5fe;
        padding: 10px 15px;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    .image-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .image-container img {
        border-radius: 8px;
        max-width: 100%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .thumbnail-container {
        max-width: 300px;
        margin: 10px 0;
        padding: 8px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .thumbnail-container:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    .thumbnail-caption {
        text-align: center;
        font-size: 0.9em;
        color: #666;
        margin-top: 5px;
    }
    /* モバイル対応 */
    @media (max-width: 768px) {
        .thumbnail-container {
            max-width: 250px;
        }
    }
    .uploaded-image {
        max-width: 500px;
        margin-bottom: 15px;
    }
    .uploaded-image img {
        border-radius: 6px;
        max-width: 100%;
    }
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 20px;
        padding: 10px 24px;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    .stButton button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .stTextInput input {
        border-radius: 20px;
        border: 1px solid #ddd;
        padding: 10px 15px;
    }
    .stTextArea textarea {
        border-radius: 15px;
        border: 1px solid #ddd;
        padding: 10px 15px;
    }
    /* チャットフォームのスタイル改善 */
    .chat-form {
        margin-top: 20px;
        display: flex;
        flex-direction: column;
    }
    .chat-input {
        border-radius: 20px !important;
        border: 1px solid #ddd !important;
        padding: 12px 15px !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05) !important;
    }
    .send-button {
        border-radius: 20px !important;
        background-color: #4CAF50 !important;
        color: white !important;
        font-weight: bold !important;
        transition: all 0.3s !important;
    }
    .send-button:hover {
        background-color: #45a049 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
    }
    .image-transformation-container {
        margin-top: 20px;
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #e0e0e0;
    }
    .transformation-option {
        padding: 10px;
        margin: 5px 0;
        background-color: white;
        border-radius: 8px;
        border: 1px solid #eee;
        cursor: pointer;
        transition: all 0.2s;
    }
    .transformation-option:hover {
        background-color: #f0f7ff;
        border-color: #b8d8ff;
    }
    .transformation-option.selected {
        background-color: #e6f4ff;
        border-color: #1890ff;
        font-weight: bold;
    }
    .style-option-label {
        font-weight: bold;
        margin-bottom: 5px;
        color: #333;
    }
    .storage-info {
        font-size: 0.8em;
        color: #666;
        margin-top: 10px;
    }
    .download-button {
        display: inline-block;
        background-color: #4CAF50;
        color: white;
        padding: 5px 10px;
        border-radius: 5px;
        text-decoration: none;
        font-size: 0.8em;
        margin-top: 5px;
    }
    .download-button:hover {
        background-color: #45a049;
    }
    .stAlert {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .stFileUploader {
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .stImage {
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .before-after-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin: 20px 0;
    }
    .image-card {
        flex: 1;
        min-width: 300px;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 3px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
    .image-card-header {
        padding: 10px;
        background-color: #f0f2f6;
        font-weight: bold;
        text-align: center;
        border-bottom: 1px solid #e0e0e0;
    }
    .image-card-body {
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# LocalStorageコンポーネントの挿入
components.html(get_localstorage_component(), height=0)

# LocalStorageとの通信用JavaScript
st.markdown("""
<script>
// Streamlitとの通信
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

// LocalStorageへの会話履歴の保存
const saveConversationToStorage = (conversation) => {
    try {
        localStorage.setItem('geminiConversation', JSON.stringify(conversation));
    } catch (e) {
        console.error('LocalStorageへの保存エラー:', e);
    }
};

// 会話履歴のクリア
const clearConversationStorage = () => {
    try {
        localStorage.removeItem('geminiConversation');
    } catch (e) {
        console.error('LocalStorageのクリアエラー:', e);
    }
};

// Streamlitからのメッセージ受信
window.addEventListener('message', (e) => {
    if (e.data.type === 'GET_CONVERSATION') {
        const conversation = loadConversationFromStorage();
        sendMessageToStreamlit('CONVERSATION_DATA', { conversation });
    } else if (e.data.type === 'SAVE_CONVERSATION' && e.data.conversation) {
        saveConversationToStorage(e.data.conversation);
    } else if (e.data.type === 'CLEAR_CONVERSATION') {
        clearConversationStorage();
    }
});

// 初期化時に会話履歴を読み込んでStreamlitに送信
document.addEventListener('DOMContentLoaded', () => {
    const conversation = loadConversationFromStorage();
    sendMessageToStreamlit('INIT_CONVERSATION', { conversation });
});
</script>
""", unsafe_allow_html=True)

# アプリの初期化
def startup():
    """
    アプリケーションの起動時に必要な初期化を行う
    
    会話履歴の初期化、環境変数の読み込み、APIキーの検証などを行います。
    """
    # メッセージの初期化
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "system",
                "content": "👋 こんにちは！画像をアップロードして、Gemini AIによる画像変換を体験してください。テキストチャットも可能です。",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
        ]
    
    # Geminiインスタンスの初期化
    if "gemini_instance" not in st.session_state:
        st.session_state.gemini_instance = None
        
    # 画像変換モードの初期化
    if "image_mode" not in st.session_state:
        st.session_state.image_mode = False

# APIキーを確認して有効なGeminiインスタンスを取得する関数
def get_valid_gemini_instance():
    """
    APIキーを確認して有効なGeminiインスタンスを返す
    
    Returns:
        GeminiAPI: 有効なAPIキーで初期化されたGeminiインスタンス
        または、None（APIキーが無効な場合）とエラーメッセージ
    """
    # セッションに保存されているAPIキーを取得
    current_api_key = os.getenv("GEMINI_API_KEY", "")
    
    # セッションストレージにあるGeminiインスタンスを取得
    gemini_instance = st.session_state.get("gemini_instance")
    
    # Geminiインスタンスが存在するか、または保存されているAPIキーが変更されたか確認
    if gemini_instance is None or gemini_instance.api_key != current_api_key:
        # Geminiインスタンスを再作成
        gemini_instance = GeminiAPI()
        st.session_state["gemini_instance"] = gemini_instance
        
        # APIキーの検証
        if not gemini_instance.is_api_key_valid():
            if not current_api_key:
                return None, "APIキーが設定されていません。左サイドバーで有効なAPIキーを設定してください。"
            else:
                masked_key = f"{current_api_key[:4]}...{current_api_key[-4:]}" if len(current_api_key) > 8 else "[短すぎるキー]"
                return None, f"APIキー（{masked_key}）が無効です。正しいAPIキーを入力してください。"
    
    return gemini_instance, None

# メッセージを処理する関数
def process_message(user_input, image_data=None, image_path=None):
    """
    ユーザー入力を処理してGeminiからの応答を取得
    
    Args:
        user_input (str): ユーザーの入力テキスト
        image_data (bytes, optional): 画像データ（バイナリ）
        image_path (str, optional): 画像ファイルのパス
        
    Returns:
        dict: 処理結果（レスポンスまたはエラー情報）
    """
    # 有効なGeminiインスタンスを取得
    gemini_instance, error_message = get_valid_gemini_instance()
    if gemini_instance is None:
        return {"error": error_message}
    
    try:
        # メッセージリストに新しいユーザーメッセージを追加
        new_user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        
        # 画像があれば追加
        if image_path:
            new_user_message["image_path"] = image_path
        
        st.session_state.messages.append(new_user_message)
        
        # ローディング表示
        with st.spinner("Geminiが考え中..."):
            # Gemini APIでレスポンスを生成
            if image_data:
                response = gemini_instance.generate_content(user_input, image_data=image_data)
            else:
                response = gemini_instance.generate_content(user_input)
        
        # エラーチェック
        if isinstance(response, dict) and "error" in response:
            return response
        
        # 成功した場合は応答を追加
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
        
        return {"success": True}
        
    except Exception as e:
        return {"error": f"メッセージ処理中にエラーが発生しました: {str(e)}"}

# 会話履歴を表示する関数
def display_conversation():
    """会話履歴を表示する"""
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(f"**{message['timestamp']}**")
                st.markdown(message["content"])
                
                # 画像があれば表示
                if "image_path" in message and message["image_path"]:
                    # 画像をサムネイルとして表示
                    try:
                        # 画像コンテナを表示
                        st.markdown('<div class="thumbnail-container">', unsafe_allow_html=True)
                        st.image(message["image_path"], use_container_width=True)
                        st.markdown(f'<div class="thumbnail-caption">アップロードされた画像</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"画像の表示に失敗しました: {str(e)}")
        
        elif message["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(f"**{message['timestamp']}**")
                st.markdown(message["content"])
        
        elif message["role"] == "system":
            st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>{message['content']}</div>", unsafe_allow_html=True)

# 画像変換のためのプロンプトを生成する関数
def get_transformation_prompt(style, custom_instruction=None):
    """
    選択されたスタイルに基づいて画像変換のプロンプトを生成
    
    Args:
        style (str): 変換スタイル
        custom_instruction (str, optional): カスタム指示
        
    Returns:
        str: 画像変換のためのプロンプト
    """
    prompts = {
        "アニメ風": "この画像をアニメーションスタイルに変換してください。明るい色彩と特徴的な線画を使用して、日本のアニメのような見た目にしてください。必ず変換後のイメージを詳しく説明してください。",
        "水彩画風": "この画像を水彩画風に変換してください。柔らかいブラシストローク、淡い色合い、そして水彩特有の滲みを表現してください。必ず変換後のイメージを詳しく説明してください。",
        "油絵風": "この画像をクラシックな油絵のスタイルに変換してください。豊かな色彩と厚塗りの質感を持つ、印象派の画家が描いたような印象にしてください。必ず変換後のイメージを詳しく説明してください。",
        "ピクセルアート": "この画像をレトロなピクセルアートスタイルに変換してください。限られた色数と明確なピクセルの境界線を持つ、80年代のビデオゲームのような見た目にしてください。必ず変換後のイメージを詳しく説明してください。",
        "ネオン風": "この画像をネオン効果のある未来的なスタイルに変換してください。暗い背景に鮮やかな光の要素を加え、サイバーパンクのような雰囲気にしてください。必ず変換後のイメージを詳しく説明してください。",
        "モノクロ": "この画像をモノクロームのスタイルに変換してください。強いコントラストと深みのある黒を使って、ドラマチックな白黒写真のような仕上がりにしてください。必ず変換後のイメージを詳しく説明してください。",
        "ポップアート": "この画像をポップアートスタイルに変換してください。明るく大胆な色使い、はっきりとした輪郭線、そしてハーフトーンパターンを使って、アンディ・ウォーホルのような仕上がりにしてください。必ず変換後のイメージを詳しく説明してください。",
        "スケッチ風": "この画像を鉛筆スケッチのスタイルに変換してください。細かい線と繊細な陰影を使った、手描きのドローイングのような印象にしてください。必ず変換後のイメージを詳しく説明してください。",
    }
    
    base_prompt = prompts.get(style, "この画像を変換してください。必ず変換後のイメージを詳しく説明してください。")
    
    if custom_instruction:
        return f"{base_prompt} 追加指示: {custom_instruction}"
    
    return base_prompt

# レスポンスが適切な画像変換の説明を含んでいるかを確認する関数
def is_valid_transformation_response(response, style):
    """
    Geminiの応答が適切な画像変換の説明を含んでいるかを確認する
    
    Args:
        response (str): Geminiからの応答テキスト
        style (str): 変換スタイル
        
    Returns:
        bool: 応答が適切な画像変換の説明を含んでいる場合はTrue
    """
    # 応答がない場合は無効
    if not response or len(response) < 50:
        return False
    
    # スタイル名が含まれているか確認
    if style.lower() not in response.lower():
        return False
    
    # 画像の特徴や変換結果の説明を含んでいるか確認するキーワード
    description_keywords = [
        "変換", "スタイル", "色彩", "質感", "特徴", "表現", "画像", 
        "効果", "線", "色合い", "テクスチャ", "陰影", "印象"
    ]
    
    # キーワードのうち少なくとも3つが含まれているか確認
    keyword_count = sum(1 for keyword in description_keywords if keyword in response)
    if keyword_count < 3:
        return False
    
    # 段落や詳細な説明が含まれているか（改行や文の数で判断）
    sentences = re.split(r'[。.!?]', response)
    if len(sentences) < 3:
        return False
    
    return True

# Geminiでの画像変換を実行する関数（リトライ機能付き）
def transform_image_with_retry(gemini_instance, prompt, image_data, style, max_retries=5):
    """
    Geminiで画像変換を実行し、適切な結果が得られるまでリトライする。
    また、PILを使用して実際に画像変換も行います。
    
    Args:
        gemini_instance (GeminiAPI): Gemini APIインスタンス
        prompt (str): 変換プロンプト
        image_data (bytes): 画像データ
        style (str): 変換スタイル
        max_retries (int, optional): 最大リトライ回数
        
    Returns:
        str: 変換結果のレスポンス
        int: リトライ回数
        str: 変換後の画像パス
    """
    from PIL import Image, ImageOps, ImageEnhance, ImageFilter
    import io
    import os
    from datetime import datetime
    import hashlib
    
    retry_count = 0
    transformed_image_path = None
    
    # 元の画像をPILで読み込む
    try:
        img = Image.open(io.BytesIO(image_data))
        
        # スタイルに応じた画像変換処理
        if style == "モノクロ":
            # モノクロ変換
            transformed_img = ImageOps.grayscale(img)
            # コントラスト強調
            enhancer = ImageEnhance.Contrast(transformed_img)
            transformed_img = enhancer.enhance(1.2)
        elif style == "スケッチ風":
            # エッジ検出してスケッチ風に
            transformed_img = img.convert("L")
            transformed_img = ImageOps.invert(transformed_img)
            transformed_img = transformed_img.filter(ImageFilter.FIND_EDGES)
            transformed_img = ImageOps.invert(transformed_img)
        elif style == "アニメ風":
            # 色彩強調とエッジ検出の組み合わせ
            # 色の彩度を上げる
            color_img = ImageEnhance.Color(img).enhance(1.5)
            # エッジを検出
            edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
            # 元の色彩強調画像にエッジをブレンド
            transformed_img = color_img
        elif style == "水彩画風":
            # ぼかしを適用して水彩風に
            transformed_img = img.filter(ImageFilter.GaussianBlur(radius=1))
            # 彩度を少し下げる
            transformed_img = ImageEnhance.Color(transformed_img).enhance(0.8)
        elif style == "油絵風":
            # コントラストと彩度を高めて油絵風に
            transformed_img = ImageEnhance.Contrast(img).enhance(1.3)
            transformed_img = ImageEnhance.Color(transformed_img).enhance(1.4)
            # テクスチャ感を出すために少しぼかす
            transformed_img = transformed_img.filter(ImageFilter.GaussianBlur(radius=0.5))
        elif style == "ピクセルアート":
            # 画像サイズを縮小してからリサイズして荒くする
            small_size = (img.width // 10, img.height // 10)
            transformed_img = img.resize(small_size, Image.NEAREST)
            transformed_img = transformed_img.resize((img.width, img.height), Image.NEAREST)
        elif style == "ネオン風":
            # エッジを検出して明るい色に
            edges = img.filter(ImageFilter.FIND_EDGES)
            # 彩度と明るさを上げる
            transformed_img = ImageEnhance.Color(edges).enhance(2.0)
            transformed_img = ImageEnhance.Brightness(transformed_img).enhance(1.5)
        elif style == "ポップアート":
            # 彩度を大幅に上げてポップアートっぽく
            transformed_img = ImageEnhance.Color(img).enhance(2.0)
            transformed_img = ImageEnhance.Contrast(transformed_img).enhance(1.5)
        else:
            # デフォルトはモノクロ
            transformed_img = ImageOps.grayscale(img)
        
        # 変換した画像を一時ファイルに保存
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename_hash = hashlib.md5(image_data).hexdigest()[:8]  # 画像データのハッシュ値を使用
        temp_dir = "temp_images"
        os.makedirs(temp_dir, exist_ok=True)
        
        transformed_image_path = os.path.join(temp_dir, f"{timestamp}_{filename_hash}_{style}.png")
        transformed_img.save(transformed_image_path)
        
    except Exception as e:
        print(f"画像変換中にエラーが発生しました: {e}")
        # エラーが発生しても処理を継続（テキスト生成は行う）
    
    while retry_count < max_retries:
        # リトライカウントを増やす
        retry_count += 1
        
        # Gemini APIで画像変換を実行
        response = gemini_instance.generate_content(prompt, image_data=image_data)
        
        # エラーチェック
        if isinstance(response, dict) and "error" in response:
            return response, retry_count, transformed_image_path
        
        # 応答が適切な画像変換の説明を含んでいるか確認
        if is_valid_transformation_response(response, style):
            return response, retry_count, transformed_image_path
        
        # 適切な応答が得られなかった場合、プロンプトを強化してリトライ
        if retry_count < max_retries:
            # プロンプトを強化
            enhanced_prompt = f"{prompt}\n\n重要: この画像の{style}への変換について、具体的かつ詳細に説明してください。画像の特徴、色彩、構図、質感などの変化を詳しく述べてください。少なくとも3段落、200文字以上の詳細な説明を提供してください。"
            prompt = enhanced_prompt
            
            # 一時停止して再試行（API制限対策）
            time.sleep(1)
    
    # 最大リトライ回数に達しても適切な応答が得られなかった場合
    return response, retry_count, transformed_image_path

# メイン関数
def main():
    """アプリケーションのメイン機能"""
    # アプリの初期化
    startup()
    
    # タイトルとスタイル
    st.markdown("<h1 style='text-align: center;'>🎨 Gemini AI イメージ変換</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>画像をアップロードして、AIによる変換効果を体験しよう</p>", unsafe_allow_html=True)
    
    # サイドバー
    with st.sidebar:
        st.header("設定")
        
        # モード切替
        app_mode = st.radio(
            "アプリモード", 
            ["画像変換モード", "チャットモード"], 
            index=0,
            help="画像変換モードでは画像の自動変換、チャットモードでは通常の会話が可能です"
        )
        
        # モードの状態を更新
        st.session_state.image_mode = (app_mode == "画像変換モード")
        
        # APIキー入力（初期値は.envから）
        api_key = os.getenv("GEMINI_API_KEY", "")
        st.markdown("### Gemini APIキー設定")
        st.markdown("1. [Google AI Studio](https://makersuite.google.com/app/apikey) からAPIキーを取得")
        st.markdown("2. 以下にコピー＆ペーストしてください")
        
        api_key_input = st.text_input(
            "Gemini API Key", 
            value=api_key, 
            type="password", 
            key="api_key_input",
            help="APIキーは「AIzaSy」で始まる文字列です。Google AI Studioから取得できます。"
        )
        
        # APIキーの状態を表示
        if api_key_input:
            if len(api_key_input) < 30:  # 一般的なGoogleのAPIキーは39文字程度
                st.warning("⚠️ 入力されたAPIキーが短すぎる可能性があります")
            else:
                st.success("✅ APIキーの形式が正しいようです")
        else:
            st.info("ℹ️ APIキーを入力してください")
        
        # APIキーが入力されたら.envファイルとLocalStorageに保存
        if api_key_input != api_key and api_key_input:
            # .envファイルに保存
            with open(".env", "w", encoding='utf-8') as f:
                f.write(f"GEMINI_API_KEY={api_key_input}")
            
            # 環境変数に直接設定
            os.environ["GEMINI_API_KEY"] = api_key_input
            
            st.success("APIキーが更新されました")
            
            # LocalStorageにも保存（JavaScript経由）
            st.markdown(f"""
            <script>
            try {{
                localStorage.setItem('geminiApiKey', '{api_key_input}');
                console.log('APIキーをLocalStorageに保存しました');
            }} catch (e) {{
                console.error('LocalStorageへのAPIキー保存に失敗しました:', e);
            }}
            </script>
            """, unsafe_allow_html=True)
            
            # Geminiインスタンスを再初期化
            if "gemini_instance" in st.session_state:
                del st.session_state["gemini_instance"]
                
            # 画面を更新してAPIキーを即時反映
            st.rerun()
        
        # APIキーのLocalStorage読み込みボタン
        if not api_key and st.button("保存済みのAPIキーを読み込む", help="ブラウザに保存されているAPIキーを読み込みます"):
            st.markdown(f"""
            <script>
            try {{
                const savedApiKey = localStorage.getItem('geminiApiKey');
                if (savedApiKey) {{
                    window.parent.postMessage({{
                        type: 'STREAMLIT:SET_WIDGET_VALUE',
                        widgetId: 'api_key_input',
                        value: savedApiKey
                    }}, '*');
                    console.log('保存済みのAPIキーを読み込みました');
                }} else {{
                    console.log('保存済みのAPIキーが見つかりません');
                }}
            }} catch (e) {{
                console.error('LocalStorageからのAPIキー読み込みに失敗しました:', e);
            }}
            </script>
            """, unsafe_allow_html=True)
            st.info("保存済みのAPIキーを読み込んでいます。ページを再読み込みしてください。")
            
        # APIキーの状態を確認して表示
        gemini_instance, error = get_valid_gemini_instance()
        if error:
            st.warning(error)
        else:
            st.success("✅ APIキーが有効です。Gemini APIを利用できます。")
            
        # 会話履歴をクリアするボタン
        if st.button("会話履歴をクリア"):
            st.session_state.messages = [
                {
                    "role": "system",
                    "content": "👋 こんにちは！画像をアップロードして、Gemini AIによる画像変換を体験してください。テキストチャットも可能です。",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
            ]
            st.rerun()
            
        # 利用ガイド
        st.markdown("---")
        if st.session_state.image_mode:
            st.subheader("画像変換の使い方")
            st.markdown("1. 「画像をアップロード」から画像を選択")
            st.markdown("2. 変換スタイルを選択")
            st.markdown("3. 必要に応じてカスタム指示を入力")
            st.markdown("4. 「変換を実行」ボタンを押して処理を開始")
        else:
            st.subheader("チャットの使い方")
            st.markdown("1. テキスト入力欄に質問や指示を入力")
            st.markdown("2. 「送信」ボタンを押すか、Enterキーで送信")
            st.markdown("3. 画像についての質問をする場合は、画像をアップロードしてから質問を入力")
    
    # メインコンテンツのレイアウト
    main_container = st.container()
    
    with main_container:
        # 画像アップロードエリア - レイアウト修正
        if st.session_state.image_mode:
            st.subheader("🖼️ 画像変換")
        else:
            st.subheader("💬 Geminiとチャット")
        
        # 画像アップロードUIの横幅を広げる
        uploaded_image = st.file_uploader(
            "📷 画像をアップロード", 
            type=["jpg", "jpeg", "png"],
            help="画像をアップロードして変換または分析を行います"
        )
        
        # 画像変換モードの場合
        if st.session_state.image_mode and uploaded_image:
            st.markdown('<div class="image-transformation-container">', unsafe_allow_html=True)
            
            # 変換スタイル選択
            st.markdown("<div class='style-option-label'>変換スタイルを選択：</div>", unsafe_allow_html=True)
            transformation_style = st.selectbox(
                "変換スタイル",
                ["アニメ風", "水彩画風", "油絵風", "ピクセルアート", "ネオン風", "モノクロ", "ポップアート", "スケッチ風"],
                label_visibility="collapsed"
            )
            
            # カスタム指示
            custom_instruction = st.text_area(
                "カスタム指示（オプション）",
                placeholder="例：より明るい色合いで、背景を夕焼けにしてください"
            )
            
            # 変換実行ボタン
            if st.button("変換を実行", type="primary", use_container_width=True):
                # 有効なGeminiインスタンスを取得
                gemini_instance, error_message = get_valid_gemini_instance()
                if gemini_instance is None:
                    st.error(error_message)
                else:
                    # 画像データの取得
                    image_data = uploaded_image.getvalue()
                    image_path = save_uploaded_image(image_data, uploaded_image.name)
                    
                    if not image_path:
                        st.error("画像の保存に失敗しました。別の画像を試してください。")
                    else:
                        # 変換プロンプトの生成
                        prompt = get_transformation_prompt(transformation_style, custom_instruction)
                        
                        # ユーザーメッセージを追加
                        user_message = {
                            "role": "user",
                            "content": f"この画像を{transformation_style}に変換してください。" + (f"\n追加指示: {custom_instruction}" if custom_instruction else ""),
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "image_path": image_path,
                            "transformation_style": transformation_style
                        }
                        st.session_state.messages.append(user_message)
                        
                        # 画像変換処理（リトライ機能付き）
                        with st.spinner(f"{transformation_style}スタイルに変換中..."):
                            response, retry_count, transformed_image_path = transform_image_with_retry(
                                gemini_instance, 
                                prompt, 
                                image_data, 
                                transformation_style
                            )
                        
                        if isinstance(response, dict) and "error" in response:
                            st.error(f"⚠️ エラーが発生しました: {response['error']}")
                        else:
                            # リトライ情報を含む応答テキストを作成
                            if retry_count > 1:
                                response_with_info = f"{response}\n\n_（{retry_count}回の試行で最適な回答を生成しました）_"
                            else:
                                response_with_info = response
                            
                            # 変換結果を追加
                            ai_message = {
                                "role": "assistant",
                                "content": response_with_info,
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "transformation_style": transformation_style,
                                "retry_count": retry_count,
                                "transformed_image_path": transformed_image_path
                            }
                            
                            st.session_state.messages.append(ai_message)
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 会話履歴用コンテナ
        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="conversation-container">', unsafe_allow_html=True)
            
            # 画像変換モードの場合、最新の変換結果を表示
            if st.session_state.image_mode:
                # 最新の変換ペアを探す
                latest_user_image = None
                latest_response = None
                
                for i in range(len(st.session_state.messages) - 1, 0, -1):
                    message = st.session_state.messages[i]
                    if message["role"] == "assistant" and "transformation_style" in message:
                        latest_response = message
                        # 対応するユーザーメッセージを探す
                        for j in range(i - 1, -1, -1):
                            user_message = st.session_state.messages[j]
                            if user_message["role"] == "user" and "image_path" in user_message:
                                latest_user_image = user_message
                                break
                        if latest_user_image:
                            break
                
                if latest_user_image and latest_response:
                    st.markdown("<h3>最新の変換結果</h3>", unsafe_allow_html=True)
                    st.markdown(f"スタイル: **{latest_user_image.get('transformation_style', '変換')}**")
                    
                    st.markdown('<div class="before-after-container">', unsafe_allow_html=True)
                    
                    # 元の画像
                    st.markdown('<div class="image-card">', unsafe_allow_html=True)
                    st.markdown('<div class="image-card-header">元の画像</div>', unsafe_allow_html=True)
                    st.markdown('<div class="image-card-body">', unsafe_allow_html=True)
                    st.image(latest_user_image["image_path"], use_container_width=True)
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    # 変換後の画像と説明
                    st.markdown('<div class="image-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="image-card-header">{latest_user_image.get("transformation_style", "変換")}スタイル</div>', unsafe_allow_html=True)
                    st.markdown('<div class="image-card-body">', unsafe_allow_html=True)
                    
                    # 変換された画像があれば表示
                    if "transformed_image_path" in latest_response and latest_response["transformed_image_path"]:
                        try:
                            st.image(latest_response["transformed_image_path"], use_container_width=True)
                            
                            # ダウンロードボタンを追加
                            with open(latest_response["transformed_image_path"], "rb") as f:
                                img_bytes = f.read()
                                style_name = latest_user_image.get("transformation_style", "変換済み")
                                file_extension = latest_response["transformed_image_path"].split(".")[-1]
                                st.download_button(
                                    label=f"{style_name}画像をダウンロード",
                                    data=img_bytes,
                                    file_name=f"gemini_{style_name}_image.{file_extension}",
                                    mime=f"image/{file_extension}"
                                )
                        except Exception as e:
                            st.error(f"変換画像の表示に失敗しました: {str(e)}")
                    else:
                        st.warning("変換された画像が見つかりません。")
                    
                    # 説明テキストは表示しない（折りたたんでおく）
                    with st.expander("変換説明を表示"):
                        st.markdown(latest_response["content"])
                    
                    st.markdown('</div></div>', unsafe_allow_html=True)
                    
                    st.markdown("<h3>変換履歴</h3>", unsafe_allow_html=True)
            
            # 会話履歴の表示
            display_conversation()
            st.markdown('</div>', unsafe_allow_html=True)
        
        # チャットモードの場合のみ入力フォームを表示
        if not st.session_state.image_mode:
            # 入力フォーム - Enterで送信できるようにフォームを使用
            with st.form(key="chat_form", clear_on_submit=True):
                st.markdown('<div class="chat-form">', unsafe_allow_html=True)
                
                # 2つの列に分割して配置
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    user_input = st.text_input(
                        "Geminiに質問する...", 
                        key="user_input",
                        placeholder="質問を入力し、Enterキーまたは「送信」ボタンを押してください",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    submit_button = st.form_submit_button(
                        "送信", 
                        use_container_width=True,
                        type="primary"
                    )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 入力があって送信ボタンが押されたら実行
                if user_input and (submit_button or st.session_state.get("enter_pressed", False)):
                    # 次回のために自動送信フラグをリセット
                    st.session_state["enter_pressed"] = False
                    
                    # 画像処理と送信ロジック
                    image_data = None
                    image_path = None
                    
                    if uploaded_image:
                        # 一時ファイルに保存
                        image_data = uploaded_image.getvalue()
                        # 新しい関数を使用して画像を保存
                        image_path = save_uploaded_image(image_data, uploaded_image.name)
                        
                        if not image_path:
                            st.error("画像の保存に失敗しました。別の画像を試してください。")
                    
                    # メッセージを処理
                    result = process_message(user_input, image_data, image_path)
                    
                    # エラーチェック
                    if "error" in result:
                        st.error(f"⚠️ エラーが発生しました: {result['error']}")
                    
                    # フォーム送信後に再描画
                    st.rerun()

# Enterキーでフォームを送信するためのJavaScriptを追加
st.markdown("""
<script>
// ページの読み込みが完了したら実行
document.addEventListener('DOMContentLoaded', function() {
    // テキスト入力フィールドにEnterキーイベントを設定する関数
    function setupEnterKeyListener() {
        // テキスト入力フィールドを探す
        const textInputs = document.querySelectorAll('input[type="text"]');
        
        textInputs.forEach(function(input) {
            // 既にリスナーが設定されているか確認
            if (!input.hasAttribute('data-enter-listener')) {
                input.setAttribute('data-enter-listener', 'true');
                
                // キー入力イベントのリスナーを追加
                input.addEventListener('keydown', function(e) {
                    // Enterキーが押された場合
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault(); // デフォルトの動作を防止
                        
                        // 送信ボタンを探して自動クリック
                        const submitButton = document.querySelector('button[type="submit"]');
                        if (submitButton) {
                            submitButton.click();
                            console.log('Enterキーで送信を実行しました');
                        }
                    }
                });
                
                console.log('テキスト入力フィールドにEnterキーイベントを設定しました');
            }
        });
    }

    // 初回実行
    setupEnterKeyListener();
    
    // DOM変更の監視設定
    const observer = new MutationObserver(function(mutations) {
        setupEnterKeyListener();
    });
    
    // body全体のDOM変更を監視
    observer.observe(document.body, { 
        childList: true, 
        subtree: true 
    });
});
</script>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    finally:
        # 終了時に古い一時ファイルをクリーンアップ（24時間以上前のファイル）
        cleanup_temp_files(24)
