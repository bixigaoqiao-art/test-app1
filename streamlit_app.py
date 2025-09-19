import streamlit as st
import folium
import googlemaps
from streamlit_folium import st_folium

# Google Maps APIキーを設定
# ここに自分のAPIキーを入力してください
gmaps = googlemaps.Client(key="YOUR_GOOGLE_MAPS_API_KEY")

st.title("日田市ハザードマップウェブアプリケーション")
st.markdown("---")

## アプリケーションの概要
st.header("概要")
st.write(
    "このアプリケーションは、大分県日田市における浸水想定区域を表示するハザードマップです。指定した場所を検索し、地図上に浸水リスクを表示できます。"
)

st.markdown("---")

## 地図と機能
st.header("地図と機能")

# ユーザー入力
user_address = st.text_input("日田市内の住所や場所を入力してください（例：大分県日田市上城内町1-8）")

# 初期地図の中心座標（日田市役所）
hida_city_center = [33.3150, 130.9250]

# 地図の初期設定
m = folium.Map(location=hida_city_center, zoom_start=13, control_scale=True)

# 検索結果の処理
if user_address:
    try:
        geocode_result = gmaps.geocode(user_address + ", 大分県日田市")
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            folium.Marker(
                [lat, lng],
                popup=user_address,
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)
            m.location = [lat, lng]
            m.zoom_start = 15
        else:
            st.error("住所が見つかりませんでした。別の住所を試してください。")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# ハザードマップのレイヤーを追加（例：架空の浸水想定区域）
# ここではダミーのPolygonを使用していますが、実際にはGeoJSONデータなどを読み込む必要があります。
# 日田市の浸水想定区域のデータは、日田市公式サイトや国土交通省のハザードマップポータルサイトなどで公開されています。
# 例: 日田市における筑後川水系の浸水想定区域データ
folium.GeoJson(
    "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson",
    name="浸水想定区域（ダミー）",
    style_function=lambda feature: {
        "fillColor": "blue",
        "color": "blue",
        "weight": 1,
        "fillOpacity": 0.5,
    },
).add_to(m)

# レイヤーコントロールを追加
folium.LayerControl().add_to(m)

# Streamlitに地図を表示
st_data = st_folium(m, width=725, height=500)

st.markdown("---")

## 使い方
st.header("使い方")
st.write("1. 上部の入力欄に、日田市内の住所や場所を入力します。")
st.write("2. エンターキーを押すと、地図が入力した場所に移動し、マーカーが表示されます。")
st.write("3. 地図上の青いエリアが浸水想定区域です（このデモではダミーデータを使用しています）。")