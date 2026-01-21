import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import unicodedata

st.set_page_config(layout="wide", page_title="Resultados Eleições SC 2022")

def limpar(texto):
    return "".join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper().strip()

@st.cache_data
def carregar_mapa():
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-42-mun.json"
    mapa = requests.get(url).json()
    for feature in mapa['features']:
        feature['properties']['name_limpo'] = limpar(feature['properties']['name'])
    return mapa

@st.cache_data
def carregar_votos():
    df = pd.read_csv("votos_sc_todos_cargos.csv")
    if 'NM_MUNICIPIO_LIMPO' not in df.columns:
        df['NM_MUNICIPIO_LIMPO'] = df['NM_MUNICIPIO'].apply(limpar)
    return df

def categorizar_votos(votos):
    if votos == 0: return "0 voto"
    elif 1 <= votos <= 99: return "1 a 99 votos"
    elif 100 <= votos <= 199: return "100 a 199 votos"
    elif 200 <= votos <= 299: return "200 a 299 votos"
    elif 300 <= votos <= 399: return "300 a 399 votos"
    elif 400 <= votos <= 499: return "400 a 499 votos"
    elif 500 <= votos <= 999: return "500 a 999 votos"
    elif 1000 <= votos <= 1999: return "1000 a 1999 votos"
    elif 2000 <= votos <= 4999: return "2000 a 4999 votos"
    else: return "Acima de 5000 votos"

st.title("🗳️ Analisador Eleitoral - Santa Catarina 2022")

try:
    mapa_sc = carregar_mapa()
    df = carregar_votos()

    # --- BARRA LATERAL ---
    st.sidebar.header("Filtros")
    
    # 1. Seleção de Cargo
    lista_cargos = sorted(df['DS_CARGO'].unique())
    cargo_sel = st.sidebar.selectbox("Escolha o Cargo:", lista_cargos)
    df_cargo = df[df['DS_CARGO'] == cargo_sel]

    # 2. Seleção de Candidato para o Mapa
    lista_candidatos = sorted(df_cargo['NM_URNA_CANDIDATO'].unique())
    cand_sel = st.sidebar.selectbox("Candidato no Mapa:", lista_candidatos)

    # 3. Seleção de Município (SC como padrão)
    lista_municipios = ["SC"] + sorted(df['NM_MUNICIPIO_LIMPO'].unique().tolist())
    municipio_sel = st.sidebar.selectbox("Ver Top 10 de:", lista_municipios, index=0)

    # --- MAPA ---
    df_mapa = df_cargo[df_cargo['NM_URNA_CANDIDATO'] == cand_sel].copy()
    df_mapa['Faixa de Votos'] = df_mapa['QT_VOTOS_NOMINAIS'].apply(categorizar_votos)

    ordem_cats = ["0 voto", "1 a 99 votos", "100 a 199 votos", "200 a 299 votos", "300 a 399 votos", 
                  "400 a 499 votos", "500 a 999 votos", "1000 a 1999 votos", "2000 a 4999 votos", "Acima de 5000 votos"]
    
    cores_azul = {"0 voto": "#f7fbff", "1 a 99 votos": "#deebf7", "100 a 199 votos": "#c6dbef", 
                  "200 a 299 votos": "#9ecae1", "300 a 399 votos": "#6baed6", "400 a 499 votos": "#4292c6", 
                  "500 a 999 votos": "#2171b5", "1000 a 1999 votos": "#08519c", "2000 a 4999 votos": "#08306b", 
                  "Acima de 5000 votos": "#041e42"}

    fig_mapa = px.choropleth(
        df_mapa, geojson=mapa_sc, locations='NM_MUNICIPIO_LIMPO', featureidkey="properties.name_limpo",
        color='Faixa de Votos', color_discrete_map=cores_azul, category_orders={"Faixa de Votos": ordem_cats},
        hover_name='NM_MUNICIPIO_LIMPO', title=f"Distribuição de Votos em SC: {cand_sel}"
    )
    fig_mapa.update_geos(fitbounds="locations", visible=False)
    fig_mapa.update_layout(height=600, margin={"r":0,"t":50,"l":0,"b":0})
    st.plotly_chart(fig_mapa, use_container_width=True)

    # --- GRÁFICO DE BARRAS (TOP 10) ---
    st.markdown("---")
    
    if municipio_sel == "SC":
        df_top = df_cargo.groupby('NM_URNA_CANDIDATO')['QT_VOTOS_NOMINAIS'].sum().reset_index()
        titulo_barras = f"Top 10 Candidatos - Geral SC ({cargo_sel})"
    else:
        df_top = df_cargo[df_cargo['NM_MUNICIPIO_LIMPO'] == municipio_sel]
        titulo_barras = f"Top 10 Candidatos em {municipio_sel} ({cargo_sel})"

    top_10 = df_top.sort_values(by='QT_VOTOS_NOMINAIS', ascending=False).head(10)

    fig_barras = px.bar(
        top_10, x='QT_VOTOS_NOMINAIS', y='NM_URNA_CANDIDATO', orientation='h',
        title=titulo_barras, labels={'QT_VOTOS_NOMINAIS': 'Votos', 'NM_URNA_CANDIDATO': 'Candidato'},
        text='QT_VOTOS_NOMINAIS'
    )
    fig_barras.update_traces(textposition='outside', marker_color='#2171b5')
    fig_barras.update_layout(yaxis={'categoryorder':'total ascending'}, height=500)
    
    st.plotly_chart(fig_barras, use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}. Verifique se rodou o limpar_dados.py primeiro.")