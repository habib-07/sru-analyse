
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import os

# Telechargement automatique des donnees au demarrage
chemin = "donnees-sru-2025.csv"
df_raw = pd.read_csv(chemin, sep=";", encoding="latin-1", dtype=str)
df_raw.columns = [
    "zone","region","departement","code_dept","code_insee","nom_commune",
    "population","code_siren","nom_epci","epci_sru","code_uu","nom_uu",
    "uu_sru","com_isolee","sru_2025","sru_2024","nb_lls","taux_sru",
    "deficitaire","carencee","exemptee","taux_cible","prelevement"
]

dept_idf = ["75","77","78","91","92","93","94","95"]
df = df_raw[df_raw["code_dept"].isin(dept_idf)].copy()

df["nb_lls"]      = pd.to_numeric(df["nb_lls"].str.replace(" ",""), errors="coerce")
df["population"]  = pd.to_numeric(df["population"].str.replace(" ",""), errors="coerce")
df["taux_sru"]    = pd.to_numeric(df["taux_sru"].str.replace("%","").str.replace(",","."), errors="coerce")
df["taux_cible"]  = pd.to_numeric(df["taux_cible"].str.replace("%","").str.replace(",","."), errors="coerce")
df["prelevement"] = pd.to_numeric(
    df["prelevement"].str.replace("\x80","",regex=False).str.replace(" ","",regex=False).str.replace(",",".",regex=False).str.strip(),
    errors="coerce").fillna(0)
df["deficitaire"] = df["deficitaire"].str.strip()
df["carencee"]    = df["carencee"].str.strip()
df["exemptee"]    = df["exemptee"].str.strip()
df["logements_manquants"] = ((df["taux_cible"]/100*df["population"]-df["nb_lls"]).clip(lower=0).round(0))
df["ecart_taux"]  = (df["taux_cible"] - df["taux_sru"]).round(2)

dept_labels = {
    "75":"Paris","77":"Seine-et-Marne","78":"Yvelines",
    "91":"Essonne","92":"Hauts-de-Seine",
    "93":"Seine-Saint-Denis","94":"Val-de-Marne","95":"Val-d Oise"
}
depts = sorted(df["code_dept"].unique())

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server

sidebar = dbc.Card([
    html.H5("Filtres"),
    html.Hr(),
    html.Label("Departements"),
    dcc.Dropdown(
        id="filtre_dept",
        options=[{"label": f"{dept_labels.get(d,d)} ({d})", "value": d} for d in depts],
        value=list(depts), multi=True, clearable=False
    ),
    html.Br(),
    html.Label("Statut commune"),
    dcc.Dropdown(
        id="filtre_statut",
        options=[
            {"label": "Toutes",       "value": "all"},
            {"label": "Deficitaires", "value": "def"},
            {"label": "Carencees",    "value": "car"},
            {"label": "Exemptees",    "value": "exe"},
        ],
        value="all", clearable=False
    ),
    html.Br(),
    html.Label("Taux SRU max (%)"),
    dcc.Slider(id="filtre_taux", min=0, max=25, value=25, step=1,
               marks={0:"0%", 10:"10%", 20:"20%", 25:"25%"})
], body=True)

tabs = dbc.Tabs([
    dbc.Tab(label="Vue d ensemble", children=[
        dbc.Row([
            dbc.Col(dbc.Card(id="kpi_total", color="primary", inverse=True), width=3),
            dbc.Col(dbc.Card(id="kpi_def",   color="danger",  inverse=True), width=3),
            dbc.Col(dbc.Card(id="kpi_car",   color="warning", inverse=True), width=3),
            dbc.Col(dbc.Card(id="kpi_prel",  color="dark",    inverse=True), width=3),
        ], className="mt-3 mb-3"),
        dbc.Row([
            dbc.Col(dcc.Graph(id="p_taux_dist"),  width=7),
            dbc.Col(dcc.Graph(id="p_statut_pie"), width=5),
        ])
    ]),
    dbc.Tab(label="Classement communes", children=[
        dbc.Row([
            dbc.Col(dcc.Graph(id="p_top_deficit"), width=6),
            dbc.Col(dcc.Graph(id="p_top_prel"),    width=6),
        ], className="mt-3")
    ]),
    dbc.Tab(label="Par departement", children=[
        dbc.Row([
            dbc.Col(dcc.Graph(id="p_dept_taux"), width=6),
            dbc.Col(dcc.Graph(id="p_dept_prel"), width=6),
        ], className="mt-3"),
        dbc.Row([dbc.Col(dcc.Graph(id="p_scatter"), width=12)])
    ]),
])

app.layout = dbc.Container([
    dbc.Row([html.H2("Loi SRU — Communes deficitaires en Ile-de-France (2025)",
                     className="text-primary my-3")]),
    dbc.Row([
        dbc.Col(sidebar, width=3),
        dbc.Col(tabs,    width=9)
    ])
], fluid=True)

def get_df(depts_sel, statut, taux_max):
    d = df[df["code_dept"].isin(depts_sel) & (df["taux_sru"] <= taux_max)]
    if statut == "def": d = d[d["deficitaire"]=="1"]
    elif statut == "car": d = d[d["carencee"]=="1"]
    elif statut == "exe": d = d[d["exemptee"]=="1"]
    return d

