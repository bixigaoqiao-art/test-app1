import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# ページ設定
st.set_page_config(
    page_title="日田市洪水ハザードマップ",
    page_icon="🌊",
    layout="wide"
)

# タイトル
st.title("🌊 日田市洪水ハザードマップ")
st.markdown("---")

# サイドバー
st.sidebar.header("表示設定")
show_flood = st.sidebar.checkbox("浸水想定区域", value=True)
show_evacuation = st.sidebar.checkbox("避難場所", value=True)
show_river = st.sidebar.checkbox("河川", value=True)

st.sidebar.markdown("---")
st.sidebar.header("浸水深の凡例")
st.sidebar.markdown("""
- 🟣 **5.0m以上** (非常に危険)
- 🔴 **3.0～5.0m** (2階まで浸水)
- 🟠 **0.5～3.0m** (1階が浸水)
- 🟡 **0.5m未満** (床上浸水)
""")

st.sidebar.markdown("---")
st.sidebar.info("""
このマップは想定最大規模の洪水を想定したものです。
実際の洪水時には、早めの避難を心がけてください。
""")

# 日田市の中心座標
hita_center = [33.3218, 130.9407]

# 浸水想定区域のサンプルデータ（日田市中心部と筑後川周辺）
flood_zones = [
    {"lat": 33.3200, "lon": 130.9350, "depth": "3.0～5.0m", "color": "red", "area": "隈地区"},
    {"lat": 33.3180, "lon": 130.9380, "depth": "0.5～3.0m", "color": "orange", "area": "豆田地区"},
    {"lat": 33.3250, "lon": 130.9420, "depth": "0.5～3.0m", "color": "orange", "area": "田島地区"},
    {"lat": 33.3150, "lon": 130.9320, "depth": "5.0m以上", "color": "purple", "area": "川沿い低地"},
    {"lat": 33.3220, "lon": 130.9500, "depth": "0.5m未満", "color": "yellow", "area": "三芳地区"},
    {"lat": 33.3280, "lon": 130.9380, "depth": "0.5～3.0m", "color": "orange", "area": "桂林地区"},
    {"lat": 33.3140, "lon": 130.9400, "depth": "3.0～5.0m", "color": "red", "area": "亀山地区"},
    {"lat": 33.3190, "lon": 130.9450, "depth": "0.5～3.0m", "color": "orange", "area": "竹田地区"},
]

# 避難場所のサンプルデータ
evacuation_sites = [
    {"name": "日田市役所", "lat": 33.3218, "lon": 130.9407, "type": "指定避難所"},
    {"name": "三隈中学校", "lat": 33.3190, "lon": 130.9360, "type": "指定避難所"},
    {"name": "桂林小学校", "lat": 33.3270, "lon": 130.9370, "type": "指定避難所"},
    {"name": "日田林工高校", "lat": 33.3150, "lon": 130.9480, "type": "指定避難所"},
    {"name": "三芳小学校", "lat": 33.3240, "lon": 130.9520, "type": "指定避難所"},
    {"name": "石井小学校", "lat": 33.3100, "lon": 130.9300, "type": "指定避難所"},
]

# 主要河川（筑後川）のポイント
river_points = [
    [33.3100, 130.9200],
    [33.3150, 130.9300],
    [33.3180, 130.9350],
    [33.3200, 130.9400],
    [33.3230, 130.9480],
    [33.3260, 130.9580],
]

# 情報表示
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("浸水想定区域数", f"{len(flood_zones)}箇所")
with col2:
    st.metric("避難場所", f"{len(evacuation_sites)}箇所")
with col3:
    st.metric("対象河川", "筑後川他")

st.markdown("---")

# 地図の作成
m = folium.Map(
    location=hita_center,
    zoom_start=13,
    tiles='OpenStreetMap'
)

# 浸水想定区域の表示
if show_flood:
    for zone in flood_zones:
        folium.Circle(
            location=[zone["lat"], zone["lon"]],
            radius=300,
            popup=f"""
                <b>{zone['area']}</b><br>
                浸水深: {zone['depth']}<br>
            """,
            tooltip=f"{zone['area']} - {zone['depth']}",
            color=zone["color"],
            fill=True,
            fillColor=zone["color"],
            fillOpacity=0.4,
            weight=2
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

# 河川の表示
if show_river:
    folium.PolyLine(
        river_points,
        color='blue',
        weight=5,
        opacity=0.7,
        tooltip='筑後川'
    ).add_to(m)

# 地図の表示
st_folium(m, width=1200, height=600)

# 詳細情報
st.markdown("---")
st.header("📊 浸水想定区域の詳細")

# データフレームの作成
flood_df = pd.DataFrame(flood_zones)
flood_df = flood_df[['area', 'depth']]
flood_df.columns = ['地区名', '想定浸水深']

st.dataframe(flood_df, use_container_width=True)

st.markdown("---")
st.header("🏠 指定避難所一覧")

evac_df = pd.DataFrame(evacuation_sites)
evac_df = evac_df[['name', 'type']]
evac_df.columns = ['施設名', '種別']

st.dataframe(evac_df, use_container_width=True)

# 注意事項
st.markdown("---")
st.warning("""
**⚠️ 重要な注意事項**
- このマップは想定最大規模の降雨を想定したものです
- 浸水想定区域外でも浸水する可能性があります
- 水深が50cm以上になると避難が非常に困難になります
- 危険を感じたら、早めに自主的な避難を開始してください
- 避難指示等が発令された場合は、速やかに避難してください
""")

st.info("""
**📞 お問い合わせ**  
日田市 総務企画部 防災・危機管理課  
電話: 0973-22-8393
""")