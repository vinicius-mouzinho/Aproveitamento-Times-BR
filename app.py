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
    Veja todos os jogos da temporada de uma equipe ou uma tabela de aproveitamento geral com filtros e classificação por métrica disponíveis!
    """
)

# Exibir DataFrame de qualquer time (opcional)
time_selecionado = st.selectbox("Selecione o time para visualizar os jogos completos", nomes_times_br_2024)
df_selecionado = dataframes_times_br_2024[nomes_times_br_2024.index(time_selecionado)]

st.write(f"Dados para o time: {time_selecionado}")
st.dataframe(df_selecionado)

# Filtros para a tabela de aproveitamento
st.header("Tabela de Aproveitamento")

# Data inicial e final
data_inicial = st.date_input("Data Inicial", value=pd.to_datetime("2024-01-01"))
data_final = st.date_input("Data Final", value=pd.to_datetime("2024-12-31"))

# Seleção de campeonatos (com opção para selecionar todos)
campeonatos = pd.concat(dataframes_times_br_2024)['Campeonato'].unique()  # Pega campeonatos de todos os times
escolher_todos_campeonatos = st.checkbox("Selecionar todos os Campeonatos")

if escolher_todos_campeonatos:
    campeonatos_escolhidos = campeonatos.tolist()  # Converter para lista
else:
    campeonatos_escolhidos = st.multiselect("Selecione os Campeonatos", campeonatos)

# Filtros para jogos em casa ou fora
apenas_jogos_casa = st.checkbox("Apenas Jogos em Casa")
apenas_jogos_visitante = st.checkbox("Apenas Jogos Fora")

# Gerar tabela de aproveitamento para todos os times
if st.button("Gerar Tabela de Aproveitamento"):
    # Verificar se a lista de campeonatos não está vazia
    if len(campeonatos_escolhidos) > 0:
        tabela_aproveitamento = gerar_tabela_times_brasileiros(
            dataframes_times_br_2024,  # Todos os DataFrames dos times
            nomes_times_br_2024,  # Lista de todos os times
            data_inicial=data_inicial.strftime('%d.%m.%y'),
            data_final=data_final.strftime('%d.%m.%y'),
            campeonatos_escolhidos=campeonatos_escolhidos,
            apenas_jogos_casa=apenas_jogos_casa,
            apenas_jogos_visitante=apenas_jogos_visitante
        )
    
        # Exibir a tabela de aproveitamento para todos os times
        st.write("Tabela de Aproveitamento para todos os times")
        st.dataframe(tabela_aproveitamento)
    else:
        st.error("Por favor, selecione pelo menos um campeonato.")
