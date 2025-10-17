import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import json
import geopandas as gpd
from pathlib import Path
import hashlib
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="日田市 洪水ハザードマップ",
    page_icon="💧",
    layout="wide",
    initimport streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from pathlib import Path

# ページ設定
st.set_page_config(
    page_title="地図アプリケーション",
    page_icon="🗺️",
    layout="wide"
)

# タイトル
st.title("🗺️ 地図アプリケーション")

# サイドバー
st.sidebar.header("設定")

# サンプルデータの作成
@st.cache_data
def load_sample_data():
    data = {
        '名前': ['東京', '大阪', '名古屋', '福岡', '札幌'],
        '緯度': [35.6762, 34.6937, 35.1815, 33.5904, 43.0642],
        '経度': [139.6503, 135.5023, 136.9066, 130.4017, 141.3469],
        '人口': [13960000, 8839000, 2296000, 1539000, 1953000]
    }
    return pd.DataFrame(data)

# タブの作成
tab1, tab2, tab3 = st.tabs(["📍 地図表示", "📊 データ表", "ℹ️ 情報"])

with tab1:
    st.header("地図表示")
    
    # データの読み込み
    df = load_sample_data()
    
    # 地図の中心を選択
    center_option = st.selectbox(
        "地図の中心を選択",
        df['名前'].tolist()
    )
    
    # 選択された場所の座標を取得
    center_data = df[df['名前'] == center_option].iloc[0]
    
    # 地図の作成
    m = folium.Map(
        location=[center_data['緯度'], center_data['経度']],
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # マーカーの追加
    for idx, row in df.iterrows():
        folium.Marker(
            location=[row['緯度'], row['経度']],
            popup=f"{row['名前']}<br>人口: {row['人口']:,}人",
            tooltip=row['名前'],
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)
    
    # 地図の表示（修正版）
    st_folium(m, width=900, height=600)

with tab2:
    st.header("データ表")
    
    # データフレームの表示（修正版）
    st.dataframe(df, width='stretch')
    
    # 統計情報
    st.subheader("統計情報")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("都市数", len(df))
    with col2:
        st.metric("平均緯度", f"{df['緯度'].mean():.2f}")
    with col3:
        st.metric("総人口", f"{df['人口'].sum():,}人")

with tab3:
    st.header("アプリケーション情報")
    
    st.markdown("""
    ### 機能
    - 📍 インタラクティブな地図表示
    - 📊 データテーブル表示
    - 🎯 マーカーによる位置表示
    
    ### 使い方
    1. 「地図表示」タブで地図の中心を選択
    2. マーカーをクリックして詳細情報を表示
    3. 「データ表」タブで統計情報を確認
    
    ### 技術スタック
    - Streamlit
    - Folium
    - GeoPandas
    - Pandas
    """)

# フッター
st.sidebar.markdown("---")
st.sidebar.info("アプリケーションが正常に動作しています ✅")ial_sidebar_state="expanded"
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
    .dataset-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #e5e7eb;
        margin: 0.5rem 0;
    }
    .dataset-card.active {
        border-color: #3b82f6;
        background: #eff6ff;
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
if 'datasets' not in st.session_state:
    st.session_state.datasets = {}
if 'dataset_counter' not in st.session_state:
    st.session_state.dataset_counter = 0

# データセットの色パレット
COLOR_PALETTE = [
    '#8B0000', '#DC143C', '#FF6347', '#FFA07A', '#4169E1',
    '#9370DB', '#20B2AA', '#32CD32', '#FFD700', '#FF69B4'
]

def generate_dataset_id(filename):
    """ファイル名からユニークなIDを生成"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    hash_str = hashlib.md5(f"{filename}{timestamp}".encode()).hexdigest()[:8]
    return f"dataset_{hash_str}"

def add_dataset(name, data, data_type, source_file):
    """データセットを追加"""
    dataset_id = generate_dataset_id(name)
    color_index = st.session_state.dataset_counter % len(COLOR_PALETTE)
    
    st.session_state.datasets[dataset_id] = {
        'id': dataset_id,
        'name': name,
        'data': data,
        'type': data_type,
        'source_file': source_file,
        'color': COLOR_PALETTE[color_index],
        'visible': True,
        'opacity': 0.6,
        'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.dataset_counter += 1
    return dataset_id

def remove_dataset(dataset_id):
    """データセットを削除"""
    if dataset_id in st.session_state.datasets:
        del st.session_state.datasets[dataset_id]

def toggle_dataset_visibility(dataset_id):
    """データセットの表示/非表示を切り替え"""
    if dataset_id in st.session_state.datasets:
        st.session_state.datasets[dataset_id]['visible'] = not st.session_state.datasets[dataset_id]['visible']

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

# データセット管理セクション
st.sidebar.markdown("---")
st.sidebar.subheader("📊 読み込み済みデータセット")

if len(st.session_state.datasets) == 0:
    st.sidebar.info("データセットがまだ読み込まれていません。\n下部の「データアップロード」からファイルを追加してください。")
else:
    st.sidebar.markdown(f"**合計: {len(st.session_state.datasets)} 件**")
    
    for dataset_id, dataset in st.session_state.datasets.items():
        with st.sidebar.expander(f"{'✅' if dataset['visible'] else '⬜'} {dataset['name']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="font-size: 0.85rem;">
                    <strong>ファイル:</strong> {dataset['source_file']}<br>
                    <strong>追加日時:</strong> {dataset['added_at']}<br>
                    <strong>形式:</strong> {dataset['type']}<br>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # 色の表示
                st.markdown(f"""
                <div style="width: 30px; height: 30px; background-color: {dataset['color']}; 
                            border-radius: 5px; margin: 5px auto;"></div>
                """, unsafe_allow_html=True)
            
            # 表示/非表示切り替え
            if st.button(
                "👁️ 非表示" if dataset['visible'] else "👁️ 表示",
                key=f"toggle_{dataset_id}",
                use_container_width=True
            ):
                toggle_dataset_visibility(dataset_id)
                st.rerun()
            
            # 透明度調整
            new_opacity = st.slider(
                "透明度",
                0.1, 1.0, dataset['opacity'],
                0.1,
                key=f"opacity_{dataset_id}"
            )
            if new_opacity != dataset['opacity']:
                st.session_state.datasets[dataset_id]['opacity'] = new_opacity
            
            # データ情報
            if dataset['type'] == 'geodataframe':
                st.markdown(f"**データ件数:** {len(dataset['data'])} 件")
            elif dataset['type'] == 'geojson':
                if 'features' in dataset['data']:
                    st.markdown(f"**データ件数:** {len(dataset['data']['features'])} 件")
            
            # 削除ボタン
            if st.button("🗑️ 削除", key=f"delete_{dataset_id}", use_container_width=True):
                remove_dataset(dataset_id)
                st.rerun()

# 避難所データ
shelters = [
    {'name': '日田市役所', 'lat': 33.3219, 'lng': 130.9412, 'capacity': 500},
    {'name': '三隈中学校', 'lat': 33.3250, 'lng': 130.9380, 'capacity': 300},
    {'name': '日田市民会館', 'lat': 33.3200, 'lng': 130.9450, 'capacity': 400},
    {'name': '咸宜小学校', 'lat': 33.3180, 'lng': 130.9390, 'capacity': 250},
    {'name': '桂林小学校', 'lat': 33.3150, 'lng': 130.9360, 'capacity': 200}
]

# 表示オプション
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ 表示オプション")
show_shelters = st.sidebar.checkbox("避難所を表示", value=True)
show_base_layers = st.sidebar.checkbox("サンプルレイヤーを表示", value=False)

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
    
    # データセット数
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{len(st.session_state.datasets)}</div>
        <div class="stat-label">読み込み済みデータセット</div>
        <small style="color: #9ca3af;">表示中: {sum(1 for d in st.session_state.datasets.values() if d['visible'])} 件</small>
    </div>
    """, unsafe_allow_html=True)
    
    # サンプル統計（実データがある場合は計算）
    total_features = 0
    for dataset in st.session_state.datasets.values():
        if dataset['type'] == 'geodataframe':
            total_features += len(dataset['data'])
        elif dataset['type'] == 'geojson' and 'features' in dataset['data']:
            total_features += len(dataset['data']['features'])
    
    if total_features > 0:
        st.markdown(f"""
        <div class="stat-card" style="margin-top: 1rem;">
            <div class="stat-value">{total_features:,}</div>
            <div class="stat-label">総データポイント数</div>
            <small style="color: #9ca3af;">全データセット合計</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="stat-card" style="margin-top: 1rem;">
        <div class="stat-value">5箇所</div>
        <div class="stat-label">指定避難所</div>
        <small style="color: #9ca3af;">総収容人数: 1,650人</small>
    </div>
    """, unsafe_allow_html=True)

