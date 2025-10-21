import streamlit as st
import numpy as np
from PIL import Image
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
import av

def rgb_to_hsv(rgb):
    """RGBをHSVに変換"""
    rgb = rgb.astype(float) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    
    maxc = np.max(rgb, axis=-1)
    minc = np.min(rgb, axis=-1)
    v = maxc
    
    deltac = maxc - minc
    s = np.where(maxc != 0, deltac / maxc, 0)
    
    rc = np.where(deltac != 0, (maxc - r) / deltac, 0)
    gc = np.where(deltac != 0, (maxc - g) / deltac, 0)
    bc = np.where(deltac != 0, (maxc - b) / deltac, 0)
    
    h = np.zeros_like(maxc)
    h = np.where((maxc == r) & (deltac != 0), bc - gc, h)
    h = np.where((maxc == g) & (deltac != 0), 2.0 + rc - bc, h)
    h = np.where((maxc == b) & (deltac != 0), 4.0 + gc - rc, h)
    h = (h / 6.0) % 1.0
    h = h * 180
    
    return np.stack([h, s * 255, v * 255], axis=-1)

def separate_colors_fast(img_array, target_color):
    """特定の色を強調して分離（高速版）"""
    hsv = rgb_to_hsv(img_array)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    
    color_ranges = {
        '赤': [(0, 10), (170, 180)],
        '緑': [(40, 80)],
        '青': [(100, 130)],
        '黄': [(20, 40)],
        '紫': [(130, 160)],
        'オレンジ': [(10, 20)],
    }
    
    mask = np.zeros(h.shape, dtype=bool)
    
    for h_range in color_ranges[target_color]:
        h_min, h_max = h_range
        mask |= ((h >= h_min) & (h <= h_max) & (s >= 80) & (v >= 80))
    
    result = img_array.copy()
    result[~mask] = result[~mask] // 3
    
    return result

def enhance_contrast_fast(img_array, target_colors):
    """複数の色のコントラストを強調（高速版）"""
    hsv = rgb_to_hsv(img_array)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    
    result = img_array.copy()
    
    for mapping in target_colors:
        if mapping == '赤→マゼンタ':
            mask1 = ((h >= 0) & (h <= 10) & (s >= 80) & (v >= 80))
            mask2 = ((h >= 170) & (h <= 180) & (s >= 80) & (v >= 80))
            mask = mask1 | mask2
            result[mask] = [255, 0, 255]
            
        elif mapping == '緑→シアン':
            mask = ((h >= 40) & (h <= 80) & (s >= 80) & (v >= 80))
            result[mask] = [0, 255, 255]
            
        elif mapping == '赤→青':
            mask1 = ((h >= 0) & (h <= 10) & (s >= 80) & (v >= 80))
            mask2 = ((h >= 170) & (h <= 180) & (s >= 80) & (v >= 80))
            mask = mask1 | mask2
            result[mask] = [0, 0, 255]
            
        elif mapping == '緑→黄':
            mask = ((h >= 40) & (h <= 80) & (s >= 80) & (v >= 80))
            result[mask] = [255, 255, 0]
    
    return result

def apply_daltonization_fast(img_array, cvd_type):
    """色覚異常補正（高速版）"""
    img_float = img_array.astype(float) / 255.0
    
    if cvd_type == '1型（赤）':
        transform = np.array([
            [0.567, 0.433, 0.000],
            [0.558, 0.442, 0.000],
            [0.000, 0.242, 0.758]
        ])
    elif cvd_type == '2型（緑）':
        transform = np.array([
            [0.625, 0.375, 0.000],
            [0.700, 0.300, 0.000],
            [0.000, 0.300, 0.700]
        ])
    else:
        transform = np.array([
            [0.950, 0.050, 0.000],
            [0.000, 0.433, 0.567],
            [0.000, 0.475, 0.525]
        ])
    
    h, w = img_float.shape[:2]
    img_flat = img_float.reshape(-1, 3)
    simulated_flat = np.dot(img_flat, transform.T)
    simulated = simulated_flat.reshape(h, w, 3)
    
    error = img_float - simulated
    corrected = img_float + error * 1.5
    corrected = np.clip(corrected, 0, 1)
    
    return (corrected * 255).astype(np.uint8)

# ビデオプロセッサクラス
class ColorVisionProcessor(VideoProcessorBase):
    def __init__(self):
        self.mode = '色の分離'
        self.target_color = '赤'
        self.mappings = ['赤→マゼンタ']
        self.cvd_type = '2型（緑）'
    
    def recv(self, frame):
        img = frame.to_ndarray(format="rgb24")
        
        if self.mode == '色の分離':
            result = separate_colors_fast(img, self.target_color)
        elif self.mode == 'コントラスト強調':
            result = enhance_contrast_fast(img, self.mappings)
        else:
            result = apply_daltonization_fast(img, self.cvd_type)
        
        return av.VideoFrame.from_ndarray(result, format="rgb24")

