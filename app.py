import streamlit as st
import pandas as pd
import os
from scrapingFunctions import gerar_tabela_times_brasileiros

# Lista de nomes dos times
nomes_times_br_2024 = [
    "Fortaleza", "Botafogo", "Flamengo", "Palmeiras", "São Paulo", "Cruzeiro", "Bahia", "Athletico-PR", 
    "Atlético-MG", "Vasco da Gama", "Bragantino", "Internacional", "Juventude", "Grêmio", "Criciúma",
    "Vitória", "Corinthians", "Fluminense", "Cuiabá", "Atlético-GO"
]

# Função para carregar DataFrames atualizados sem scraping
def carregar_dataframes():
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
    Aqui, você pode ver todos os jogos da temporada de uma equipe, além de uma tabela de aproveitamento com informações de gols, 
    gols sofridos, vitórias, derrotas, empates e aproveitamento filtrado por data, mando de campo ou campeonato.
    """
)

# Filtro para selecionar o time
time_selecionado = st.selectbox("Selecione o time", nomes_times_br_2024)
df_selecionado = dataframes_times_br_2024[nomes_times_br_2024.index(time_selecionado)]

# Exibir DataFrame do time selecionado
st.write(f"Dados para o time: {time_selecionado}")
st.dataframe(df_selecionado)

# Filtros para a tabela de aproveitamento
st.header("Tabela de Aproveitamento")

# Data inicial e final
data_inicial = st.date_input("Data Inicial", value=pd.to_datetime("2024-01-01"))
data_final = st.date_input("Data Final", value=pd.to_datetime("2024-12-31"))

# Seleção de campeonatos
campeonatos = df_selecionado['Campeonato'].unique()  # Pegar campeonatos únicos do DataFrame
campeonatos_escolhidos = st.multiselect("Selecione os Campeonatos", campeonatos)

# Filtros para jogos em casa ou fora
apenas_jogos_casa = st.checkbox("Apenas Jogos em Casa")
apenas_jogos_visitante = st.checkbox("Apenas Jogos Fora")

# Gerar tabela de aproveitamento
if st.button("Gerar Tabela de Aproveitamento"):
    tabela_aproveitamento = gerar_tabela_times_brasileiros(
        [df_selecionado],  # Lista com o DataFrame do time selecionado
        [time_selecionado],  # Nome do time
        data_inicial=data_inicial.strftime('%d.%m.%y'),
        data_final=data_final.strftime('%d.%m.%y'),
        campeonatos_escolhidos=campeonatos_escolhidos,
        apenas_jogos_casa=apenas_jogos_casa,
        apenas_jogos_visitante=apenas_jogos_visitante
    )
    
    # Exibir a tabela de aproveitamento
    st.write(f"Tabela de Aproveitamento para o time: {time_selecionado}")
    st.dataframe(tabela_aproveitamento)
