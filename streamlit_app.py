import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import json

# ページ設定
st.set_page_config(
    page_title="日田市浸水予想ハザードマップ",
    page_icon="🌊",
    layout="wide"
)

# タイトル
st.title("🌊 日田市浸水予想ハザードマップ")
st.markdown("---")

# サイドバー
with st.sidebar:
    st.header("📋 使い方")
    st.markdown("""
    このアプリは日田市の浸水想定区域を可視化します。
    
    **データソース:**
    - 国土数値情報 洪水浸水想定区域データ
    - 日田市公式ハザードマップ情報
    
    **表示内容:**
    - 浸水想定区域
    - 浸水深さ
    - 避難場所
    """)
    
    st.markdown("---")
    st.header("⚙️ 設定")
    
    # データファイルのアップロード
    uploaded_file = st.file_uploader(
        "GeoJSONまたはShapefileをアップロード",
        type=['geojson', 'json', 'zip'],
        help="国土数値情報からダウンロードしたデータをアップロードしてください"
    )
    
    # 浸水深さフィルター
    st.subheader("浸水深さフィルター")
    depth_filter = st.multiselect(
        "表示する浸水深さ",
        ["0.5m未満", "0.5-1.0m", "1.0-2.0m", "2.0-5.0m", "5.0m以上"],
        default=["0.5m未満", "0.5-1.0m", "1.0-2.0m", "2.0-5.0m", "5.0m以上"]
    )

# メインコンテンツ
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 地図表示")
    
    # 日田市の中心座標
    hita_center = [33.3226, 130.9411]
    
    # 地図の作成
    m = folium.Map(
        location=hita_center,
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # サンプルデータ処理（実データがアップロードされた場合の処理）
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.geojson') or uploaded_file.name.endswith('.json'):
                gdf = gpd.read_file(uploaded_file)
                
                # 浸水深さに応じた色分け
                def get_color(depth):
                    if depth < 0.5:
                        return '#FFFF00'  # 黄色
                    elif depth < 1.0:
                        return '#FFA500'  # オレンジ
                    elif depth < 2.0:
                        return '#FF6347'  # 赤
                    elif depth < 5.0:
                        return '#8B0000'  # 濃い赤
                    else:
                        return '#4B0082'  # 紫
                
                # GeoJSONレイヤーの追加
                folium.GeoJson(
                    gdf,
                    name='浸水想定区域',
                    style_function=lambda x: {
                        'fillColor': get_color(x['properties'].get('depth', 0)),
                        'color': 'black',
                        'weight': 1,
                        'fillOpacity': 0.6
                    },
                    tooltip=folium.GeoJsonTooltip(
                        fields=['name', 'depth'],
                        aliases=['河川名:', '浸水深さ(m):'],
                        localize=True
                    )
                ).add_to(m)
                
                st.success("✅ データを読み込みました")
                
        except Exception as e:
            st.error(f"❌ データの読み込みに失敗しました: {str(e)}")
    else:
        # サンプル浸水想定区域（デモ用）
        sample_areas = [
            {"lat": 33.3226, "lon": 130.9411, "name": "日田市中心部", "depth": "1.0-2.0m"},
            {"lat": 33.3400, "lon": 130.9500, "name": "三隈川周辺", "depth": "2.0-5.0m"},
            {"lat": 33.3100, "lon": 130.9300, "name": "花月川周辺", "depth": "0.5-1.0m"},
        ]
        
        # サンプルマーカーの追加
        for area in sample_areas:
            color = 'red' if '2.0-5.0m' in area['depth'] else 'orange' if '1.0-2.0m' in area['depth'] else 'yellow'
            folium.CircleMarker(
                location=[area['lat'], area['lon']],
                radius=50,
                popup=f"{area['name']}<br>想定浸水深: {area['depth']}",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.4
            ).add_to(m)
        
        st.info("ℹ️ サンプルデータを表示中です。実際のデータをアップロードしてください。")
    
    # 避難所マーカー（サンプル）
    evacuation_sites = [
        {"name": "日田市役所", "lat": 33.3226, "lon": 130.9411},
        {"name": "日田市総合体育館", "lat": 33.3300, "lon": 130.9450},
    ]
    
    for site in evacuation_sites:
        folium.Marker(
            location=[site['lat'], site['lon']],
            popup=f"避難所: {site['name']}",
            icon=folium.Icon(color='green', icon='home', prefix='fa')
        ).add_to(m)
    
    # 凡例の追加
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 200px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
    <p style="margin-bottom: 5px;"><strong>浸水深さ</strong></p>
    <p style="margin: 3px;"><span style="background-color: #FFFF00; padding: 3px 10px;">　</span> 0.5m未満</p>
    <p style="margin: 3px;"><span style="background-color: #FFA500; padding: 3px 10px;">　</span> 0.5-1.0m</p>
    <p style="margin: 3px;"><span style="background-color: #FF6347; padding: 3px 10px;">　</span> 1.0-2.0m</p>
    <p style="margin: 3px;"><span style="background-color: #8B0000; padding: 3px 10px;">　</span> 2.0-5.0m</p>
    <p style="margin: 3px;"><span style="background-color: #4B0082; padding: 3px 10px;">　</span> 5.0m以上</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # 地図の表示
    st_folium(m, width=800, height=600)

with col2:
    st.subheader("📊 統計情報")
    
    # 統計データ（サンプル）
    st.metric("浸水想定区域面積", "約150 ha")
    st.metric("対象世帯数", "約5,000世帯")
    st.metric("指定避難所数", "18箇所")
    
    st.markdown("---")
    
    st.subheader("⚠️ 注意事項")
    st.warning("""
    - この地図は想定される最大規模の洪水を想定しています
    - 実際の浸水範囲は気象条件により変動します
    - 浸水想定区域外でも浸水の可能性があります
    - 避難情報は必ず日田市の公式情報を確認してください
    """)
    
    st.markdown("---")
    
    st.subheader("🔗 関連リンク")
    st.markdown("""
    - [日田市公式ハザードマップ](https://www.city.hita.oita.jp/)
    - [国土数値情報ダウンロード](https://nlftp.mlit.go.jp/ksj/)
    - [ハザードマップポータルサイト](https://disaportal.gsi.go.jp/)
    """)

# フッター
st.markdown("---")
st.caption("""
データソース: 国土数値情報（国土交通省）、日田市公式ハザードマップ  
※このアプリは参考情報です。実際の避難判断は公式情報に基づいて行ってください。
""")

# データダウンロード方法の説明
with st.expander("📥 データの取得方法"):
    st.markdown("""
    ### 国土数値情報からのデータ取得手順:
    
    1. [国土数値情報ダウンロードサイト](https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A31.html)にアクセス
    2. 「洪水浸水想定区域データ」を選択
    3. 大分県のデータをダウンロード
    4. ZIPファイルを解凍
    5. GeoJSON形式に変換（必要に応じて）
    6. このアプリにアップロード
    
    ### データ形式:
    - GeoJSON (.geojson)
    - Shapefile (.zip)
    
    ### 必要な属性情報:
    - 河川名
    - 浸水深さ
    - 想定規模
    """)