with col1:
    st.subheader("🗺️ 洪水ハザードマップ")
    
    if len(st.session_state.datasets) > 0:
        visible_count = sum(1 for d in st.session_state.datasets.values() if d['visible'])
        st.info(f"📍 表示中のデータセット: {visible_count} / {len(st.session_state.datasets)}")
    
    # 地図の作成
    m = folium.Map(
        location=[33.3219, 130.9412],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # サンプルレイヤーの描画
    if show_base_layers:
        sample_areas = [
            {
                'coords': [[33.3250, 130.9350], [33.3250, 130.9400], 
                          [33.3200, 130.9400], [33.3200, 130.9350]],
                'color': '#8B0000',
                'name': 'サンプルエリア1'
            },
            {
                'coords': [[33.3280, 130.9320], [33.3280, 130.9420], 
                          [33.3180, 130.9420], [33.3180, 130.9320]],
                'color': '#DC143C',
                'name': 'サンプルエリア2'
            }
        ]
        
        for area in sample_areas:
            folium.Polygon(
                locations=area['coords'],
                color=area['color'],
                fill=True,
                fillColor=area['color'],
                fillOpacity=0.3,
                weight=2,
                popup=area['name']
            ).add_to(m)
    
    # 読み込まれたデータセットの描画
    for dataset_id, dataset in st.session_state.datasets.items():
        if not dataset['visible']:
            continue
        
        try:
            if dataset['type'] == 'geodataframe':
                gdf = dataset['data']
                
                # GeoDataFrameをGeoJSONに変換
                geojson_str = gdf.to_json()
                
                folium.GeoJson(
                    geojson_str,
                    name=dataset['name'],
                    style_function=lambda x, color=dataset['color'], opacity=dataset['opacity']: {
                        'fillColor': color,
                        'color': color,
                        'weight': 2,
                        'fillOpacity': opacity
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=list(gdf.columns[:5]),
                        aliases=[str(col) for col in gdf.columns[:5]],
                        localize=True
                    )
                ).add_to(m)
                
            elif dataset['type'] == 'geojson':
                folium.GeoJson(
                    dataset['data'],
                    name=dataset['name'],
                    style_function=lambda x, color=dataset['color'], opacity=dataset['opacity']: {
                        'fillColor': color,
                        'color': color,
                        'weight': 2,
                        'fillOpacity': opacity
                    }
                ).add_to(m)
        except Exception as e:
            st.error(f"データセット '{dataset['name']}' の描画エラー: {str(e)}")
    
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
    
    # レイヤーコントロールを追加
    folium.LayerControl().add_to(m)
    
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
            <li>サイドバーでデータセットの表示/非表示を切り替え</li>
            <li>右上のレイヤーコントロールで個別レイヤーの切り替えが可能</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# データアップロードセクション
st.markdown("---")
st.subheader("📁 洪水浸水想定区域データの読み込み")

# タブで機能を分ける
tab1, tab2 = st.tabs(["📤 データアップロード", "🔄 形式変換ツール"])

with tab1:
    st.markdown("""
    国土交通省の**洪水浸水想定区域データ**を複数アップロードできます。
    
    **対応フォーマット:**
    - GeoJSON (.geojson, .json) ← **推奨**
    - Shapefile (.zip形式でアップロード)
    - KML (.kml)
    
    **📌 複数ファイル対応**: 一度に複数のファイルをアップロード可能です
    """)
    
    uploaded_files = st.file_uploader(
        "データファイルを選択（複数選択可）",
        type=['geojson', 'json', 'zip', 'kml'],
        help="国土交通省のデータポータルからダウンロードした洪水浸水想定区域データ",
        accept_multiple_files=True,
        key="main_uploader"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # ファイル名からデータセット名を生成
            dataset_name = uploaded_file.name.rsplit('.', 1)[0]
            
            # 既に同じ名前のデータセットがあるかチェック
            existing_names = [d['name'] for d in st.session_state.datasets.values()]
            if dataset_name in existing_names:
                st.warning(f"⚠️ '{dataset_name}' は既に読み込まれています。スキップします。")
                continue
            
            with st.spinner(f"'{uploaded_file.name}' を読み込み中..."):
                try:
                    if uploaded_file.name.endswith('.zip'):
                        # Shapefileの処理
                        import tempfile
                        import zipfile
                        import os
                        
                        with tempfile.TemporaryDirectory() as tmpdir:
                            with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
                                zip_ref.extractall(tmpdir)
                            
                            shp_files = []
                            for root, dirs, files in os.walk(tmpdir):
                                for file in files:
                                    if file.endswith('.shp'):
                                        shp_files.append(os.path.join(root, file))
                            
                            if shp_files:
                                gdf = gpd.read_file(shp_files[0])
                                
                                # WGS84に変換
                                if gdf.crs and gdf.crs.to_epsg() != 4326:
                                    gdf = gdf.to_crs(epsg=4326)
                                
                                dataset_id = add_dataset(
                                    dataset_name,
                                    gdf,
                                    'geodataframe',
                                    uploaded_file.name
                                )
                                st.success(f"✅ '{dataset_name}' を読み込みました（{len(gdf)} 件）")
                            else:
                                st.error(f"❌ '{uploaded_file.name}' 内に.shpファイルが見つかりません")
                    
                    elif uploaded_file.name.endswith('.kml'):
                        # KMLの処理
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_file_path = tmp_file.name
                        
                        gdf = gpd.read_file(tmp_file_path, driver='KML')
                        os.unlink(tmp_file_path)
                        
                        # WGS84に変換
                        if gdf.crs and gdf.crs.to_epsg() != 4326:
                            gdf = gdf.to_crs(epsg=4326)
                        
                        dataset_id = add_dataset(
                            dataset_name,
                            gdf,
                            'geodataframe',
                            uploaded_file.name
                        )
                        st.success(f"✅ '{dataset_name}' を読み込みました（{len(gdf)} 件）")
                    
                    else:
                        # GeoJSONの処理
                        file_content = uploaded_file.read()
                        geojson_data = json.loads(file_content)
                        
                        dataset_id = add_dataset(
                            dataset_name,
                            geojson_data,
                            'geojson',
                            uploaded_file.name
                        )
                        
                        feature_count = len(geojson_data['features']) if 'features' in geojson_data else 0
                        st.success(f"✅ '{dataset_name}' を読み込みました（{feature_count} 件）")
                
                except Exception as e:
                    st.error(f"❌ '{uploaded_file.name}' の読み込みに失敗: {str(e)}")
        
        if st.button("🔄 ページを更新", use_container_width=True):
            st.rerun()

with tab2:
    st.markdown("""
    ## 🔄 GeoJSON変換ツール
    
    Shapefile、KML、その他の地理空間データをGeoJSON形式に変換します。
    """)
    
    convert_file = st.file_uploader(
        "変換したいファイルを選択",
        type=['zip', 'kml', 'gpx', 'geojson', 'json'],
        help="Shapefile(ZIP)、KML、GPXなどの地理空間データファイル",
        key="convert_uploader"
    )
    
    if convert_file is not None:
        try:
            import tempfile
            import zipfile
            import os
            
            gdf = None
            
            with st.spinner("変換中..."):
                if convert_file.name.endswith('.zip'):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        with zipfile.ZipFile(convert_file, 'r') as zip_ref:
                            zip_ref.extractall(tmpdir)
                        
                        shp_files = []
                        for root, dirs, files in os.walk(tmpdir):
                            for file in files:
                                if file.endswith('.shp'):
                                    shp_files.append(os.path.join(root, file))
                        
                        if shp_files:
                            gdf = gpd.read_file(shp_files[0])
                            st.success(f"✅ Shapefileを読み込みました")
                        else:
                            st.error("❌ ZIPファイル内にShapefileが見つかりません")
                
                elif convert_file.name.endswith('.kml'):
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.kml') as tmp_file:
                        tmp_file.write(convert_file.read())
                        tmp_file_path = tmp_file.name
                    
                    gdf = gpd.read_file(tmp_file_path, driver='KML')
                    os.unlink(tmp_file_path)
                    st.success(f"✅ KMLファイルを読み込みました")
            
            if gdf is not None:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("データ件数", f"{len(gdf)} 件")
                with col2:
                    st.metric("カラム数", f"{len(gdf.columns)} 個")
                with col3:
                    if gdf.crs:
                        st.metric("座標系", str(gdf.crs).split(':')[-1])
                
                # 座標系変換
                if gdf.crs and gdf.crs.to_epsg() != 4326:
                    if st.button("🌍 WGS84 (EPSG:4326) に変換"):
                        gdf = gdf.to_crs(epsg=4326)
                        st.success("✅ 座標系を変換しました")
                
                # GeoJSON出力
                geojson_str = gdf.to_json()
                
                default_filename = convert_file.name.rsplit('.', 1)[0] + "_converted.geojson"
                
                st.download_button(
                    label="📥 GeoJSONファイルをダウンロード",
                    data=geojson_str,
                    file_name=default_filename,
                    mime="application/json",
                    use_container_width=True
                )
        
        except Exception as e:
            st.error(f"❌ 変換に失敗しました: {str(e)}")

# フッター
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; padding: 2rem;">
    <p style="font-size: 0.9rem;">日田市 洪水ハザードマップ | データソース: 国土交通省 洪水浸水想定区域データ</p>
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">※ このマップは想定最大規模降雨（1000年に1度程度）による浸水想定を示しています。</p>
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">緊急時は <a href="tel:119">119番</a> または市役所防災課までご連絡ください。</p>
</div>
""", unsafe_allow_html=True)