@app.callback(
    Output("kpi_total","children"), Output("kpi_def","children"),
    Output("kpi_car","children"),   Output("kpi_prel","children"),
    Input("filtre_dept","value"), Input("filtre_statut","value"), Input("filtre_taux","value")
)
def kpis(depts_sel, statut, taux_max):
    d = get_df(depts_sel, statut, taux_max)
    def k(t,v): return dbc.CardBody([html.H6(t), html.H3(str(v))])
    return (k("Communes", len(d)),
            k("Deficitaires", (d["deficitaire"]=="1").sum()),
            k("Carencees",    (d["carencee"]=="1").sum()),
            k("Prelevement",  f"{d['prelevement'].sum()/1e6:.1f} M EUR"))

@app.callback(Output("p_taux_dist","figure"),
              Input("filtre_dept","value"), Input("filtre_statut","value"), Input("filtre_taux","value"))
def p_taux_dist(depts_sel, statut, taux_max):
    d = get_df(depts_sel, statut, taux_max)
    fig = px.histogram(d, x="taux_sru", nbins=30, color="deficitaire",
                       color_discrete_map={"1":"#A32D2D","0":"#1D9E75"},
                       title="Distribution des taux SRU",
                       labels={"taux_sru":"Taux SRU (%)","deficitaire":"Deficitaire"})
    fig.add_vline(x=20, line_dash="dash", line_color="orange", annotation_text="Seuil 20%")
    fig.add_vline(x=25, line_dash="dash", line_color="red",    annotation_text="Seuil 25%")
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(Output("p_statut_pie","figure"),
              Input("filtre_dept","value"), Input("filtre_statut","value"), Input("filtre_taux","value"))
def p_statut_pie(depts_sel, statut, taux_max):
    d = get_df(depts_sel, statut, taux_max)
    labels = ["Atteint objectif","Deficitaire","Carencee","Exemptee"]
    values = [
        ((d["deficitaire"]=="0") & (d["exemptee"]=="0")).sum(),
        ((d["deficitaire"]=="1") & (d["carencee"]=="0")).sum(),
        (d["carencee"]=="1").sum(),
        (d["exemptee"]=="1").sum()
    ]
    fig = px.pie(names=labels, values=values,
                 color_discrete_sequence=["#1D9E75","#EF9F27","#A32D2D","#888780"],
                 title="Repartition des communes")
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(Output("p_top_deficit","figure"),
              Input("filtre_dept","value"), Input("filtre_statut","value"), Input("filtre_taux","value"))
def p_top_deficit(depts_sel, statut, taux_max):
    d = get_df(depts_sel, statut, taux_max)
    d = d[d["deficitaire"]=="1"].nlargest(15,"logements_manquants")
    fig = px.bar(d, x="logements_manquants", y="nom_commune", orientation="h",
                 color="departement", title="Top 15 — Logements manquants",
                 labels={"logements_manquants":"Logements manquants","nom_commune":""})
    fig.update_layout(template="plotly_white", yaxis=dict(autorange="reversed"))
    return fig

@app.callback(Output("p_top_prel","figure"),
              Input("filtre_dept","value"), Input("filtre_statut","value"), Input("filtre_taux","value"))
def p_top_prel(depts_sel, statut, taux_max):
    d = get_df(depts_sel, statut, taux_max)
    d = d[d["prelevement"]>0].nlargest(15,"prelevement")
    fig = px.bar(d, x="prelevement", y="nom_commune", orientation="h",
                 color="departement", title="Top 15 — Prelevement SRU (EUR)",
                 labels={"prelevement":"Prelevement (EUR)","nom_commune":""})
    fig.update_layout(template="plotly_white", yaxis=dict(autorange="reversed"))
    return fig

@app.callback(Output("p_dept_taux","figure"),
              Input("filtre_dept","value"), Input("filtre_statut","value"), Input("filtre_taux","value"))
def p_dept_taux(depts_sel, statut, taux_max):
    d = get_df(depts_sel, statut, taux_max)
    d_grp = d.groupby("departement")["taux_sru"].mean().reset_index()
    fig = px.bar(d_grp, x="departement", y="taux_sru",
                 title="Taux SRU moyen par departement",
                 labels={"taux_sru":"Taux SRU moyen (%)","departement":""},
                 color="taux_sru", color_continuous_scale="RdYlGn")
    fig.add_hline(y=25, line_dash="dash", line_color="red", annotation_text="Objectif 25%")
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(Output("p_dept_prel","figure"),
              Input("filtre_dept","value"), Input("filtre_statut","value"), Input("filtre_taux","value"))
def p_dept_prel(depts_sel, statut, taux_max):
    d = get_df(depts_sel, statut, taux_max)
    d_grp = d.groupby("departement")["prelevement"].sum().reset_index()
    fig = px.bar(d_grp, x="departement", y="prelevement",
                 title="Prelevement SRU total par departement (EUR)",
                 labels={"prelevement":"Prelevement (EUR)","departement":""},
                 color="prelevement", color_continuous_scale="Reds")
    fig.update_layout(template="plotly_white")
    return fig

@app.callback(Output("p_scatter","figure"),
              Input("filtre_dept","value"), Input("filtre_statut","value"), Input("filtre_taux","value"))
def p_scatter(depts_sel, statut, taux_max):
    d = get_df(depts_sel, statut, taux_max)
    fig = px.scatter(d, x="taux_sru", y="logements_manquants",
                     size="population", color="departement",
                     hover_name="nom_commune",
                     hover_data=["taux_cible","prelevement"],
                     title="Taux SRU vs Logements manquants",
                     labels={"taux_sru":"Taux SRU (%)","logements_manquants":"Logements manquants"})
    fig.add_vline(x=25, line_dash="dash", line_color="red", annotation_text="Objectif 25%")
    fig.update_layout(template="plotly_white")
    return fig

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8055)))
