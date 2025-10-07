import streamlit as st
import geopandas as gpd
import folium
from folium import plugins
from streamlit_folium import folium_static
import pandas as pd
import requests
import zipfile
import io
import os

st.set_page_config(page_title="日田市洪水ハザードマップ", layout="wide")

st.title("🌊 日田市洪水浸水想定区域ハザードマップ")
st.markdown("国土数値情報の洪水浸水想定区域データを使用した日田市のハザードマップです")

# サイドバー
st.sidebar.header("設定")
st.sidebar.markdown("### 表示オプション")

# 浸水深の色分け定義
def get_depth_color(depth_code):
    """浸水深コードに基づいて色を返す"""
    color_map = {
        1: '#FFFF00',  # 0.5m未満 - 黄色
        2: '#FFD700',  # 0.5-1.0m - 金色
        3: '#FFA500',  # 1.0-2.0m - オレンジ
        4: '#FF6347',  # 2.0-5.0m - トマト色
        5: '#FF0000',  # 5.0-10.0m - 赤
        6: '#8B0000',  # 10.0-20.0m - 濃い赤
        7: '#4B0082',  # 20.0m以上 - インディゴ
    }
    return color_map.get(depth_code, '#808080')

def get_depth_label(depth_code):
    """浸水深コードに基づいてラベルを返す"""
    label_map = {
        1: '0.5m未満',
        2: '0.5-1.0m',
        3: '1.0-2.0m',
        4: '2.0-5.0m',
        5: '5.0-10.0m',
        6: '10.0-20.0m',
        7: '20.0m以上',
    }
    return label_map.get(depth_code, '不明')

# データ読み込みのキャッシュ
@st.cache_data
def load_sample_data():
    """サンプルデータを作成（実際のデータがない場合）"""
    # 日田市の中心座標
    hita_center = [33.3219, 130.9408]
    
    # サンプルポリゴンデータ
    sample_polygons = []
    offsets = [
        (0.01, 0.01, 2), (0.02, 0.01, 3), (-0.01, 0.01, 4),
        (0.01, -0.01, 3), (-0.02, -0.01, 5), (0.03, 0.02, 4)
    ]
    
    for offset_x, offset_y, depth in offsets:
        lat, lon = hita_center[0] + offset_y, hita_center[1] + offset_x
        polygon = [
            [lon - 0.005, lat - 0.005],
            [lon + 0.005, lat - 0.005],
            [lon + 0.005, lat + 0.005],
            [lon - 0.005, lat + 0.005],
            [lon - 0.005, lat - 0.005]
        ]
        sample_polygons.append({
            'geometry': {'type': 'Polygon', 'coordinates': [polygon]},
            'depth_code': depth,
            'depth_label': get_depth_label(depth)
        })
    
    return gpd.GeoDataFrame.from_features(sample_polygons, crs="EPSG:4326")

# メイン処理
try:
    st.info("💡 このアプリはデモ版です。実際の国土数値情報データを使用する場合は、データをダウンロードして読み込んでください。")
    
    # ファイルアップロード機能
    uploaded_file = st.sidebar.file_uploader(
        "GeoJSON/Shapefileをアップロード", 
        type=['geojson', 'json', 'zip']
    )
    
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.zip'):
            # Shapefileの場合
            with zipfile.ZipFile(uploaded_file) as z:
                z.extractall('temp_data')
            shp_files = [f for f in os.listdir('temp_data') if f.endswith('.shp')]
            if shp_files:
                gdf = gpd.read_file(f'temp_data/{shp_files[0]}')
        else:
            # GeoJSONの場合
            gdf = gpd.read_file(uploaded_file)
        
        st.success("✅ データを読み込みました")
    else:
        # サンプルデータを使用
        gdf = load_sample_data()
        st.warning("⚠️ サンプルデータを表示しています")
    
    # CRSを確認・変換
    if gdf.crs != "EPSG:4326":
        gdf = gdf.to_crs("EPSG:4326")
    
    # 表示する浸水深の選択
    if 'depth_code' in gdf.columns:
        unique_depths = sorted(gdf['depth_code'].unique())
        selected_depths = st.sidebar.multiselect(
            "表示する浸水深",
            options=unique_depths,
            default=unique_depths,
            format_func=get_depth_label
        )
        gdf_filtered = gdf[gdf['depth_code'].isin(selected_depths)]
    else:
        gdf_filtered = gdf
    
    # 地図の作成
    st.subheader("📍 洪水浸水想定区域マップ")
    
    # 地図の中心座標を計算
    bounds = gdf_filtered.total_bounds
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    
    # Folium地図の作成
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # レイヤーコントロール用
    feature_group = folium.FeatureGroup(name="浸水想定区域")
    
    # ポリゴンを地図に追加
    for idx, row in gdf_filtered.iterrows():
        depth_code = row.get('depth_code', 0)
        depth_label = row.get('depth_label', get_depth_label(depth_code))
        
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x, dc=depth_code: {
                'fillColor': get_depth_color(dc),
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.6
            },
            tooltip=f"浸水深: {depth_label}"
        ).add_to(feature_group)
    
    feature_group.add_to(m)
    
    # レイヤーコントロールを追加
    folium.LayerControl().add_to(m)
    
    # 凡例を追加
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 180px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p style="margin:0; font-weight:bold;">浸水深凡例</p>
    '''
    for code in range(1, 8):
        color = get_depth_color(code)
        label = get_depth_label(code)
        legend_html += f'<p style="margin:3px 0;"><span style="background-color:{color}; width:20px; height:15px; display:inline-block; margin-right:5px;"></span>{label}</p>'
    
    legend_html += '</div>'
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 地図を表示
    folium_static(m, width=1200, height=600)
    
    # 統計情報
    st.subheader("📊 統計情報")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("総区域数", len(gdf_filtered))
    
    with col2:
        if 'depth_code' in gdf_filtered.columns:
            max_depth = gdf_filtered['depth_code'].max()
            st.metric("最大浸水深", get_depth_label(max_depth))
    
    with col3:
        total_area = gdf_filtered.geometry.area.sum() * 111320 * 111320  # 概算面積(m²)
        st.metric("総面積(概算)", f"{total_area/1000000:.2f} km²")
    
    # データテーブル
    if st.checkbox("データテーブルを表示"):
        st.dataframe(gdf_filtered.drop(columns=['geometry']))

except Exception as e:
    st.error(f"エラーが発生しました: {str(e)}")
    st.info("国土数値情報ダウンロードサイト: https://nlftp.mlit.go.jp/ksj/")

# フッター
st.sidebar.markdown("---")
st.sidebar.markdown("### データについて")
st.sidebar.markdown("""
このアプリは国土数値情報の洪水浸水想定区域データを使用します。

**データ取得先:**
- [国土数値情報ダウンロードサービス](https://nlftp.mlit.go.jp/ksj/)
- カテゴリ: 洪水浸水想定区域
- 地域: 大分県日田市
""")