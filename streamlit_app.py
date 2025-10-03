import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import zipfile
import os
import tempfile
from io import BytesIO

# ページ設定
st.set_page_config(
    page_title="日田市洪水ハザードマップ",
    page_icon="🌊",
    layout="wide"
)

# タイトル
st.title("🌊 日田市洪水ハザードマップ（国土数値情報準拠）")
st.markdown("---")

# サイドバー
st.sidebar.header("📂 データの読み込み")
st.sidebar.markdown("""
### データ入手方法
1. [国土数値情報ダウンロードサイト](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A31-v4_0.html)にアクセス
2. メッシュ番号 **5030** と **5031** のGEOJSON形式データをダウンロード
   - A31-22_10_5030_GEOJSON.zip（洪水予報河川）
   - A31-22_20_5030_GEOJSON.zip（その他の河川）
   - A31-22_10_5031_GEOJSON.zip（洪水予報河川）
   - A31-22_20_5031_GEOJSON.zip（その他の河川）
3. ダウンロードしたZIPファイルをここにアップロード
""")

# ファイルアップロード
uploaded_files = st.sidebar.file_uploader(
    "GeoJSONのZIPファイルをアップロード",
    type=["zip"],
    accept_multiple_files=True
)

st.sidebar.markdown("---")
st.sidebar.header("🎨 表示設定")
show_flood = st.sidebar.checkbox("浸水想定区域", value=True)
show_evacuation = st.sidebar.checkbox("避難場所", value=True)

st.sidebar.markdown("---")
st.sidebar.header("浸水深の凡例")
st.sidebar.markdown("""
- 🟣 **5.0m以上** (2階天井以上浸水)
- 🔴 **3.0～5.0m** (2階床まで浸水)
- 🟠 **0.5～3.0m** (1階が浸水)
- 🟡 **0.5m未満** (床上浸水程度)
- 🔵 **その他** (詳細不明)
""")

st.sidebar.markdown("---")
st.sidebar.warning("""
**⚠️ 重要な注意事項**
- このマップは想定最大規模の降雨を想定
- 浸水想定区域外でも浸水する可能性あり
- 水深50cm以上で避難が非常に困難に
- 危険を感じたら早めに避難を開始
""")

# 日田市の避難場所サンプルデータ
evacuation_sites = [
    {"name": "日田市役所", "lat": 33.3218, "lon": 130.9407, "type": "指定避難所"},
    {"name": "三隈中学校", "lat": 33.3190, "lon": 130.9360, "type": "指定避難所"},
    {"name": "桂林小学校", "lat": 33.3270, "lon": 130.9370, "type": "指定避難所"},
    {"name": "日田林工高校", "lat": 33.3150, "lon": 130.9480, "type": "指定避難所"},
    {"name": "三芳小学校", "lat": 33.3240, "lon": 130.9520, "type": "指定避難所"},
    {"name": "石井小学校", "lat": 33.3100, "lon": 130.9300, "type": "指定避難所"},
    {"name": "光岡小学校", "lat": 33.3280, "lon": 130.9450, "type": "指定避難所"},
    {"name": "高瀬小学校", "lat": 33.3050, "lon": 130.9250, "type": "指定避難所"},
]

# 浸水深に応じた色の設定
def get_color_from_depth(depth_desc):
    """浸水深の説明から色を返す"""
    if isinstance(depth_desc, str):
        if "5.0m以上" in depth_desc or "5m以上" in depth_desc:
            return "purple"
        elif "3.0～5.0m" in depth_desc or "3～5m" in depth_desc:
            return "red"
        elif "0.5～3.0m" in depth_desc or "0.5～3m" in depth_desc:
            return "orange"
        elif "0.5m未満" in depth_desc:
            return "yellow"
    return "blue"

# GeoJSONデータの読み込み関数
def load_geojson_from_zip(zip_file):
    """ZIPファイルからGeoJSONを読み込む"""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # ZIPファイルを解凍
            with zipfile.ZipFile(BytesIO(zip_file.read())) as z:
                z.extractall(tmpdir)
                
                # GeoJSONファイルを探す
                for root, dirs, files in os.walk(tmpdir):
                    for file in files:
                        if file.endswith('.geojson') or file.endswith('.json'):
                            filepath = os.path.join(root, file)
                            gdf = gpd.read_file(filepath)
                            return gdf
        return None
    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")
        return None

# メイン処理
hita_center = [33.3218, 130.9407]
all_geodata = []

# アップロードされたファイルを処理
if uploaded_files:
    with st.spinner("データを読み込んでいます..."):
        for uploaded_file in uploaded_files:
            st.info(f"処理中: {uploaded_file.name}")
            gdf = load_geojson_from_zip(uploaded_file)
            if gdf is not None:
                all_geodata.append(gdf)
                st.success(f"✓ {uploaded_file.name} を読み込みました（{len(gdf)}件）")

