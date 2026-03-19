# SRU Analyse — Communes déficitaires en Île-de-France

Dashboard interactif d'analyse de la loi SRU (Solidarité et Renouvellement Urbain) en Île-de-France, développé en Python à partir des données officielles data.gouv.fr (2025).

##  Lien de l'application
L'application est déployée sur Render et consultable ici : 👉 [https://sru-idf.onrender.com/] 

## Objectifs

- Visualiser les communes déficitaires en logements sociaux en IDF
- Identifier les communes carencées et leur prélèvement SRU
- Analyser l'écart entre taux réel et objectif légal (20% ou 25%)
- Comparer les départements franciliens

## Dashboard

3 onglets interactifs avec filtres (département, statut, taux SRU) :

- **Vue d ensemble** — KPIs, distribution des taux SRU, répartition des statuts
- **Classement communes** — Top 15 logements manquants, top 15 prélèvements
- **Par département** — Taux moyen, prélèvement total, scatter plot

## Stack technique

- Python : pandas, plotly, dash, dash-bootstrap-components
- Données : Inventaire SRU 2025 — data.gouv.fr
- Déploiement : Render

## Données sources

Télécharger sur data.gouv.fr :
https://www.data.gouv.fr/datasets/communes-et-inventaire-sru

## Auteur

Habib Laskin KPENGOU — Data Analyst, données territoriales
DRIEAT Île-de-France
linkedin.com/in/kpengou-habib-laskin-4b772a201
