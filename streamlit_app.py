import streamlit as st
import folium
import requests
from streamlit_folium import st_folium
import urllib.parse # 新たに追加

# アプリケーションのタイトル
st.title("日田市ハザードマップウェブアプリケーション")
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
        # クエリ文字列をURLエンコード
        encoded_address = urllib.parse.quote(user_address + ", 大分県日田市")
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={encoded_address}"
        
        # リクエストヘッダーにユーザーエージェントを追加
        headers = {'User-Agent': 'HitaCityHazardMapApp/1.0 (streamlit_app; developer@example.com)'}
        response = requests.get(url, headers=headers)
        
        # HTTPステータスコードを確認
        response.raise_for_status()
        
        geocode_result = response.json()

        if geocode_result:
            location = geocode_result[0]
            lat = float(location['lat'])
            lng = float(location['lon'])
            folium.Marker(
                [lat, lng],
                popup=user_address,
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)
            m.location = [lat, lng]
            m.zoom_start = 15
        else:
            st.error("住所が見つかりませんでした。別の住所を試してください。")
    except requests.exceptions.HTTPError as errh:
        st.error(f"HTTPエラーが発生しました: {errh}")
    except requests.exceptions.RequestException as erre:
        st.error(f"リクエストエラーが発生しました: {erre}")
    except ValueError as ve:
        st.error("レスポンスがJSON形式ではありませんでした。しばらく待ってから再度お試しください。")
    except Exception as e:
        st.error(f"予期せぬエラーが発生しました: {e}")

# ハザードマップのレイヤーを追加（ダミーデータ）
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