# 統計情報の表示
if all_geodata:
    total_features = sum(len(gdf) for gdf in all_geodata)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("読み込んだデータセット", f"{len(all_geodata)}個")
    with col2:
        st.metric("浸水想定区域", f"{total_features:,}箇所")
    with col3:
        st.metric("避難場所", f"{len(evacuation_sites)}箇所")
    
    st.markdown("---")
    
    # 地図の作成
    m = folium.Map(
        location=hita_center,
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # 浸水想定区域の表示
    if show_flood and all_geodata:
        for idx, gdf in enumerate(all_geodata):
            # 日田市周辺のデータのみをフィルタリング（緯度経度の範囲指定）
            gdf_hita = gdf.cx[130.8:131.1, 33.2:33.4]
            
            if len(gdf_hita) > 0:
                st.info(f"データセット{idx+1}: 日田市周辺に{len(gdf_hita)}件の浸水区域")
                
                for _, row in gdf_hita.iterrows():
                    # 浸水深の情報を取得
                    depth_info = ""
                    color = "blue"
                    
                    # GeoJSONの属性から浸水深情報を取得
                    if 'A31_001' in row:  # 河川名
                        depth_info += f"河川: {row['A31_001']}<br>"
                    if 'A31_006' in row:  # 浸水ランク
                        rank = row['A31_006']
                        depth_info += f"浸水ランク: {rank}<br>"
                        color = get_color_from_depth(str(rank))
                    
                    # ポリゴンを地図に追加
                    folium.GeoJson(
                        row['geometry'],
                        style_function=lambda x, c=color: {
                            'fillColor': c,
                            'color': c,
                            'weight': 1,
                            'fillOpacity': 0.4
                        },
                        tooltip=depth_info if depth_info else "浸水想定区域"
                    ).add_to(m)
    
    # 避難場所の表示
    if show_evacuation:
        marker_cluster = MarkerCluster().add_to(m)
        for site in evacuation_sites:
            folium.Marker(
                location=[site["lat"], site["lon"]],
                popup=f"""
                    <b>{site['name']}</b><br>
                    {site['type']}
                """,
                tooltip=site["name"],
                icon=folium.Icon(color='green', icon='home', prefix='fa')
            ).add_to(marker_cluster)
    
    # 地図の表示
    st_folium(m, width=1200, height=600)
    
    # データの詳細情報
    st.markdown("---")
    st.header("📊 読み込んだデータの詳細")
    
    for idx, gdf in enumerate(all_geodata):
        with st.expander(f"データセット {idx+1} の詳細 ({len(gdf)}件)"):
            # 日田市周辺のデータのみ
            gdf_hita = gdf.cx[130.8:131.1, 33.2:33.4]
            
            if len(gdf_hita) > 0:
                # 属性情報の表示
                st.write(f"**日田市周辺のデータ数**: {len(gdf_hita)}件")
                
                # データフレームとして表示
                if not gdf_hita.empty:
                    display_cols = [col for col in gdf_hita.columns if col != 'geometry']
                    st.dataframe(gdf_hita[display_cols].head(20))
            else:
                st.info("このデータセットには日田市周辺のデータが含まれていません")

else:
    # データ未アップロード時のデモ表示
    st.info("""
    ### 📤 データをアップロードしてください
    
    左のサイドバーから国土数値情報の洪水浸水想定区域データ（GeoJSON形式）をアップロードすると、
    日田市の正式な浸水想定区域が表示されます。
    
    **推奨データ:**
    - メッシュ番号 5030（日田市を含む）
    - メッシュ番号 5031（日田市東部を含む）
    
    データは[国土数値情報ダウンロードサイト](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A31-v4_0.html)から入手できます。
    """)
    
    # デモ地図の表示
    m = folium.Map(
        location=hita_center,
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # 避難場所のみ表示
    if show_evacuation:
        marker_cluster = MarkerCluster().add_to(m)
        for site in evacuation_sites:
            folium.Marker(
                location=[site["lat"], site["lon"]],
                popup=f"<b>{site['name']}</b><br>{site['type']}",
                tooltip=site["name"],
                icon=folium.Icon(color='green', icon='home', prefix='fa')
            ).add_to(marker_cluster)
    
    st_folium(m, width=1200, height=600)

# フッター
st.markdown("---")
st.info("""
**📞 お問い合わせ**  
日田市 総務企画部 防災・危機管理課  
電話: 0973-23-3111（代表）

**📖 データ出典**  
国土数値情報 洪水浸水想定区域データ（国土交通省）  
令和4年度版（2022年度）
""")