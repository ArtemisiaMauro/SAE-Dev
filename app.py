import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from streamlit_extras.metric_cards import style_metric_cards

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="FranceMetrics", layout="wide")

UNSPLASH_KEY = st.secrets.get("UNSPLASH_KEY", "")

CACHE_FILE = "city_images_cache.json"

# =========================
# DATA LOAD
# =========================
population = pd.read_excel("population.xlsx")
reg_dep = pd.read_excel("regions_departements.xlsx")
densite = pd.read_excel("densite.xlsx")
menages = pd.read_excel("menages.xlsx")
emploi = pd.read_excel("emploi.xlsx")
logements = pd.read_excel("logements.xlsx")

pop_merge = population.merge(reg_dep, on="Ville", how="left").merge(densite, on="Ville", how="left")

# =========================
# CACHE IMAGE
# =========================
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

city_image_cache = load_cache()

# =========================
# IMAGE UNSPLASH
# =========================
def get_city_image(city):
    if city in city_image_cache:
        return city_image_cache[city]

    url = "https://api.unsplash.com/search/photos"

    params = {
        "query": f"{city} france city",
        "per_page": 1,
        "orientation": "landscape"
    }

    headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()

        if data.get("results"):
            img = data["results"][0]["urls"]["regular"]
            city_image_cache[city] = img
            save_cache(city_image_cache)
            return img

    except:
        pass

    return None

def display_image(img):
    if img:
        st.image(img, use_container_width=True)
    else:
        st.image("https://via.placeholder.com/800x400?text=Image+indisponible")

def render_city_info(data):
    return f"""
    <div style="padding:10px">
        <h3>{data['Ville']}</h3>
        <p>Population : {data['Population']}</p>
        <p>Densité : {data['Densité de population']}</p>
    </div>
    """

# =========================
# SAFE ROW
# =========================
def safe_row(df, col, value):
    res = df[df[col] == value]
    if len(res) == 0:
        return None
    return res.iloc[0]

# =========================
# UI
# =========================
st.title("FranceMetrics")
st.subheader("Comparateur de villes")

st.caption(f"{len(population)} villes comparables")

col1, col2 = st.columns(2)

with col1:
    ville1 = st.selectbox("Ville 1", pop_merge["Ville"].unique())

with col2:
    ville2 = st.selectbox("Ville 2", pop_merge["Ville"].unique())

data1 = safe_row(pop_merge, "Ville", ville1)
data2 = safe_row(pop_merge, "Ville", ville2)

if data1 is None or data2 is None:
    st.error("Ville introuvable")
    st.stop()

# =========================
# IMAGES
# =========================
c1, c2 = st.columns(2)

with c1:
    st.subheader(ville1)
    display_image(get_city_image(ville1))
    st.markdown(render_city_info(data1), unsafe_allow_html=True)

with c2:
    st.subheader(ville2)
    display_image(get_city_image(ville2))
    st.markdown(render_city_info(data2), unsafe_allow_html=True)

# =========================
# METEO API SAFE
# =========================
@st.cache_data
def get_coords(city):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{city}, France", "format": "json", "limit": 1},
            headers={"User-Agent": "app"},
            timeout=10
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        pass
    return None, None

@st.cache_data
def get_history(city):
    lat, lon = get_coords(city)
    if lat is None:
        return None

    try:
        r = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "daily": "temperature_2m_mean",
                "timezone": "auto"
            },
            timeout=10
        )
        data = r.json()
        if "daily" in data:
            return data
    except:
        pass

    return None

def season_mean(m):
    df = pd.DataFrame({
        "Date": pd.to_datetime(m["daily"]["time"]),
        "Temp": m["daily"]["temperature_2m_mean"]
    })

    df["mois"] = df["Date"].dt.month

    def season(m):
        if m in [12,1,2]: return "Hiver"
        if m in [3,4,5]: return "Printemps"
        if m in [6,7,8]: return "Été"
        return "Automne"

    df["Saison"] = df["mois"].apply(season)

    return df.groupby("Saison")["Temp"].mean().reindex(
        ["Hiver","Printemps","Été","Automne"]
    )

# =========================
# METEO UI SAFE
# =========================
st.subheader("🌡️ Météo")

h1 = get_history(ville1)
h2 = get_history(ville2)

if h1 and h2:
    s1 = season_mean(h1)
    s2 = season_mean(h2)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=s1.index,
        y=s1.values,
        name=ville1
    ))

    fig.add_trace(go.Bar(
        x=s2.index,
        y=s2.values,
        name=ville2
    ))

    fig.update_layout(barmode="group")

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Météo indisponible")

# =========================
# FIN
# =========================
st.caption("FranceMetrics © 2026")
