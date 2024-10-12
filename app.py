import streamlit as st
import pandas as pd
import os
from scrapingFunctions import (
    obter_gols_tempo_normal,
    salvar_dataframes_partidas_timesbr_2024,
    gerar_tabela_times_brasileiros,
    obter_tabela_rodada_com_selenium,
    urls_br_2024,
    nomes_times_br_2024
)

@st.cache(ttl=3600)
def carregar_dataframes():
    salvar_dataframes_partidas_timesbr_2024(urls_br_2024, nomes_times_br_2024)
    dfs = []
    for nome_time in nomes_times_br_2024:
        caminho_arquivo = fr'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2024\Temporada {nome_time} 2024.csv'
        
        # Verificar se o arquivo existe
        if os.path.exists(caminho_arquivo):
            df = pd.read_csv(caminho_arquivo)
            dfs.append(df)
        else:
            st.error(f"Arquivo {caminho_arquivo} não encontrado.")
    return dfs

# Carregar os DataFrames atualizados
dataframes_times_br_2024 = carregar_dataframes()

# Interface do app Streamlit
st.title("Aplicativo de análise da Temporada das Equipes - Futebol Brasileiro")

st.subheader(
    """
    Aqui, você pode ver todos os jogos da temporada de uma equipe, além de uma tabela de aproveitamento com informações de gols, gols sofridos, vitórias, derrotas, empates e aproveitamento filtrado por data, mando de campo ou campeonato.
    """
)

# Filtro para selecionar o time
time_selecionado = st.selectbox("Selecione o time", nomes_times_br_2024)
df_selecionado = dataframes_times_br_2024[nomes_times_br_2024.index(time_selecionado)]

# Exibir DataFrame do time selecionado
st.write(f"Dados para o time: {time_selecionado}")
st.dataframe(df_selecionado)
