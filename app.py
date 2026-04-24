import streamlit as st
import pandas as pd
import altair as alt
import os
import plotly.express as px

st.sidebar.title("Filtres")

villes_disponibles = ["Annemasse", "Brest", "Montauban"]
villes_affichees = st.sidebar.multiselect(
    "Choisissez les villes à comparer :",
    villes_disponibles,
    default=villes_disponibles[:2],
    max_selections=3
)

st.title("Outil comparatif de villes en France")
st.info("Ce site permet de comparer des indicateurs clés sur la démographie, le logement, l'emploi et la météo de plusieurs villes de France.")


meteo = pd.read_excel('Meteo.xlsx')
previsions = pd.read_excel('Meteo_Previsions.xlsx')
effectifs = pd.read_excel('Emploi.xlsx', sheet_name="effectifs")
tranches_ages = pd.read_excel('Emploi.xlsx', sheet_name="tranches_age")
actifs_age = pd.read_excel('Emploi.xlsx', sheet_name="actifs_tranches_age")
vulnerabilite = pd.read_excel('Emploi.xlsx', sheet_name="vulnérabilité")
education = pd.read_excel('Emploi.xlsx', sheet_name="education")
formations = pd.read_excel('Emploi.xlsx', sheet_name="formations")
ef_entreprises = pd.read_excel('Emploi.xlsx', sheet_name="effectifs_entreprises")
poids_secteurs = pd.read_excel('Emploi.xlsx', sheet_name="poids_secteurs")

st.header("DÉMOGRAPHIE & LOGEMENT")
tabD1, tabD2 = st.tabs(["Démographie", "Logement"])

import os

BASE_DIR = os.path.dirname(__file__)
logement_path = os.path.join(BASE_DIR, "logement.csv")
demo_path = os.path.join(BASE_DIR, "demo_prpre.xlsx")
log_path = os.path.join(BASE_DIR, "log_prpre.xlsx")

log2 = pd.read_excel(log_path, engine="openpyxl")
logement = pd.read_csv(logement_path, sep=";", encoding="latin-1")
demo = pd.read_excel(demo_path, engine="openpyxl")

logement["agglomeration"] = logement["agglomeration"].astype(str).str.strip()
for col in ["loyer_moyen", "Surface moyenne (m²)"]:
    logement[col] = pd.to_numeric(
        logement[col].astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )

demo_melt = demo.melt(
    id_vars=["Categorie", "Indicateur"],
    var_name="Ville",
    value_name="Valeur"
)

with tabD1:

    st.subheader("📊 Indicateurs démographiques")

    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        categorie = st.selectbox(
            "Catégorie",
            demo_melt["Categorie"].unique()
        )

        df_demo = demo_melt[
            (demo_melt["Categorie"] == categorie) &
            (demo_melt["Ville"].isin(villes_affichees))
        ]

        fig_demo = px.bar(
            df_demo,
            x="Indicateur",
            y="Valeur",
            color="Ville",
            barmode="group",
            text_auto=True,
            title=f"{categorie} — comparaison"
        )

        st.plotly_chart(fig_demo, use_container_width=True)

        st.divider()

        st.subheader("Heatmap")

        heat = demo_melt.pivot_table(
            index="Indicateur",
            columns="Ville",
            values="Valeur"
        )

        fig_heat = px.imshow(
            heat,
            text_auto=True,
            aspect="auto",
            title="Indicateurs supplémentaires"
        )

        st.plotly_chart(fig_heat, use_container_width=True)

        st.divider()

