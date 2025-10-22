import streamlit as st
import numpy as np
from PIL import Image
import io

st.set_page_config(page_title="色覚異常支援ツール", layout="wide")

st.title("🎨 色覚異常支援ツール")
st.markdown("色を分離・強調して、色覚異常の方でも色の違いを認識しやすくします")

# サイドバーで設定
st.sidebar.header("⚙️ 設定")

# 色覚異常のタイプ選択
color_blind_type = st.sidebar.selectbox(
    "色覚異常のタイプ",
    ["1型色覚（赤色弱）", "2型色覚（緑色弱）", "3型色覚（青色弱）"]
)

# 処理モード選択
mode = st.sidebar.radio(
    "処理モード",
    ["色相シフト", "コントラスト強調", "パターン変換"]
)

# パラメータ調整
if mode == "色相シフト":
    shift_amount = st.sidebar.slider("シフト量", 0, 180, 30, 5)
    saturation_boost = st.sidebar.slider("彩度強調", 1.0, 3.0, 1.5, 0.1)
elif mode == "コントラスト強調":
    contrast_factor = st.sidebar.slider("コントラスト", 1.0, 3.0, 1.8, 0.1)
    brightness_factor = st.sidebar.slider("明度調整", 0.5, 1.5, 1.0, 0.1)
else:  # パターン変換
    pattern_intensity = st.sidebar.slider("パターン強度", 0.0, 1.0, 0.5, 0.1)

# 画像アップロード
uploaded_file = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])

def rgb_to_hsv(rgb):
    """RGB to HSV変換"""
    rgb = rgb.astype(float) / 255.0
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    
    maxc = np.maximum(np.maximum(r, g), b)
    minc = np.minimum(np.minimum(r, g), b)
    v = maxc
    
    delta = maxc - minc
    s = np.where(maxc != 0, delta / maxc, 0)
    
    rc = np.where(delta != 0, (maxc - r) / delta, 0)
    gc = np.where(delta != 0, (maxc - g) / delta, 0)
    bc = np.where(delta != 0, (maxc - b) / delta, 0)
    
    h = np.zeros_like(r)
    h = np.where((maxc == r), bc - gc, h)
    h = np.where((maxc == g), 2.0 + rc - bc, h)
    h = np.where((maxc == b), 4.0 + gc - rc, h)
    h = (h / 6.0) % 1.0
    
    return np.stack([h, s, v], axis=2)

def hsv_to_rgb(hsv):
    """HSV to RGB変換"""
    h, s, v = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
    
    i = (h * 6.0).astype(int)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6
    
    conditions = [i == 0, i == 1, i == 2, i == 3, i == 4, i == 5]
    r = np.select(conditions, [v, q, p, p, t, v])
    g = np.select(conditions, [t, v, v, q, p, p])
    b = np.select(conditions, [p, p, t, v, v, q])
    
    rgb = np.stack([r, g, b], axis=2)
    return (rgb * 255).astype(np.uint8)

def hue_shift_process(img_array, shift, saturation):
    """色相シフト処理"""
    hsv = rgb_to_hsv(img_array)
    
    # 色相をシフト
    hsv[:,:,0] = (hsv[:,:,0] + shift / 360.0) % 1.0
    
    # 彩度を強調
    hsv[:,:,1] = np.clip(hsv[:,:,1] * saturation, 0, 1)
    
    return hsv_to_rgb(hsv)

def contrast_enhance(img_array, contrast, brightness):
    """コントラスト強調処理"""
    # 明度調整
    img_float = img_array.astype(float) * brightness
    
    # コントラスト調整
    mean = img_float.mean(axis=(0, 1))
    img_float = (img_float - mean) * contrast + mean
    
    return np.clip(img_float, 0, 255).astype(np.uint8)

def pattern_conversion(img_array, intensity):
    """パターン変換処理"""
    # グレースケール変換
    gray = np.dot(img_array[...,:3], [0.299, 0.587, 0.114])
    
    # パターンの生成
    h, w = gray.shape
    pattern = np.zeros_like(img_array)
    
    # 色相に基づいてパターンを変える
    hsv = rgb_to_hsv(img_array)
    hue = hsv[:,:,0]
    
    # 赤系: 横線パターン
    red_mask = ((hue < 0.05) | (hue > 0.95))
    for i in range(0, h, 4):
        pattern[i:i+2, :] = img_array[i:i+2, :]
    
    # 緑系: 縦線パターン
    green_mask = (hue > 0.25) & (hue < 0.45)
    for j in range(0, w, 4):
        pattern[:, j:j+2] = img_array[:, j:j+2]
    
    # 青系: 斜線パターン
    blue_mask = (hue > 0.55) & (hue < 0.75)
    for i in range(h):
        for j in range(w):
            if (i + j) % 4 < 2:
                pattern[i, j] = img_array[i, j]
    
    # パターンと元画像をブレンド
    result = img_array * (1 - intensity) + pattern * intensity
    return result.astype(np.uint8)

if uploaded_file is not None:
    # 画像を読み込み
    image = Image.open(uploaded_file)
    img_array = np.array(image)
    
    # RGB画像のみ処理
    if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
        img_array = img_array[:, :, :3]  # アルファチャンネルを除去
        
        # 処理実行
        if mode == "色相シフト":
            processed = hue_shift_process(img_array, shift_amount, saturation_boost)
        elif mode == "コントラスト強調":
            processed = contrast_enhance(img_array, contrast_factor, brightness_factor)
        else:
            processed = pattern_conversion(img_array, pattern_intensity)
        
        # 結果表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("元画像")
            st.image(img_array, use_container_width=True)
        
        with col2:
            st.subheader("処理後")
            st.image(processed, use_container_width=True)
        
        # ダウンロードボタン
        processed_image = Image.fromarray(processed)
        buf = io.BytesIO()
        processed_image.save(buf, format="PNG")
        buf.seek(0)
        
        st.download_button(
            label="📥 処理後の画像をダウンロード",
            data=buf,
            file_name="processed_image.png",
            mime="image/png"
        )
    else:
        st.error("RGB形式の画像をアップロードしてください")
else:
    st.info("👆 画像をアップロードして開始してください")
    
    # 使い方の説明
    with st.expander("📖 使い方"):
        st.markdown("""
        ### 各モードの説明
        
        **色相シフト**
        - 色相環上で色をシフトさせ、区別しにくい色を別の色域に移動させます
        - 彩度を強調して色の違いをより明確にします
        
        **コントラスト強調**
        - 明暗のコントラストを強調して、色の違いを明度の違いとして認識しやすくします
        - 輝度の差を大きくすることで、色覚に依存しない判別を可能にします
        
        **パターン変換**
        - 色の違いをパターン（線や点）の違いに変換します
        - 色が区別できなくても、パターンの違いで識別できるようになります
        
        ### 推奨設定
        - **1型色覚（赤色弱）**: 色相シフト +30〜60度
        - **2型色覚（緑色弱）**: コントラスト強調 または 色相シフト
        - **3型色覚（青色弱）**: 色相シフト +30度 または コントラスト強調
        """)

# フッター
st.markdown("---")
st.markdown("💡 **ヒント**: スライダーを調整して、最も見やすい設定を見つけてください")