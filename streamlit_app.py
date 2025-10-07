import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import os

# --- 設定 ---
# データのファイルパス (ご自身のダウンロードしたファイルに合わせて変更してください)
# Shapefile (.shp) のファイルを指定することを推奨
DATA_FILE = "path/to/your/A31_Hita_Flood_Data.shp" 
# ※ GMLファイルの場合、読み込み前に解凍が必要な場合があります。

# 日田市の中心座標 (概算)
HITA_LAT = 33.310
HITA_LON = 130.940

# --- データのロードと準備 ---
@st.cache_data
def load_data(file_path):
    """地理空間データをロードし、必要な処理を行う"""
    if not os.path.exists(file_path):
        st.error(f"データファイルが見つかりません: {file_path}")
        st.stop()
    
    try:
        # GeoPandasでデータを読み込み
        # encodingを 'shift_jis' などに変更する必要があるかもしれません
        gdf = gpd.read_file(file_path)
        
        # 浸水深の属性名を確認し、必要に応じてリネーム (例: 'A31_001'を 'D_CLASS'と仮定)
        # 属性名はデータセットのバージョンによって異なるため、ご自身のデータを確認してください
        # 国土数値情報では、浸水深のランクを示す属性が使われます (例: A31_001,浸水深ランク)
        # 属性名が不明な場合は、print(gdf.columns) で確認してください
        
        # 例: 浸水深ランクの属性名を 'D_CLASS' と仮定して列を追加
        if 'D_CLASS' in gdf.columns:
             gdf['浸水深ランク'] = gdf['D_CLASS']
        elif 'A31_001' in gdf.columns: # 一般的な国土数値情報の一例
             gdf['浸水深ランク'] = gdf['A31_001']
        else:
             st.warning("浸水深ランクを示す属性列が見つかりません。属性名を確認してください。")
             return gdf

        # 浸水深ランクに基づく色分けの設定
        # 国土数値情報の凡例に基づいて色を割り当てます
        def get_color(d_class):
            if d_class == 1: return '#00BFFF' # 0.5m未満
            if d_class == 2: return '#1E90FF' # 0.5m～3.0m
            if d_class == 3: return '#0000CD' # 3.0m～5.0m
            if d_class == 4: return '#4B0082' # 5.0m以上
            return '#808080' # その他/不明
        
        gdf['color'] = gdf['浸水深ランク'].apply(get_color)
        
        return gdf
    except Exception as e:
        st.error(f"データの読み込み中にエラーが発生しました: {e}")
        st.stop()


# --- Streamlit アプリケーションの本体 ---
def main():
    st.set_page_config(layout="wide")
    st.title("日田市 洪水浸水想定区域 ハザードマップ")
    
    # データのロード
    gdf = load_data(DATA_FILE)

    if gdf is not None:
        st.subheader("浸水想定区域の表示")
        
        # 凡例の表示
        st.sidebar.markdown("### 浸水深ランク凡例")
        st.sidebar.markdown(f"<div style='background-color:#00BFFF; padding: 5px; margin: 2px; color: black;'>■ ランク1: 0.5m未満</div>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<div style='background-color:#1E90FF; padding: 5px; margin: 2px; color: white;'>■ ランク2: 0.5m～3.0m</div>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<div style='background-color:#0000CD; padding: 5px; margin: 2px; color: white;'>■ ランク3: 3.0m～5.0m</div>", unsafe_allow_html=True)
        st.sidebar.markdown(f"<div style='background-color:#4B0082; padding: 5px; margin: 2px; color: white;'>■ ランク4: 5.0m以上</div>", unsafe_allow_html=True)

        # Foliumマップの作成
        m = folium.Map(location=[HITA_LAT, HITA_LON], zoom_start=12, tiles='OpenStreetMap')
        
        # GeoDataFrameの各ポリゴンをマップに追加
        # 浸水深ランクに基づいて色分けして描画
        for _, row in gdf.iterrows():
            if row.geometry.geom_type == 'Polygon':
                # GeoJSON形式でプロットするために、座標を(lat, lon)のリストに変換
                coords = [(lat, lon) for lon, lat in row.geometry.exterior.coords]
                
                folium.Polygon(
                    locations=coords,
                    tooltip=f"浸水深ランク: {row['浸水深ランク']}", # マウスオーバーで情報表示
                    color=row['color'],
                    fill=True,
                    fill_color=row['color'],
                    fill_opacity=0.6,
                    weight=1
                ).add_to(m)

        # StreamlitにFoliumマップを表示
        st_folium(m, width=700, height=500)
        
        st.info("💡 浸水想定区域の色分けは、国土数値情報（洪水浸水想定区域データ）の凡例に基づいています。詳細な情報や最新のハザードマップは日田市公式の情報をご確認ください。")

if __name__ == "__main__":
    main()