with tabD2:

    st.subheader("🏠 Logement")

    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        df_log = logement[logement["agglomeration"].isin(villes_affichees)]

        cols = st.columns(len(villes_affichees))

        for col, ville in zip(cols, villes_affichees):
            data = df_log[df_log["agglomeration"] == ville]

            if not data.empty:
                loyer = data["Moyenne loyer mensuel"].mean()
                loyer_m2 = data["loyer_moyen"].mean()

                with col:
                    st.metric(
                        label=f"{ville} — Loyer mensuel moyen",
                        value=f"{loyer:.2f} €"
                    )
                    st.caption(f"Loyer moyen au m² : {loyer_m2:.2f} €/m²")

        st.divider()

        metric = st.selectbox(
            "Indicateur logement",
            ["Moyenne loyer mensuel", "Surface moyenne (m²)"]
        )

        df_plot = df_log.groupby(["agglomeration", "Type_habitat"], as_index=False).agg(
            valeur=(metric, "mean")
        )

        fig_log = px.bar(
            df_plot,
            x="agglomeration",
            y="valeur",
            color="Type_habitat",
            barmode="group",
            text_auto=".2f",
            title="Comparaison logement"
        )

        st.plotly_chart(fig_log, use_container_width=True)

        st.divider()
        colonnes_villes = [c for c in log2.columns if c not in ["Catégorie", "Indicateur"]]

        colonnes_filtrees = [v for v in villes_affichees if v in colonnes_villes]

        if len(colonnes_filtrees) == 0:
            st.warning("Aucune des villes sélectionnées n'existe dans log2.")
        else:
            df_long = log2.melt(
                id_vars=["Categorie", "Indicateur"],
                value_vars=colonnes_filtrees,
                var_name="Ville",
                value_name="Valeur"
            )

            indicateur_sel = st.selectbox(
                "Indicateurs",
                df_long["Indicateur"].unique()
            )

            df_indic = df_long[df_long["Indicateur"] == indicateur_sel]

            fig_log2 = px.bar(
                df_indic,
                x="Ville",
                y="Valeur",
                color="Ville",
                text_auto=True,
                title=f"{indicateur_sel} — comparaison"
            )

            st.plotly_chart(fig_log2, use_container_width=True)



st.header("💼 EMPLOI")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Population", "Éducation", "Secteurs et entreprises", "Économie", "Accès à l'emploi"])

with tab1:
    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        effectifs_filtre = effectifs[effectifs["Territoire"].isin(villes_affichees)]

    col5, col6 = st.columns(2)

    col5.subheader("Distribution")
    age_filtre = tranches_ages[tranches_ages["Territoire"].isin(villes_affichees)]
    age_pivot = age_filtre.pivot(
        index="Tranches",
        columns="Territoire",
        values="Pourcentage Habitants"
    )

    col5.bar_chart(age_pivot, stack=False, y_label="Population (%)")

    col6.subheader("Distribution (actifs)")
    actifs_filtre = actifs_age[actifs_age["Territoire"].isin(villes_affichees)]
    actifs_pivot = actifs_filtre.pivot(
        index="Tranches",
        columns="Territoire",
        values="Pourcentage Actifs"
    )

    col6.bar_chart(actifs_pivot, stack=False, y_label="Population (%)")

with tab2:
    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        st.subheader("Niveau de diplôme")

        education_filtre = education[education["Territoire"].isin(villes_affichees)]

        ordre_diplomes = [
            "< CAP-BEP",
            "CAP-BEP",
            "Bac",
            "Bac + 2",
            "bac+3 / bac+4",
            ">= Bac + 5"
        ]

        education_filtre["Niveau de diplôme"] = pd.Categorical(
            education_filtre["Niveau de diplôme"],
            categories=ordre_diplomes,
            ordered=True
        )

        education_filtre = education_filtre.sort_values("Niveau de diplôme")

        education_filtre["Pourcentage Population"] = (
            education_filtre["Pourcentage Population"]
            .astype(float)
        )

        chart = (
            alt.Chart(education_filtre)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "Niveau de diplôme:N",
                    title=None,
                    axis=alt.Axis(labelLimit=0)
                ),
                x=alt.X(
                    "Pourcentage Population:Q",
                    title="Population (%)"
                ),
                color=alt.Color("Territoire:N", legend=None),
                tooltip=["Territoire", "Niveau de diplôme", "Pourcentage Population"]
            )
            .properties(height=200)
            .facet(
                row="Territoire:N"
            )
        )

        st.altair_chart(chart, use_container_width=True)

