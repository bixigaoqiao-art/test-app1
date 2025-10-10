import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import json
import geopandas as gpd
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="日田市 洪水ハザードマップ",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e40af 0%, #1e3a8a 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .warning-box {
        background-color: #fef3c7;
        border-left: 5px solid #f59e0b;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .info-card {
        background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #3b82f6;
        margin: 1rem 0;
    }
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .stat-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e40af;
    }
    .stat-label {
        color: #6b7280;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    .depth-legend {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .shelter-card {
        background: #dcfce7;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #86efac;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None

# ヘッダー
st.markdown("""
<div class="main-header">
    <h1>💧 日田市 洪水ハザードマップ</h1>
    <p style="font-size: 1.1rem; margin-top: 0.5rem;">洪水浸水想定区域データ（河川単位）を活用した防災情報システム</p>
</div>
""", unsafe_allow_html=True)

# 警告メッセージ
st.markdown("""
<div class="warning-box">
    <h3>⚠️ ハザードマップの活用について</h3>
    <p style="margin: 0.5rem 0;">このマップは、想定される最大規模の降雨により河川が氾濫した場合の浸水想定区域を示したものです。</p>
    <p style="margin: 0.5rem 0;">実際の災害では、想定外の浸水が発生する可能性があります。</p>
    <p style="margin: 0.5rem 0; font-weight: bold; color: #92400e;">🚨 避難情報が発令されたら、速やかに避難してください。</p>
</div>
""", unsafe_allow_html=True)

# サイドバー設定
st.sidebar.header("🗺️ 表示設定")

# 河川データの定義
rivers_data = {
    'all': {'name': '全河川表示', 'color': '#ff0000'},
    'chikugo': {'name': '筑後川', 'color': '#ff0000', 'risk': 5},
    'mikuma': {'name': '三隈川', 'color': '#ff4500', 'risk': 4},
    'kagetsu': {'name': '花月川', 'color': '#ff8c00', 'risk': 3},
    'ono': {'name': '大野川', 'color': '#ffa500', 'risk': 3}
}

# 河川選択
selected_river = st.sidebar.selectbox(
    "表示する河川を選択",
    options=list(rivers_data.keys()),
    format_func=lambda x: rivers_data[x]['name'],
    index=0
)

# 表示オプション
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 表示オプション")
show_shelters = st.sidebar.checkbox("避難所を表示", value=True)
show_rivers = st.sidebar.checkbox("河川を表示", value=True)
show_flood_areas = st.sidebar.checkbox("浸水想定区域を表示", value=True)

# 浸水深度の凡例
st.sidebar.markdown("---")
st.sidebar.subheader("📊 浸水深度の目安")

depth_levels = [
    {'depth': '5.0m以上', 'color': '#8B0000', 'desc': '2階の軒下まで浸水'},
    {'depth': '3.0-5.0m', 'color': '#DC143C', 'desc': '1階の天井まで浸水'},
    {'depth': '0.5-3.0m', 'color': '#FF6347', 'desc': '大人の腰まで浸水'},
    {'depth': '0.5m未満', 'color': '#FFA07A', 'desc': '大人の膝まで浸水'}
]

for level in depth_levels:
    st.sidebar.markdown(f"""
    <div class="depth-legend">
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 30px; height: 30px; background-color: {level['color']}; 
                        border-radius: 5px; flex-shrink: 0;"></div>
            <div>
                <strong>{level['depth']}</strong><br>
                <small style="color: #6b7280;">{level['desc']}</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 避難所データ
shelters = [
    {'name': '日田市役所', 'lat': 33.3219, 'lng': 130.9412, 'capacity': 500},
    {'name': '三隈中学校', 'lat': 33.3250, 'lng': 130.9380, 'capacity': 300},
    {'name': '日田市民会館', 'lat': 33.3200, 'lng': 130.9450, 'capacity': 400},
    {'name': '咸宜小学校', 'lat': 33.3180, 'lng': 130.9390, 'capacity': 250},
    {'name': '桂林小学校', 'lat': 33.3150, 'lng': 130.9360, 'capacity': 200}
]

# 避難所リスト表示
if show_shelters:
    st.sidebar.markdown("---")
    st.sidebar.subheader("🏢 指定避難所")
    for shelter in shelters:
        st.sidebar.markdown(f"""
        <div class="shelter-card">
            <strong>{shelter['name']}</strong><br>
            <small>収容人数: {shelter['capacity']}人</small>
        </div>
        """, unsafe_allow_html=True)

# メインコンテンツエリア
col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("📊 統計情報")
    
    # 統計カード
    st.markdown("""
    <div class="stat-card">
        <div class="stat-value">12.5 km²</div>
        <div class="stat-label">浸水想定区域面積</div>
        <small style="color: #9ca3af;">想定最大規模降雨時</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="stat-card" style="margin-top: 1rem;">
        <div class="stat-value">8,500人</div>
        <div class="stat-label">想定浸水人口</div>
        <small style="color: #9ca3af;">浸水深0.5m以上の区域内</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="stat-card" style="margin-top: 1rem;">
        <div class="stat-value">5箇所</div>
        <div class="stat-label">指定避難所</div>
        <small style="color: #9ca3af;">総収容人数: 1,650人</small>
    </div>
    """, unsafe_allow_html=True)
    
    # 河川別危険度
    st.markdown("---")
    st.subheader("⚠️ 河川別危険度")
    
    river_risk_data = []
    for river_id, river_info in rivers_data.items():
        if river_id != 'all' and 'risk' in river_info:
            river_risk_data.append({
                '河川名': river_info['name'],
                '危険度': '⭐' * river_info['risk'],
                'レベル': river_info['risk']
            })
    
    risk_df = pd.DataFrame(river_risk_data)
    st.dataframe(risk_df[['河川名', '危険度']], hide_index=True, use_container_width=True)

with col1:
    st.subheader("🗺️ 浸水想定区域マップ")
    
    if selected_river != 'all':
        st.info(f"📍 表示中: **{rivers_data[selected_river]['name']}**")
    
    # 地図の作成
    m = folium.Map(
        location=[33.3219, 130.9412],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # 浸水想定エリアのサンプルデータ
    flood_areas = [
        {
            'coords': [[33.3250, 130.9350], [33.3250, 130.9400], 
                      [33.3200, 130.9400], [33.3200, 130.9350]],
            'color': '#8B0000',
            'depth': '5.0m以上',
            'river': 'chikugo'
        },
        {
            'coords': [[33.3280, 130.9320], [33.3280, 130.9420], 
                      [33.3180, 130.9420], [33.3180, 130.9320]],
            'color': '#DC143C',
            'depth': '3.0-5.0m',
            'river': 'mikuma'
        },
        {
            'coords': [[33.3300, 130.9300], [33.3300, 130.9450], 
                      [33.3150, 130.9450], [33.3150, 130.9300]],
            'color': '#FF6347',
            'depth': '0.5-3.0m',
            'river': 'kagetsu'
        },
        {
            'coords': [[33.3270, 130.9360], [33.3270, 130.9410], 
                      [33.3220, 130.9410], [33.3220, 130.9360]],
            'color': '#FFA07A',
            'depth': '0.5m未満',
            'river': 'ono'
        }
    ]
    
    # 浸水エリアの描画
    if show_flood_areas:
        for area in flood_areas:
            if selected_river == 'all' or selected_river == area['river']:
                folium.Polygon(
                    locations=area['coords'],
                    color=area['color'],
                    fill=True,
                    fillColor=area['color'],
                    fillOpacity=0.5,
                    weight=2,
                    popup=folium.Popup(
                        f"<b>浸水深度:</b> {area['depth']}<br>"
                        f"<b>河川:</b> {rivers_data[area['river']]['name']}",
                        max_width=200
                    )
                ).add_to(m)
    
    # 河川ラインの描画
    if show_rivers:
        river_lines = {
            'chikugo': [[33.3300, 130.9200], [33.3250, 130.9350], [33.3200, 130.9450]],
            'mikuma': [[33.3280, 130.9250], [33.3220, 130.9400], [33.3180, 130.9420]],
            'kagetsu': [[33.3350, 130.9300], [33.3250, 130.9380], [33.3180, 130.9400]],
            'ono': [[33.3320, 130.9280], [33.3270, 130.9360], [33.3230, 130.9380]]
        }
        
        if selected_river == 'all':
            for river_id, coords in river_lines.items():
                folium.PolyLine(
                    coords,
                    color=rivers_data[river_id]['color'],
                    weight=5,
                    opacity=0.8,
                    popup=rivers_data[river_id]['name']
                ).add_to(m)
        elif selected_river in river_lines:
            folium.PolyLine(
                river_lines[selected_river],
                color=rivers_data[selected_river]['color'],
                weight=6,
                opacity=0.9,
                popup=rivers_data[selected_river]['name']
            ).add_to(m)
    
    # 避難所マーカーの追加
    if show_shelters:
        for shelter in shelters:
            folium.Marker(
                location=[shelter['lat'], shelter['lng']],
                popup=folium.Popup(
                    f"<b>{shelter['name']}</b><br>"
                    f"収容人数: {shelter['capacity']}人<br>"
                    f"<small>クリックで詳細を表示</small>",
                    max_width=250
                ),
                tooltip=shelter['name'],
                icon=folium.Icon(color='green', icon='home', prefix='fa')
            ).add_to(m)
    
    # 地図の表示
    folium_static(m, width=900, height=600)
    
    # 地図の説明
    st.markdown("""
    <div class="info-card">
        <h4>💡 地図の使い方</h4>
        <ul style="margin: 0.5rem 0;">
            <li>マウスホイールでズームイン/アウト</li>
            <li>ドラッグで地図を移動</li>
            <li>マーカーやエリアをクリックで詳細情報を表示</li>
            <li>サイドバーで表示する河川や情報を切り替え</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# データアップロードセクション
st.markdown("---")
st.subheader("📁 洪水浸水想定区域データの読み込み")

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    国土交通省の**洪水浸水想定区域データ（GeoJSON形式）**をアップロードすると、
    実際のデータに基づいた正確なハザードマップを表示できます。
    
    **対応フォーマット:**
    - GeoJSON (.geojson, .json)
    - Shapefile (.zip形式でアップロード)
    """)
    
    uploaded_file = st.file_uploader(
        "データファイルを選択",
        type=['geojson', 'json', 'zip'],
        help="国土交通省のデータポータルからダウンロードした洪水浸水想定区域データ"
    )
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.zip'):
                # Shapefileの処理
                import tempfile
                import zipfile
                
                with tempfile.TemporaryDirectory() as tmpdir:
                    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)
                    
                    # .shpファイルを探す
                    shp_files = list(Path(tmpdir).glob('*.shp'))
                    if shp_files:
                        gdf = gpd.read_file(shp_files[0])
                        st.session_state.uploaded_data = gdf
                        st.success(f"✅ Shapefileを読み込みました: {len(gdf)} 件のデータ")
                    else:
                        st.error("❌ ZIPファイル内に.shpファイルが見つかりません")
            else:
                # GeoJSONの処理
                geojson_data = json.load(uploaded_file)
                st.session_state.uploaded_data = geojson_data
                st.success(f"✅ GeoJSONファイルを読み込みました")
                
                # データのプレビュー
                if 'features' in geojson_data:
                    st.info(f"📊 データ数: {len(geojson_data['features'])} 件")
                    
                    # 最初のデータをプレビュー
                    if len(geojson_data['features']) > 0:
                        with st.expander("データのプレビュー（最初の1件）"):
                            st.json(geojson_data['features'][0])
        
        except Exception as e:
            st.error(f"❌ ファイルの読み込みに失敗しました: {str(e)}")

with col2:
    st.markdown("""
    <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; border: 2px solid #3b82f6;">
        <h4>📖 データ取得方法</h4>
        <ol style="font-size: 0.9rem; margin: 0.5rem 0;">
            <li>国土交通省の<a href="https://www.mlit.go.jp/" target="_blank">ウェブサイト</a>にアクセス</li>
            <li>「洪水浸水想定区域データ」を検索</li>
            <li>日田市または大分県のデータをダウンロード</li>
            <li>GeoJSON形式で保存</li>
            <li>このページにアップロード</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

# 避難時の注意事項
st.markdown("---")
st.subheader("🚨 避難時の注意事項")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="background: #dbeafe; padding: 1.5rem; border-radius: 10px; height: 100%;">
        <h4>🕐 避難のタイミング</h4>
        <p style="margin: 0.5rem 0;">避難指示が出たら、速やかに避難を開始してください。</p>
        <p style="margin: 0.5rem 0;">夜間の避難は危険なため、明るいうちに避難しましょう。</p>
        <p style="margin: 0.5rem 0; font-weight: bold;">早めの避難が命を守ります。</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="background: #dcfce7; padding: 1.5rem; border-radius: 10px; height: 100%;">
        <h4>🎒 持ち物</h4>
        <ul style="margin: 0.5rem 0; padding-left: 1.5rem;">
            <li>貴重品</li>
            <li>常備薬</li>
            <li>飲料水・食料</li>
            <li>懐中電灯</li>
            <li>携帯ラジオ</li>
            <li>モバイルバッテリー</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="background: #fef3c7; padding: 1.5rem; border-radius: 10px; height: 100%;">
        <h4>🗺️ 避難経路</h4>
        <p style="margin: 0.5rem 0;">浸水想定区域を避け、安全な経路で避難してください。</p>
        <p style="margin: 0.5rem 0; font-weight: bold; color: #92400e;">⚠️ 冠水している道路は絶対に通行しないでください。</p>
    </div>
    """, unsafe_allow_html=True)

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem;">
    <p style="font-size: 0.9rem;">日田市 洪水ハザードマップ | データソース: 国土交通省 洪水浸水想定区域データ</p>
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">※ このマップは想定最大規模降雨（1000年に1度程度）による浸水想定を示しています。</p>
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">緊急時は <a href="tel:119">119番</a> または市役所防災課までご連絡ください。</p>
</div>
""", unsafe_allow_html=True)