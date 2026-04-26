import streamlit as st
import pandas as pd
import altair as alt
import requests
from streamlit_extras.metric_cards import style_metric_cards
import plotly.express as px
from geopy.geocoders import Nominatim
import plotly.graph_objects as go


population = pd.read_excel('population.xlsx')
reg_dep = pd.read_excel('regions_departements.xlsx')
densite = pd.read_excel('densite.xlsx')
menages = pd.read_excel('menages.xlsx')
emploi = pd.read_excel('emploi.xlsx')

colonnes_menage = ["Nombre de ménages", "Nombre de familles"]

for col in colonnes_menage:
    menages[col] = (
        menages[col]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.replace("\u202f", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.extract(r"(\d+\.?\d*)")[0]
        .pipe(pd.to_numeric, errors="coerce")
    )

logements = pd.read_excel("logements.xlsx")

colonnes_logement = [
    "Loyer d'annonce (appartement)",
    "Loyer d'annonce (maison)",
    "Nombre de logements",
    "Taux d'évolution",
    "Nombre de logements sociaux (RPLS)"
]

for col in colonnes_logement:
    logements[col] = (
        logements[col]
        .astype(str)
        .str.replace(" ", "", regex=False)
        .str.replace("\u202f", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.extract(r"(\d+\.?\d*)")[0]
        .pipe(pd.to_numeric, errors="coerce")
    )


pop_merge1 = population.merge(reg_dep, on="Ville", how="left")
pop_merge = pop_merge1.merge(densite, on="Ville", how="left")

st.title("FranceMetrics")
st.subheader("Comparateur de villes")
st.caption(f"Comparaison limitée aux villes de 20 000 habitants ou plus : {len(population["Ville"])} villes comparables.")

def render_city_info(data):
    html = f"<h2 style='margin-bottom:0'>{data['Ville']}</h2>"

    # Département + Région
    if pd.notna(data["Département"]) and pd.notna(data["Région"]):
        html += (
            f"<p style='color:gray; margin-top:0'>"
            f"{data['Département']}, {data['Région']}"
            f"</p>"
        )

    if pd.notna(data["Code INSEE"]):
        html += (
            f"<p style='color:gray; margin-top:0'>"
            f"Code INSEE : {data['Code INSEE']}"
            f"</p>"
        )

    return html

def get_city_image_url(city_name):
    query = f"{city_name} ville France"
    url = f"https://www.bing.com/images/search?q={query.replace(' ', '+')}"

    try:
        response = requests.get(url, timeout=5)
        html = response.text

        marker = "murl&quot;:&quot;"
        start = html.find(marker)
        if start == -1:
            return None

        start += len(marker)
        end = html.find("&quot;", start)
        img_url = html[start:end]

        if img_url.startswith("http") and (".jpg" in img_url or ".jpeg" in img_url or ".png" in img_url):
            return img_url

        return None

    except:
        return None

def display_city_image(img_url, width=350, height=220, radius=18):
    if img_url:
        st.markdown(
            f"""
            <div style="
                width:{width}px;
                height:{height}px;
                border-radius:{radius}px;
                overflow:hidden;
                box-shadow:0 4px 12px rgba(0,0,0,0.15);
                margin-bottom:10px;
            ">
                <img src="{img_url}" 
                     style="width:100%; height:100%; object-fit:cover; display:block;">
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.write("Photo indisponible")

col_select1, col_select2 = st.columns(2)

with col_select1:
    ville1 = st.selectbox(label="choix ville1", options=pop_merge["Ville"].sort_values().unique(), placeholder="Choisissez une ville", label_visibility="collapsed")

with col_select2:
    ville2 = st.selectbox(label="choix ville2", options=pop_merge["Ville"].sort_values().unique(), placeholder="Choisissez une ville", label_visibility="collapsed")

st.divider()

data1 = pop_merge[pop_merge["Ville"] == ville1].iloc[0]
data2 = pop_merge[pop_merge["Ville"] == ville2].iloc[0]

men1 = menages[menages["Ville"] == ville1].iloc[0]
men2 = menages[menages["Ville"] == ville2].iloc[0]

log1 = logements[logements["Ville"] == ville1].iloc[0]
log2 = logements[logements["Ville"] == ville2].iloc[0]

emp1 = emploi[emploi["Libellé"] == ville1].iloc[0]
emp2 = emploi[emploi["Libellé"] == ville2].iloc[0]

moy_loyer_app = round(logements["Loyer d'annonce (appartement)"].mean())
moy_loyer_mai = round(logements["Loyer d'annonce (maison)"].mean())
moy_nb_log = round(logements["Nombre de logements"].mean())
moy_nb_soc = round(logements["Nombre de logements sociaux (RPLS)"].mean())
moy_taux = round(logements["Taux d'évolution"].mean(), 2)

col1, col2 = st.columns(2)

with col1:
    st.badge("Ville 1", color="violet")
    img1 = get_city_image_url(data1["Ville"])
    display_city_image(img1)
    st.markdown(render_city_info(data1), unsafe_allow_html=True)

with col2:
    st.badge("Ville 2", color="violet")
    img2 = get_city_image_url(data2["Ville"])
    display_city_image(img2)
    st.markdown(render_city_info(data2), unsafe_allow_html=True)

densite["Densité de population"] = pd.to_numeric(
    densite["Densité de population"].astype(str).str.replace(" ", "").str.replace(",", "."),
    errors="coerce"
)

moyenne_population = population["Population"].mean()
moyenne_densite = densite["Densité de population"].mean()
moy_menages = menages["Nombre de ménages"].mean()
moy_familles = menages["Nombre de familles"].mean()

tab1, tab2, tab3, tab4 = st.tabs(["Démographie", "Emploi", "Logement", "Météo"])

with tab1:
    st.subheader("Population")

    col_fr1, col_fr2, col_fr3 = st.columns(3)
    col_fr2.metric("Moyenne française", f"{round(moyenne_population):,}".replace(",", " "))
    st.write("")

    col_pop1, col_pop2 = st.columns(2)
    with col_pop1:
        st.metric(
            label=f"{ville1}",
            value=f"{data1['Population']:,}".replace(",", " ")
        )

    with col_pop2:
        st.metric(
            label=f"{ville2}",
            value=f"{data2['Population']:,}".replace(",", " ")
        )

    style_metric_cards(
        background_color="#F8F8F8",
        border_left_color="#1F15A7",
        border_color="#E0E0E0",
        border_radius_px=10,
        box_shadow=True
    )

    st.caption("(Chiffres 2023, INSEE)")

    st.subheader("Densité de population")

    col_den1, col_den2, col_den3 = st.columns(3)
    col_den2.metric(label="Moyenne française", value=int(moyenne_densite))
    st.write("")

    col_den1, col_den2 = st.columns(2)
    with col_den1:
        st.metric(
            label=f"{ville1}",
            value=f"{data1['Densité de population']:,}".replace(",", " ")
        )
        st.write("Habitants/km²")

    with col_den2:
        st.metric(
            label=f"{ville2}",
            value=f"{data2['Densité de population']:,}".replace(",", " ")
        )
        st.write("Habitants/km²")

    st.caption("(Chiffres 2022, INSEE)")

    pop_age = pd.read_excel("population_tranches.xlsx")

    colonnes_age = [
        "Moins de 25 ans",
        "25 à 64 ans",
        "65 ans ou plus",
        "80 ans ou plus"
    ]

    for col in colonnes_age:
        pop_age[col] = (
            pop_age[col]
            .astype(str)
            .str.replace(" ", "")
            .str.replace(",", ".")
            .pipe(pd.to_numeric, errors="coerce")
        )


    moyennes_france = {
    "Ville": "France",
    "Moins de 25 ans": round(pop_age["Moins de 25 ans"].mean()),
    "25 à 64 ans": round(pop_age["25 à 64 ans"].mean()),
    "65 ans ou plus": round(pop_age["65 ans ou plus"].mean()),
    "80 ans ou plus": round(pop_age["80 ans ou plus"].mean())
    }



    pop_age = pd.concat([pop_age, pd.DataFrame([moyennes_france])], ignore_index=True)

    pop_age_graph = pop_age[pop_age["Ville"].isin([ville1, ville2, "France"])]

    pop_age_long = pop_age_graph.melt(
    id_vars="Ville",
    value_vars=[
        "Moins de 25 ans",
        "25 à 64 ans",
        "65 ans ou plus",
        "80 ans ou plus"
    ],
    var_name="Tranche d'âge",
    value_name="Population"
    )


    pop_age_long["Population"] = pd.to_numeric(pop_age_long["Population"], errors="coerce")

    fig_age = px.bar(
    pop_age_long,
    x="Tranche d'âge",
    y="Population",
    color="Ville",
    barmode="group",
    text_auto=True,
    title=None,
    color_discrete_map={
        ville1: "#1F15A7",
        ville2: "#76D8FF",
        "France": "#FFB000"
    }
    )

    fig_age.update_traces(textposition="outside")

    st.subheader("Répartition de la population par tranche d'âge")

    st.plotly_chart(fig_age, use_container_width=True)

    st.caption("(Chiffres 2022, INSEE)")

    st.subheader("Ménages et familles")

    col_menfr1, col_menfr2 = st.columns(2)
    with col_menfr1:
        st.metric(label="Nombre de ménages - Moyenne française", value=round(moy_menages))

    with col_menfr2:
        st.metric(label="Nombre de familles - Moyenne française", value=round(moy_familles))

    st.write("")

    col_men1, col_men2 = st.columns(2)

    with col_men1:
        st.metric(
            label=f"Nombre de ménages - {ville1}",
            value=f"{int(men1['Nombre de ménages']):,}".replace(",", " ")
        )
        st.metric(
            label=f"Nombre de familles - {ville1}",
            value=f"{int(men1['Nombre de familles']):,}".replace(",", " ")
        )

    with col_men2:
        st.metric(
            label=f"Nombre de ménages - {ville2}",
            value=f"{int(men2['Nombre de ménages']):,}".replace(",", " ")
        )
        st.metric(
            label=f"Nombre de familles - {ville2}",
            value=f"{int(men2['Nombre de familles']):,}".replace(",", " ")
        )


    st.caption("(Chiffres 2022, INSEE)")

    st.divider()

    st.info("Sources")
    st.write("Insee - Statistiques locales")
    st.write("Observatoire des territoires")


with tab2:
    st.header("Emploi")

    # Colonnes à convertir en numérique
    colonnes_emploi = [
        "Part des 25-34 ans titulaires d'un diplôme de l'enseignement supérieur 2022",
        "Taux d'activité des 15-64 ans 2022 Ensemble",
        "Taux de chômage des 15-64 ans (RP) 2022 Ensemble",
        "Taux de chômage des 15-64 ans (RP) 2022 Femmes",
        "Taux de chômage des 15-64 ans (RP) 2022 Hommes",
        "Taux de croissance des effectifs dans les établissements d'enseignement supérieur au cours des 10 dernières années Total des formations d'enseignement supérieur",
        "Part des 20-24 ans sans diplôme 2022"
    ]

    for col in colonnes_emploi:
        emploi[col] = (
            emploi[col]
            .astype(str)
            .str.replace(" ", "", regex=False)
            .str.replace(",", ".", regex=False)
            .pipe(pd.to_numeric, errors="coerce")
        )

    # Moyennes France
    moy_diplome = round(emploi["Part des 25-34 ans titulaires d'un diplôme de l'enseignement supérieur 2022"].mean(), 1)
    moy_activite = round(emploi["Taux d'activité des 15-64 ans 2022 Ensemble"].mean(), 1)
    moy_chomage = round(emploi["Taux de chômage des 15-64 ans (RP) 2022 Ensemble"].mean(), 1)
    moy_sans_diplome = round(emploi["Part des 20-24 ans sans diplôme 2022"].mean(), 1)

    # --------------------------
    # Activité
    # --------------------------
    st.subheader("Taux d'activité des 15-64 ans")

    col1, col2, col3 = st.columns(3)
    with col2:
        st.metric("Moyenne française", f"{moy_activite} %")

    c1, c2 = st.columns(2)
    with c1:
        st.metric(ville1, f"{emp1["Taux d'activité des 15-64 ans 2022 Ensemble"]} %")
    with c2:
        st.metric(ville2, f"{emp2["Taux d'activité des 15-64 ans 2022 Ensemble"]} %")

    st.caption("(Chiffres 2022, INSEE)")

    # --------------------------
    # Comparaison activité H/F
    # --------------------------
    colonnes = [
        "Taux d'activité des 15-64 ans 2022 Femmes",
        "Taux d'activité des 15-64 ans 2022 Hommes"
    ]

    for col in colonnes:
        emploi[col] = (
            emploi[col]
            .astype(str)
            .str.replace(" ", "")
            .str.replace("%", "")
            .str.replace(",", ".")
            .pipe(pd.to_numeric, errors="coerce")
        )
    
    st.subheader("Activité femmes / hommes")

    # Moyennes France
    moy_act_f = round(
        emploi["Taux d'activité des 15-64 ans 2022 Femmes"].mean(), 1
    )

    moy_act_h = round(
        emploi["Taux d'activité des 15-64 ans 2022 Hommes"].mean(), 1
    )

    # DataFrame graphique avec France ajoutée
    df_activ = pd.DataFrame([
        {"Ville": ville1, "Catégorie": "Femmes", "Valeur": emp1["Taux d'activité des 15-64 ans 2022 Femmes"]},
        {"Ville": ville1, "Catégorie": "Hommes", "Valeur": emp1["Taux d'activité des 15-64 ans 2022 Hommes"]},

        {"Ville": ville2, "Catégorie": "Femmes", "Valeur": emp2["Taux d'activité des 15-64 ans 2022 Femmes"]},
        {"Ville": ville2, "Catégorie": "Hommes", "Valeur": emp2["Taux d'activité des 15-64 ans 2022 Hommes"]},

        {"Ville": "France", "Catégorie": "Femmes", "Valeur": moy_act_f},
        {"Ville": "France", "Catégorie": "Hommes", "Valeur": moy_act_h},
    ])

    fig_activ = px.bar(
        df_activ,
        x="Catégorie",
        y="Valeur",
        color="Ville",
        barmode="group",
        text_auto=True,
        color_discrete_map={
            ville1: "#1F15A7",
            ville2: "#76D8FF",
            "France": "#FFB000"
        }
    )

    fig_activ.update_traces(textposition="outside")
    fig_activ.update_layout(bargap=0.25)

    st.plotly_chart(fig_activ, use_container_width=True)

    # --------------------------
    # Chômage
    # --------------------------
    st.subheader("Taux de chômage")

    col1, col2, col3 = st.columns(3)
    with col2:
        st.metric("Moyenne française", f"{moy_chomage} %")

    c1, c2 = st.columns(2)
    with c1:
        st.metric(ville1, f"{emp1['Taux de chômage des 15-64 ans (RP) 2022 Ensemble']} %")
    with c2:
        st.metric(ville2, f"{emp2['Taux de chômage des 15-64 ans (RP) 2022 Ensemble']} %")

    st.caption("(Chiffres 2022, INSEE)")

    # --------------------------
    # Comparaison chômage H/F
    # --------------------------
    st.subheader("Chômage femmes / hommes")

    # Moyennes France
    moy_chom_f = round(
        emploi["Taux de chômage des 15-64 ans (RP) 2022 Femmes"].mean(), 1
    )

    moy_chom_h = round(
        emploi["Taux de chômage des 15-64 ans (RP) 2022 Hommes"].mean(), 1
    )

    # DataFrame graphique avec France ajoutée
    df_chomage = pd.DataFrame([
        {"Ville": ville1, "Catégorie": "Femmes", "Valeur": emp1["Taux de chômage des 15-64 ans (RP) 2022 Femmes"]},
        {"Ville": ville1, "Catégorie": "Hommes", "Valeur": emp1["Taux de chômage des 15-64 ans (RP) 2022 Hommes"]},

        {"Ville": ville2, "Catégorie": "Femmes", "Valeur": emp2["Taux de chômage des 15-64 ans (RP) 2022 Femmes"]},
        {"Ville": ville2, "Catégorie": "Hommes", "Valeur": emp2["Taux de chômage des 15-64 ans (RP) 2022 Hommes"]},

        {"Ville": "France", "Catégorie": "Femmes", "Valeur": moy_chom_f},
        {"Ville": "France", "Catégorie": "Hommes", "Valeur": moy_chom_h},
    ])

    fig_chomage = px.bar(
        df_chomage,
        x="Catégorie",
        y="Valeur",
        color="Ville",
        barmode="group",
        text_auto=True,
        color_discrete_map={
            ville1: "#1F15A7",
            ville2: "#76D8FF",
            "France": "#FFB000"
        }
    )

    fig_chomage.update_traces(textposition="outside")
    fig_chomage.update_layout(bargap=0.25)

    st.plotly_chart(fig_chomage, use_container_width=True)

    st.caption("(Chiffres 2022, INSEE)")

    # --------------------------
    # Diplômés supérieur
    # --------------------------
    st.subheader("25-34 ans diplômés du supérieur")

    col1, col2, col3 = st.columns(3)
    with col2:
        st.metric("Moyenne française", f"{moy_diplome} %")

    c1, c2 = st.columns(2)
    with c1:
        st.metric(ville1, f"{emp1["Part des 25-34 ans titulaires d'un diplôme de l'enseignement supérieur 2022"]} %")
    with c2:
        st.metric(ville2, f"{emp2["Part des 25-34 ans titulaires d'un diplôme de l'enseignement supérieur 2022"]} %")

    st.caption("(Chiffres 2022, INSEE)")

    # --------------------------
    # Sans diplôme
    # --------------------------
    st.subheader("20-24 ans sans diplôme")

    col1, col2, col3 = st.columns(3)
    with col2:
        st.metric("Moyenne française", f"{moy_sans_diplome} %")

    c1, c2 = st.columns(2)
    with c1:
        st.metric(ville1, f"{emp1["Part des 20-24 ans sans diplôme 2022"]} %")
    with c2:
        st.metric(ville2, f"{emp2["Part des 20-24 ans sans diplôme 2022"]} %")

    st.caption("(Chiffres 2022, INSEE)")

    st.divider()

    st.info("Sources")
    st.write("Insee - Statistiques locales")
    st.write("Observatoire des territoires")



with tab3:
    st.header("Logement")
    st.subheader("Loyer d'annonce par m² (€/m²)")
    st.write("Charges comprises, parc privé locatif")
    col_log1, col_log2 = st.columns(2)

    with col_log1:
        st.metric("Loyer appartement - Moyenne française", moy_loyer_app)

    with col_log2:
        st.metric("Loyer maison - Moyenne française", moy_loyer_mai)
    
    st.write("")

    col_l1, col_l2 = st.columns(2)

    with col_l1:
        st.metric(f"Loyer appartement - {ville1}", f"{log1[f"Loyer d'annonce (appartement)"]}")
        st.metric(f"Loyer maison (€/m²) - {ville1}", f"{log1[f"Loyer d'annonce (maison)"]}")

    with col_l2:
        st.metric(f"Loyer appartement - {ville2}", f"{log2[f"Loyer d'annonce (appartement)"]}")
        st.metric(f"Loyer maison - {ville2}", f"{log2[f"Loyer d'annonce (maison)"]}")

    st.caption("(Chiffres 2025, Observatoire des territoires)")

    st.subheader("Nombre de logements et logements sociaux")

    df_log = pd.DataFrame([
        {"Ville": ville1, "Indicateur": "Logements", "Nombre": log1["Nombre de logements"]},
        {"Ville": ville1, "Indicateur": "Logements sociaux", "Nombre": log1["Nombre de logements sociaux (RPLS)"]},
        {"Ville": ville2, "Indicateur": "Logements", "Nombre": log2["Nombre de logements"]},
        {"Ville": ville2, "Indicateur": "Logements sociaux", "Nombre": log2["Nombre de logements sociaux (RPLS)"]},
        {"Ville": "France", "Indicateur": "Logements", "Nombre": moy_nb_log},
        {"Ville": "France", "Indicateur": "Logements sociaux", "Nombre": moy_nb_soc},
    ])

    fig_log = px.bar(
        df_log,
        x="Indicateur",
        y="Nombre",
        color="Ville",
        barmode="group",
        text_auto=True,
        title=None,
        color_discrete_map={
            ville1: "#1F15A7",
            ville2: "#76D8FF",
            "France": "#FFB000"
        }
    )

    fig_log.update_traces(textposition="outside")
    fig_log.update_layout(bargap=0.25)

    st.plotly_chart(fig_log, use_container_width=True)
    st.caption("(Chiffres 2022 et 2023, Observatoire des territoires)")


    st.subheader("Taux d'évolution du nombre de logements")

    col_tauxfr1, col_tauxfr2, col_tauxfr3 = st.columns(3)

    with col_tauxfr2:
        st.metric("Moyenne française", f"{moy_taux} %")

    st.write("")

    col_t1, col_t2 = st.columns(2)

    with col_t1:
        st.metric(f"{ville1}", f"{log1[f"Taux d'évolution"]} %")

    with col_t2:
        st.metric(f"{ville2}", f"{log2[f"Taux d'évolution"]} %")

    st.caption("(Chiffres 2022, Observatoire des territoires)")

    st.divider()

    st.info("Sources")
    st.write("Insee - Statistiques locales")
    st.write("Observatoire des territoires")


with tab4:
    st.header("Météo")

    # =========================
    # COORDONNÉES + HISTORIQUE
    # =========================
    @st.cache_data
    def get_coords(ville):
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": f"{ville}, France", "format": "json", "limit": 1}
        headers = {"User-Agent": "FranceMetricsApp"}

        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None


    @st.cache_data(ttl=86400)
    def get_history(ville):
        lat, lon = get_coords(ville)
        if lat is None:
            return None

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "daily": "temperature_2m_mean",
            "timezone": "auto"
        }

        return requests.get(url, params=params).json()


    # =========================
    # SAISONS (CLIMAT)
    # =========================
    def season_mean(meteo):
        df = pd.DataFrame({
            "Date": pd.to_datetime(meteo["daily"]["time"]),
            "Temp": meteo["daily"]["temperature_2m_mean"]
        })

        df["Mois"] = df["Date"].dt.month

        def season(m):
            if m in [12, 1, 2]:
                return "Hiver"
            elif m in [3, 4, 5]:
                return "Printemps"
            elif m in [6, 7, 8]:
                return "Été"
            else:
                return "Automne"

        df["Saison"] = df["Mois"].apply(season)

        return df.groupby("Saison")["Temp"].mean().reindex(
            ["Hiver", "Printemps", "Été", "Automne"]
        )


    # =========================
    # PARTIE CLIMAT
    # =========================
    st.subheader("🌡️ Température moyenne par saison")

    hist1 = get_history(ville1)
    hist2 = get_history(ville2)

    s1 = season_mean(hist1)
    s2 = season_mean(hist2)

    saisons = ["Hiver", "Printemps", "Été", "Automne"]

    fig1 = go.Figure()

    fig1.add_trace(go.Bar(
        x=saisons,
        y=s1.values,
        name=ville1,
        marker_color="#1F15A7",
        text=[f"{v:.1f}°C" for v in s1.values],
        textposition="outside"
    ))

    fig1.add_trace(go.Bar(
        x=saisons,
        y=s2.values,
        name=ville2,
        marker_color="#76D8FF",
        text=[f"{v:.1f}°C" for v in s2.values],
        textposition="outside"
    ))

    fig1.update_layout(barmode="group")

    st.plotly_chart(fig1, use_container_width=True)


    # =========================
    # PRÉVISIONS (APRES)
    # =========================
    def get_forecast(ville):
        lat, lon = get_coords(ville)
        if lat is None:
            return None

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto"
        }

        return requests.get(url, params=params).json()

    st.subheader("📈 Prévisions 7 jours")

    choix = st.selectbox(
        "Indicateur prévisions",
        ["Température moyenne", "Vent (km/h)", "Pluie (mm/j)"]
    )

    mapping = {
        "Température moyenne": "temperature_2m_mean",
        "Vent (km/h)": "wind_speed_10m_max",
        "Pluie (mm/j)": "precipitation_sum"
    }

    def get_forecast(ville):
        lat, lon = get_coords(ville)

        if lat is None:
            return None

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": (
                "temperature_2m_mean,"
                "precipitation_sum,"
                "wind_speed_10m_max"
            ),
            "timezone": "auto"
        }

        return requests.get(url, params=params).json()


    meteo1 = get_forecast(ville1)
    meteo2 = get_forecast(ville2)

    if meteo1 and meteo2:

        col = mapping[choix]

        df = pd.concat([
            pd.DataFrame({
                "Date": meteo1["daily"]["time"],
                "Valeur": meteo1["daily"][col],
                "Ville": ville1
            }),
            pd.DataFrame({
                "Date": meteo2["daily"]["time"],
                "Valeur": meteo2["daily"][col],
                "Ville": ville2
            })
        ])

        fig2 = px.line(
            df,
            x="Date",
            y="Valeur",
            color="Ville",
            markers=True,
            color_discrete_map={
                ville1: "#1F15A7",
                ville2: "#76D8FF"
            }
        )

        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.error("Données météo indisponibles")

    meteo1 = get_forecast(ville1)
    meteo2 = get_forecast(ville2)

    st.divider()

    st.info("Sources")
    st.write("API open-meteo ARCHIVES")
    st.write("API open-meteo FORECAST")


st.caption("© 2026 FranceMetrics. Créé par Ayah Belamfedel-Alaoui et Artemisia Mauro. Données publiques officielles.")