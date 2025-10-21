import streamlit as st
import numpy as np
from PIL import Image
import cv2

def separate_colors(image, target_color):
    """特定の色を強調して分離"""
    img_array = np.array(image)
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    
    # 色相範囲の定義（HSV空間）
    color_ranges = {
        '赤': [(0, 100, 100), (10, 255, 255), (170, 100, 100), (180, 255, 255)],
        '緑': [(40, 100, 100), (80, 255, 255)],
        '青': [(100, 100, 100), (130, 255, 255)],
        '黄': [(20, 100, 100), (40, 255, 255)],
        '紫': [(130, 100, 100), (160, 255, 255)],
        'オレンジ': [(10, 100, 100), (20, 255, 255)],
    }
    
    # マスクの作成
    if target_color == '赤':
        mask1 = cv2.inRange(hsv, color_ranges['赤'][0], color_ranges['赤'][1])
        mask2 = cv2.inRange(hsv, color_ranges['赤'][2], color_ranges['赤'][3])
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        mask = cv2.inRange(hsv, color_ranges[target_color][0], color_ranges[target_color][1])
    
    # 結果画像の作成
    result = img_array.copy()
    result[mask == 0] = result[mask == 0] // 3  # 対象外の色を暗くする
    
    return Image.fromarray(result)

def enhance_contrast(image, target_colors):
    """複数の色のコントラストを強調"""
    img_array = np.array(image)
    hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
    
    color_mappings = {
        '赤→マゼンタ': [(0, 180, 170, 255), (255, 0, 255)],
        '緑→シアン': [(40, 80, 100, 255), (0, 255, 255)],
        '赤→青': [(0, 10, 100, 255), (0, 0, 255), (170, 180, 100, 255)],
        '緑→黄': [(40, 80, 100, 255), (255, 255, 0)],
    }
    
    result = img_array.copy()
    
    for mapping in target_colors:
        if mapping in color_mappings:
            data = color_mappings[mapping]
            if mapping == '赤→青':
                # 赤の2つの範囲を処理
                mask1 = cv2.inRange(hsv, (data[0][0], data[0][2], data[0][3], 0), 
                                   (data[0][1], 255, 255, 0))
                mask2 = cv2.inRange(hsv, (data[2][0], data[2][2], data[2][3], 0), 
                                   (data[2][1], 255, 255, 0))
                mask = cv2.bitwise_or(mask1, mask2)
                result[mask > 0] = data[1]
            else:
                mask = cv2.inRange(hsv, (data[0][0], data[0][2], data[0][3], 0), 
                                  (data[0][1], 255, 255, 0))
                result[mask > 0] = data[1]
    
    return Image.fromarray(result)

def apply_daltonization(image, cvd_type):
    """色覚異常シミュレーションと補正"""
    img_array = np.array(image).astype(float) / 255.0
    
    # 変換行列（簡易版）
    if cvd_type == '1型（赤）':
        # プロタノピア（赤錐体欠損）
        transform = np.array([
            [0.567, 0.433, 0.000],
            [0.558, 0.442, 0.000],
            [0.000, 0.242, 0.758]
        ])
    elif cvd_type == '2型（緑）':
        # デュータノピア（緑錐体欠損）
        transform = np.array([
            [0.625, 0.375, 0.000],
            [0.700, 0.300, 0.000],
            [0.000, 0.300, 0.700]
        ])
    else:  # 3型（青）
        # トリタノピア（青錐体欠損）
        transform = np.array([
            [0.950, 0.050, 0.000],
            [0.000, 0.433, 0.567],
            [0.000, 0.475, 0.525]
        ])
    
    # 画像を変換
    h, w = img_array.shape[:2]
    img_flat = img_array.reshape(-1, 3)
    simulated_flat = np.dot(img_flat, transform.T)
    simulated = simulated_flat.reshape(h, w, 3)
    
    # 補正（差分を強調）
    error = img_array - simulated
    corrected = img_array + error * 1.5
    corrected = np.clip(corrected, 0, 1)
    
    return Image.fromarray((corrected * 255).astype(np.uint8))

# Streamlitアプリ
st.title('🎨 色覚異常支援ツール')
st.write('画像の色を分離・強調して、色の識別をサポートします')

# サイドバー
st.sidebar.header('設定')
mode = st.sidebar.radio(
    '処理モード',
    ['色の分離', 'コントラスト強調', '色覚補正']
)

# 画像アップロード
uploaded_file = st.file_uploader('画像をアップロード', type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file).convert('RGB')
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('元画像')
        st.image(image, use_container_width=True)
    
    with col2:
        st.subheader('処理後')
        
        if mode == '色の分離':
            target = st.sidebar.selectbox(
                '分離する色',
                ['赤', '緑', '青', '黄', '紫', 'オレンジ']
            )
            result = separate_colors(image, target)
            st.image(result, use_container_width=True)
            st.info(f'{target}色の領域を強調表示しています')
            
        elif mode == 'コントラスト強調':
            mappings = st.sidebar.multiselect(
                '色の変換',
                ['赤→マゼンタ', '緑→シアン', '赤→青', '緑→黄'],
                default=['赤→マゼンタ']
            )
            if mappings:
                result = enhance_contrast(image, mappings)
                st.image(result, use_container_width=True)
                st.info('選択した色を識別しやすい色に変換しています')
            else:
                st.image(image, use_container_width=True)
                
        else:  # 色覚補正
            cvd = st.sidebar.selectbox(
                '色覚異常のタイプ',
                ['1型（赤）', '2型（緑）', '3型（青）']
            )
            result = apply_daltonization(image, cvd)
            st.image(result, use_container_width=True)
            st.info(f'{cvd}色覚異常に対応した補正を適用しています')
    
    # ダウンロードボタン
    if st.button('処理画像をダウンロード'):
        result.save('processed_image.png')
        with open('processed_image.png', 'rb') as f:
            st.download_button(
                '💾 ダウンロード',
                f,
                file_name='processed_image.png',
                mime='image/png'
            )

else:
    st.info('👆 画像をアップロードしてください')
    
# 説明
with st.expander('ℹ️ 各モードの説明'):
    st.markdown('''
    **色の分離**: 特定の色だけを強調表示し、他の色を暗くすることで色の識別を容易にします
    
    **コントラスト強調**: 混同しやすい色を、より識別しやすい色に変換します
    - 赤→マゼンタ: 赤を鮮やかなマゼンタに
    - 緑→シアン: 緑を明るいシアンに
    - 赤→青: 赤を青に変換（赤緑混同対策）
    - 緑→黄: 緑を明るい黄色に
    
    **色覚補正**: 色覚異常のタイプに応じた補正を適用し、色の違いを強調します
    - 1型（赤）: 赤錐体の機能不全
    - 2型（緑）: 緑錐体の機能不全（最も一般的）
    - 3型（青）: 青錐体の機能不全
    ''')