with tab3:
    st.subheader("Effectifs des établissements")

    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        cols = st.columns(len(villes_affichees))

        for col, ville in zip(cols, villes_affichees):
            ligne = ef_entreprises[
                ef_entreprises["Territoire"] == ville
            ]

            if not ligne.empty:
                eff_etab = ligne["Effectif Établissements"].iloc[0]
                evolu_ent = ligne["Evolution / 2022"].iloc[0]

                with col:
                    st.metric(
                        label=ville,
                        value=f"{eff_etab}",
                        delta=f"{evolu_ent:+.1f} %"
                    )

        st.subheader("Répartition par secteur")

        colA, colB = st.columns(2)

        df = poids_secteurs[poids_secteurs["Territoire"].isin(villes_affichees)].copy()

        df["Pourcentage Établissements"] = (
            df["Pourcentage Établissements"]
            .astype(str)
            .str.replace(",", ".")
            .str.replace("%", "")
            .astype(float)
        )

        df["Pourcentage Salariés"] = (
            df["Pourcentage Salariés"]
            .astype(str)
            .str.replace(",", ".")
            .str.replace("%", "")
            .astype(float)
        )

        with colA:
            st.write("**% d’établissements par secteur**")

            chart_etab = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    y=alt.Y("Secteur:N", title=None, axis=alt.Axis(labelLimit=0)),
                    x=alt.X("Pourcentage Établissements:Q", title="Pourcentage (%)"),
                    color=alt.Color("Territoire:N", legend=None),
                    tooltip=["Territoire", "Secteur", "Pourcentage Établissements"],
                )
                .properties(height=200)
                .facet(row="Territoire:N")
            )

            st.altair_chart(chart_etab, use_container_width=True)

        with colB:
            st.write("**% de salariés par secteur**")

            chart_sal = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    y=alt.Y("Secteur:N", title=None, axis=alt.Axis(labelLimit=0)),
                    x=alt.X("Pourcentage Salariés:Q", title="Pourcentage (%)"),
                    color=alt.Color("Territoire:N", legend=None),
                    tooltip=["Territoire", "Secteur", "Pourcentage Salariés"],
                )
                .properties(height=200)
                .facet(row="Territoire:N")
            )

            st.altair_chart(chart_sal, use_container_width=True)




with tab4:
    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        st.subheader(f"Taux de pauvreté au seuil de 60% du revenu médian")
        cols = st.columns(len(villes_affichees))

        for col, ville in zip(cols, villes_affichees):

            ligne = vulnerabilite[
                (vulnerabilite["Territoire"] == ville) &
                (vulnerabilite["Vulnérabilité"].str.contains("60%", case=False))
            ]

            if not ligne.empty:
                valeur = (
                    ligne["Pourcentage Population"].iloc[0]
                )
                valeur = float(valeur)

                with col:
                    st.metric(
                        label=ville,
                        value=f"{valeur} %"
                    )

        st.subheader("Imposition")

        tab_vul = vulnerabilite[
            (vulnerabilite["Territoire"].isin(villes_affichees)) &
            (vulnerabilite["Vulnérabilité"].str.contains("impos", case=False))
        ]
        
        tab_vul2 = tab_vul.copy()
        tab_vul2["Pourcentage Population"] = (
            tab_vul2["Pourcentage Population"]
            .astype(float)
        )

        st.dataframe(
            tab_vul2[["Territoire", "Vulnérabilité", "Pourcentage Population"]],
            use_container_width=True,
            column_config={"Pourcentage Population": "Population (%)"}
        )


