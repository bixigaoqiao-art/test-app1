import streamlit as st
import numpy as np
from PIL import Image, ImageEnhance, ImageDraw
import colorsys

st.set_page_config(page_title="色覚サポートアプリ", layout="wide")

st.title("🎨 色覚サポートアプリケーション")
st.markdown("色覚異常の方でも色の違いを認識しやすくするために、色を分離・強調表示します")

def rgb_to_hsv(rgb):
    """RGB (0-255) を HSV (H:0-360, S:0-100, V:0-100) に変換"""
    r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s * 100, v * 100

def hsv_to_rgb(hsv):
    """HSV (H:0-360, S:0-100, V:0-100) を RGB (0-255) に変換"""
    h, s, v = hsv[0]/360.0, hsv[1]/100.0, hsv[2]/100.0
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return int(r * 255), int(g * 255), int(b * 255)

def is_in_color_range(h, s, v, color_name):
    """指定した色の範囲内かチェック"""
    color_ranges = {
        "赤色系": [(h >= 0 and h <= 10 and s >= 40 and v >= 40) or 
                  (h >= 340 and h <= 360 and s >= 40 and v >= 40)],
        "緑色系": [h >= 80 and h <= 150 and s >= 20 and v >= 20],
        "青色系": [h >= 200 and h <= 260 and s >= 40 and v >= 40],
        "黄色系": [h >= 45 and h <= 65 and s >= 40 and v >= 40],
        "オレンジ色系": [h >= 10 and h <= 35 and s >= 40 and v >= 40],
        "紫色系": [h >= 270 and h <= 320 and s >= 20 and v >= 20]
    }
    return any(color_ranges.get(color_name, [False]))

def process_image(img_array, color_mode, enhancement, show_pattern):
    """画像処理のメイン関数"""
    height, width = img_array.shape[:2]
    result = img_array.copy()
    
    if color_mode == "全色分離":
        # 全色を異なる色で表示
        overlay = np.zeros_like(img_array)
        
        colors_to_detect = {
            "赤色系": (255, 50, 50),
            "緑色系": (50, 255, 50),
            "青色系": (50, 150, 255),
            "黄色系": (255, 255, 50)
        }
        
        for y in range(height):
            for x in range(width):
                r, g, b = img_array[y, x]
                h, s, v = rgb_to_hsv((r, g, b))
                
                for color_name, display_color in colors_to_detect.items():
                    if is_in_color_range(h, s, v, color_name):
                        overlay[y, x] = display_color
                        break
        
        # 元画像とブレンド
        alpha = 0.5
        result = (img_array * (1 - alpha) + overlay * alpha).astype(np.uint8)
        
    else:
        # 特定の色を強調
        mask = np.zeros((height, width), dtype=bool)
        
        for y in range(height):
            for x in range(width):
                r, g, b = img_array[y, x]
                h, s, v = rgb_to_hsv((r, g, b))
                
                if is_in_color_range(h, s, v, color_mode):
                    mask[y, x] = True
        
        # 強調処理
        enhanced = np.clip(img_array.astype(float) * enhancement, 0, 255).astype(np.uint8)
        result = np.where(mask[:, :, np.newaxis], enhanced, img_array)
        
        # パターンオーバーレイ
        if show_pattern:
            for y in range(0, height, 10):
                for x in range(width):
                    if mask[y, x]:
                        result[y, x] = (result[y, x] * 0.7 + 255 * 0.3).astype(np.uint8)
    
    return result

# サイドバーで設定
st.sidebar.header("設定")

uploaded_file = st.file_uploader("画像をアップロードしてください", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    # 画像を読み込み
    image = Image.open(uploaded_file)
    
    # サイズが大きすぎる場合はリサイズ
    max_size = 800
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = tuple(int(dim * ratio) for dim in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # RGB配列に変換
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    img_array = np.array(image)
    
    st.sidebar.subheader("色の選択")
    color_mode = st.sidebar.selectbox(
        "強調する色",
        ["赤色系", "緑色系", "青色系", "黄色系", "オレンジ色系", "紫色系", "全色分離"]
    )
    
    # 強調度の調整
    enhancement = st.sidebar.slider("強調度", 1.0, 3.0, 1.5, 0.1)
    
    # パターン表示のオプション
    show_pattern = st.sidebar.checkbox("パターンオーバーレイ", value=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("元画像")
        st.image(image, use_container_width=True)
    
    with col2:
        st.subheader("処理後画像")
        
        with st.spinner('処理中...'):
            result = process_image(img_array, color_mode, enhancement, show_pattern)
            result_image = Image.fromarray(result)
        
        st.image(result_image, use_container_width=True)
    
    # 色の説明
    st.markdown("---")
    st.subheader("📖 使い方")
    st.markdown("""
    1. **画像をアップロード**: 色の識別が難しい画像を選択してください
    2. **色を選択**: 区別したい色を選択します
    3. **強調度を調整**: スライダーで色の強調具合を変更できます
    4. **全色分離**: すべての主要な色を異なる色相で表示し、区別しやすくします
    5. **パターンオーバーレイ**: 選択した色の領域に線パターンを追加します
    
    **ヒント**: 赤と緑の区別が難しい場合は「全色分離」モードが効果的です。
    """)
    
    # ダウンロードボタン
    from io import BytesIO
    buf = BytesIO()
    result_image.save(buf, format='PNG')
    st.download_button(
        label="処理後画像をダウンロード",
        data=buf.getvalue(),
        file_name="color_enhanced.png",
        mime="image/png"
    )

else:
    st.info("👆 画像をアップロードして開始してください")
    
    # サンプル説明
    st.markdown("---")
    st.subheader("このアプリでできること")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 色の分離")
        st.markdown("特定の色を検出して強調表示します")
    
    with col2:
        st.markdown("### 🔍 色の識別")
        st.markdown("似た色を区別しやすく変換します")
    
    with col3:
        st.markdown("### 🎨 全色可視化")
        st.markdown("すべての色を明確に分けて表示します")