# Streamlitアプリ
st.title('🎨 色覚異常支援ツール')
st.write('カメラまたは画像で色を分離・強調して、色の識別をサポートします')

# サイドバー
st.sidebar.header('設定')

# モード選択
app_mode = st.sidebar.radio(
    '使用モード',
    ['📷 リアルタイムカメラ', '🖼️ 画像アップロード']
)

mode = st.sidebar.radio(
    '処理モード',
    ['色の分離', 'コントラスト強調', '色覚補正']
)

# リアルタイムカメラモード
if app_mode == '📷 リアルタイムカメラ':
    st.subheader('リアルタイム処理')
    st.info('カメラを起動して、リアルタイムで色処理を確認できます')
    
    # プロセッサの設定
    ctx = webrtc_streamer(
        key="color-vision",
        video_processor_factory=ColorVisionProcessor,
        rtc_configuration=RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        ),
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )
    
    if ctx.video_processor:
        ctx.video_processor.mode = mode
        
        if mode == '色の分離':
            ctx.video_processor.target_color = st.sidebar.selectbox(
                '分離する色',
                ['赤', '緑', '青', '黄', '紫', 'オレンジ'],
                key='camera_color'
            )
            
        elif mode == 'コントラスト強調':
            ctx.video_processor.mappings = st.sidebar.multiselect(
                '色の変換',
                ['赤→マゼンタ', '緑→シアン', '赤→青', '緑→黄'],
                default=['赤→マゼンタ'],
                key='camera_mappings'
            )
            
        else:
            ctx.video_processor.cvd_type = st.sidebar.selectbox(
                '色覚異常のタイプ',
                ['1型（赤）', '2型（緑）', '3型（青）'],
                key='camera_cvd'
            )

# 画像アップロードモード
else:
    uploaded_file = st.file_uploader('画像をアップロード', type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file).convert('RGB')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader('元画像')
            st.image(image, use_container_width=True)
        
        with col2:
            st.subheader('処理後')
            img_array = np.array(image)
            
            if mode == '色の分離':
                target = st.sidebar.selectbox(
                    '分離する色',
                    ['赤', '緑', '青', '黄', '紫', 'オレンジ'],
                    key='image_color'
                )
                result = separate_colors_fast(img_array, target)
                st.image(result, use_container_width=True)
                st.info(f'{target}色の領域を強調表示しています')
                
            elif mode == 'コントラスト強調':
                mappings = st.sidebar.multiselect(
                    '色の変換',
                    ['赤→マゼンタ', '緑→シアン', '赤→青', '緑→黄'],
                    default=['赤→マゼンタ'],
                    key='image_mappings'
                )
                if mappings:
                    result = enhance_contrast_fast(img_array, mappings)
                    st.image(result, use_container_width=True)
                    st.info('選択した色を識別しやすい色に変換しています')
                else:
                    st.image(img_array, use_container_width=True)
                    
            else:
                cvd = st.sidebar.selectbox(
                    '色覚異常のタイプ',
                    ['1型（赤）', '2型（緑）', '3型（青）'],
                    key='image_cvd'
                )
                result = apply_daltonization_fast(img_array, cvd)
                st.image(result, use_container_width=True)
                st.info(f'{cvd}色覚異常に対応した補正を適用しています')
        
        # ダウンロードボタン
        if 'result' in locals():
            from io import BytesIO
            buf = BytesIO()
            Image.fromarray(result).save(buf, format='PNG')
            byte_im = buf.getvalue()
            
            st.download_button(
                '💾 処理画像をダウンロード',
                byte_im,
                file_name='processed_image.png',
                mime='image/png'
            )
    else:
        st.info('👆 画像をアップロードしてください')

# 説明
with st.expander('ℹ️ 使い方と各モードの説明'):
    st.markdown('''
    ### 📱 リアルタイムカメラモード
    - 「START」ボタンを押してカメラを起動
    - スマートフォンでアクセスすると、背面/前面カメラが使用可能
    - リアルタイムで色処理が適用されます
    
    ### 🖼️ 画像アップロードモード
    - 静止画を処理して結果を確認・保存できます
    
    ---
    
    ### 処理モード
    
    **色の分離**: 特定の色だけを強調表示し、他の色を暗くすることで色の識別を容易にします
    
    **コントラスト強調**: 混同しやすい色を、より識別しやすい色に変換します
    - 赤→マゼンタ: 赤を鮮やかなマゼンタに
    - 緑→シアン: 緑を明るいシアンに
    - 赤→青: 赤を青に変換（赤緑混同対策）
    - 緑→黄: 緑を明るい黄色に
    
    **色覚補正**: 色覚異常のタイプに応じた補正を適用し、色の違いを強調します
    - 1型（赤）: 赤錐体の機能不全（プロタノピア）
    - 2型（緑）: 緑錐体の機能不全（デュータノピア・最も一般的）
    - 3型（青）: 青錐体の機能不全（トリタノピア）
    ''')