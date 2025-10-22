import streamlit as st
import numpy as np
from PIL import Image
import cv2

st.set_page_config(page_title="色覚サポートアプリ", layout="wide")

st.title("🎨 色覚サポートアプリケーション")
st.markdown("色覚異常の方でも色の違いを認識しやすくするために、色を分離・強調表示します")

# サイドバーで設定
st.sidebar.header("設定")

uploaded_file = st.file_uploader("画像をアップロードしてください", type=['png', 'jpg', 'jpeg'])

if uploaded_file is not None:
    # 画像を読み込み
    image = Image.open(uploaded_file)
    img_array = np.array(image)
    
    # RGBからBGRに変換（OpenCV用）
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    else:
        st.error("RGB画像をアップロードしてください")
        st.stop()
    
    # HSV色空間に変換
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    
    st.sidebar.subheader("色の選択")
    color_mode = st.sidebar.selectbox(
        "強調する色",
        ["赤色系", "緑色系", "青色系", "黄色系", "オレンジ色系", "紫色系", "全色分離"]
    )
    
    # 色範囲の定義（HSV）
    color_ranges = {
        "赤色系": [(0, 100, 100), (10, 255, 255), (170, 100, 100), (180, 255, 255)],
        "緑色系": [(40, 40, 40), (80, 255, 255)],
        "青色系": [(100, 100, 100), (130, 255, 255)],
        "黄色系": [(20, 100, 100), (30, 255, 255)],
        "オレンジ色系": [(10, 100, 100), (20, 255, 255)],
        "紫色系": [(130, 50, 50), (160, 255, 255)]
    }
    
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
        
        if color_mode == "全色分離":
            # 全色を分離して表示
            result = np.zeros_like(img_array)
            
            colors_to_show = ["赤色系", "緑色系", "青色系", "黄色系"]
            display_colors = [
                (255, 0, 0),      # 赤
                (0, 255, 0),      # 緑
                (0, 0, 255),      # 青
                (255, 255, 0)     # 黄
            ]
            
            for color_name, display_color in zip(colors_to_show, display_colors):
                ranges = color_ranges[color_name]
                mask = np.zeros(img_hsv[:, :, 0].shape, dtype=np.uint8)
                
                if len(ranges) == 4:  # 赤色（2つの範囲）
                    mask1 = cv2.inRange(img_hsv, np.array(ranges[0]), np.array(ranges[1]))
                    mask2 = cv2.inRange(img_hsv, np.array(ranges[2]), np.array(ranges[3]))
                    mask = cv2.bitwise_or(mask1, mask2)
                else:
                    mask = cv2.inRange(img_hsv, np.array(ranges[0]), np.array(ranges[1]))
                
                # マスクを適用して色を割り当て
                for i in range(3):
                    result[:, :, i] = np.where(mask > 0, 
                                               display_color[i], 
                                               result[:, :, i])
            
            # 元画像とブレンド
            alpha = 0.6
            result = cv2.addWeighted(img_array, 1-alpha, result, alpha, 0)
            
        else:
            # 特定の色を強調
            ranges = color_ranges[color_mode]
            mask = np.zeros(img_hsv[:, :, 0].shape, dtype=np.uint8)
            
            if len(ranges) == 4:  # 赤色の場合
                mask1 = cv2.inRange(img_hsv, np.array(ranges[0]), np.array(ranges[1]))
                mask2 = cv2.inRange(img_hsv, np.array(ranges[2]), np.array(ranges[3]))
                mask = cv2.bitwise_or(mask1, mask2)
            else:
                mask = cv2.inRange(img_hsv, np.array(ranges[0]), np.array(ranges[1]))
            
            # マスクを3チャンネルに拡張
            mask_3ch = cv2.merge([mask, mask, mask])
            
            # 強調処理
            highlighted = img_array.copy().astype(float)
            highlighted = highlighted * enhancement
            highlighted = np.clip(highlighted, 0, 255).astype(np.uint8)
            
            # マスク部分だけ強調
            result = np.where(mask_3ch > 0, highlighted, img_array)
            
            # パターンオーバーレイ
            if show_pattern:
                pattern = np.zeros_like(mask)
                pattern[::10, :] = 255  # 横線パターン
                pattern_3ch = cv2.merge([pattern, pattern, pattern])
                result = np.where((mask_3ch > 0) & (pattern_3ch > 0), 
                                 (result * 0.7 + 255 * 0.3).astype(np.uint8), 
                                 result)
        
        st.image(result, use_container_width=True)
    
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