with tab5:
    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        st.subheader("Taux d'accès à l'emploi après formation")
        st.write("Par domaine")

        form_filtre = formations[formations["Territoire"].isin(villes_affichees)]

        # Nettoyage du pourcentage
        form_filtre["Taux (%)"] = (
            form_filtre["Taux (%)"]
            .astype(str)
            .str.replace("%", "")
            .str.replace(",", ".")
            .astype(float)
        )

        chart = (
            alt.Chart(form_filtre)
            .mark_bar()
            .encode(
                y=alt.Y("Domaines de formation:N", title=None, axis=alt.Axis(labelLimit=0)),
                x=alt.X("Taux (%):Q", title="Taux (%)"),
                color=alt.Color("Territoire:N", legend=None),
                tooltip=["Territoire", "Domaines de formation", "Taux (%)"],
            )
            .properties(height=200)
            .facet(
                row="Territoire:N"
            )
        )

        st.altair_chart(chart, use_container_width=True)


st.header("🌦️ MÉTÉO")

tab8, tab9 = st.tabs(["Prévision", "Tendance"])

with tab8:
    st.subheader("Prévisions de la semaine prochaine")

    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        previsions["DATE"] = pd.to_datetime(previsions["DATE"])
        dates_disponibles = previsions["DATE"].sort_values().unique()
        first_date = dates_disponibles[0]

        date_selection = st.date_input(
            "Choisissez une date",
            value=dates_disponibles[0],
            min_value=dates_disponibles[0],
            max_value=dates_disponibles[-1]
        )

        def delta_vs_veille(ville, temp_today):
            if pd.to_datetime(date_selection) == first_date:
                valeurs_init = {"Montauban": 27, "Annemasse": 24, "Brest": 21}
                prev = valeurs_init.get(ville, temp_today)
            else:
                prev_date = pd.to_datetime(date_selection) - pd.Timedelta(days=1)
                ligne_prev = previsions[
                    (previsions["DATE"] == prev_date) &
                    (previsions["VILLE"] == ville)
                ]
                prev = ligne_prev["MAXIMALE"].iloc[0] if not ligne_prev.empty else temp_today
            return temp_today - prev

        cols = st.columns(len(villes_affichees))

        for col, ville in zip(cols, villes_affichees):
            ligne = previsions[
                (previsions["DATE"] == pd.to_datetime(date_selection)) &
                (previsions["VILLE"] == ville)
            ]

            if not ligne.empty:
                temp = ligne["MAXIMALE"].iloc[0]
                vent = ligne["VENT"].iloc[0]
                delta = delta_vs_veille(ville, temp)

                with col:
                    st.metric(
                        label=ville,
                        value=f"{temp} °C",
                        delta=f"{delta:+.1f} °C"
                    )
                    st.caption(f"Vent : {vent} km/h")
    
    st.divider()


with tab9:
    col3, col4 = st.columns(2)
    col3.subheader("Archives 2025")

    if len(villes_affichees) == 0:
        st.caption("Aucune ville sélectionnée.")
    else:
        variables = {
            "Température max (°C)": "MAX_TEMPERATURE_C",
            "Température min (°C)": "MIN_TEMPERATURE_C",
            "Vent max (km/h)": "WINDSPEED_MAX_KMH",
            "Précipitations (mm)": "PRECIP_TOTAL_DAY_MM",
            "Humidité max (%)": "HUMIDITY_MAX_PERCENT",
            "Couverture nuageuse (%)": "CLOUDCOVER_AVG_PERCENT",
            "Neige (mm)": "TOTAL_SNOW_MM",
            "Indice UV": "UV_INDEX"
        }

        choix_label = col4.selectbox("Choisissez un critère météorologique :", list(variables.keys()))
        choix = variables[choix_label]

        meteo_avg = (
            meteo.groupby(["VILLE", "MOIS"], as_index=False)
            .agg({choix: "mean"})
        )

        meteo_filtre = meteo_avg[meteo_avg["VILLE"].isin(villes_affichees)]
        meteo_pivot = meteo_filtre.pivot(index="MOIS", columns="VILLE", values=choix)

        st.line_chart(meteo_pivot, x_label="Mois")

    st.divider()

st.caption("Sources : France Travail, Data Gouv, Insee, Météo France, Historique Météo")