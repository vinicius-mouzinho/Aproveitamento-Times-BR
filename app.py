import streamlit as st
import pandas as pd
import os

# Lista de nomes dos times
nomes_times_br_2025 = [
    "Fortaleza", "Botafogo", "Flamengo", "Palmeiras", "São Paulo", "Cruzeiro", "Bahia", "Atlético-MG", "Vasco da Gama",
    "Bragantino", "Internacional", "Juventude", "Grêmio", "Vitória", "Corinthians", "Fluminense", "Santos", "Ceará", "Sport", "Mirassol"
]

# Função para carregar DataFrames a partir dos arquivos CSV na pasta local do projeto
def carregar_dataframes():
    dfs = []
    for nome_time in nomes_times_br_2025:
        caminho_arquivo = f'data/Temporada {nome_time} 2025.csv'  # Assumindo que você tenha uma pasta "data" no projeto
        
        # Verificar se o arquivo existe
        if os.path.exists(caminho_arquivo):
            df = pd.read_csv(caminho_arquivo)
            dfs.append(df)
        else:
            st.error(f"Arquivo {caminho_arquivo} não encontrado.")
    return dfs

def gerar_tabela_times_brasileiros(dataframes, nomes_times, data_inicial=None, data_final=None, campeonatos_escolhidos=None, apenas_jogos_casa=None, apenas_jogos_visitante=None):
    # Criação de uma lista para armazenar os resultados
    resultados = []

    # Loop para processar cada DataFrame e calcular as estatísticas
    for df, time in zip(dataframes, nomes_times):
        # Filtrar pelos campeonatos escolhidos, se fornecidos
        if campeonatos_escolhidos:
            if isinstance(campeonatos_escolhidos, list):
                df = df[df['Campeonato'].isin(campeonatos_escolhidos)].copy()
            else:
                df = df[df['Campeonato'] == campeonatos_escolhidos].copy()

        # Converter a coluna de data para o formato datetime e filtrar por datas, se fornecidas
        df['Data'] = pd.to_datetime(df['Data'].str[4:], format='%d/%m/%y')
        
        if data_inicial:
            data_inicial = pd.to_datetime(data_inicial, format='%d.%m.%y')
            df = df[df['Data'] >= data_inicial]
        if data_final:
            data_final = pd.to_datetime(data_final, format='%d.%m.%y')
            df = df[df['Data'] <= data_final]

        # Filtrar apenas jogos em casa, se solicitado
        if apenas_jogos_casa:
            df = df[df['Time da casa'] == time]
        
        # Filtrar apenas jogos como visitante, se solicitado
        if apenas_jogos_visitante:
            df = df[df['Time visitante'] == time]

        # Contagem de gols marcados
        gols_casa = df[df['Time da casa'] == time]['Gols Casa'].sum()
        gols_visitante = df[df['Time visitante'] == time]['Gols Visitante'].sum()
        total_gols_marcados = gols_casa + gols_visitante

        # Contagem de gols sofridos
        gols_sofridos_casa = df[df['Time da casa'] == time]['Gols Visitante'].sum()
        gols_sofridos_visitante = df[df['Time visitante'] == time]['Gols Casa'].sum()
        total_gols_sofridos = gols_sofridos_casa + gols_sofridos_visitante

        # Contagem de vitórias
        vitorias = len(df[df['Nome Time Vitorioso'] == time])

        # Contagem de empates
        empates = len(df[df['Nome Time Vitorioso'] == 'Empate'])

        # Contagem de derrotas
        derrotas = len(df) - (vitorias + empates)  # Total de jogos - (vitórias + empates)

        # Contagem de partidas
        partidas = len(df)

        # Cálculo do aproveitamento (percentual)
        pontos = (vitorias * 3) + (empates * 1)
        aproveitamento = (pontos / (partidas * 3)) * 100 if partidas > 0 else 0

        # Cálculo dos gols marcados e sofridos por partida
        gols_marcados_por_partida = total_gols_marcados / partidas if partidas > 0 else 0
        gols_sofridos_por_partida = total_gols_sofridos / partidas if partidas > 0 else 0
        
        # Cálculo da sequência invicta
        sequencia_invicta = 0
        contador = 0
        for index, row in df.iterrows():
            if row['Nome Time Vitorioso'] == time or row['Nome Time Vitorioso'] == 'Empate':
                contador += 1
            else:
                contador = 0
            sequencia_invicta = contador

        jogos_sem_sofrer_gols = 0
        contador_jsg = 0
        for index, row in df.iterrows():
            if row['Time da Casa'] == time:
                if row['Gols Visitante'] == 0:
                    contador_jsg += 1
            else:
                if row['Gols Casa'] == 0:
                    contador_jsg += 1
            jogos_sem_sofrer_gols = contador_jsg

        # Adicionar os resultados à lista de resultados
        resultados.append({
            'Time': time,
            'Partidas': partidas,
            'Vitórias': vitorias,
            'Empates': empates,
            'Derrotas': derrotas,
            'Gols Marcados': total_gols_marcados,
            'Gols Sofridos': total_gols_sofridos,
            'Gols Marcados por Partida': round(gols_marcados_por_partida, 2),
            'Gols Sofridos por Partida': round(gols_sofridos_por_partida, 2),
            'Pontos': pontos,
            'Aproveitamento (%)': round(aproveitamento, 2),  # Arredondar para 2 casas decimais
            'Sequência Invicta': sequencia_invicta,
            'Jogos sem sofrer gol': jogos_sem_sofrer_gols
        })

    # Criar o DataFrame final a partir da lista de resultados
    tabela_final = pd.DataFrame(resultados)

    return tabela_final

# Carregar os DataFrames atualizados
dataframes_times_br_2025 = carregar_dataframes()

# Interface do app Streamlit
st.title("Aplicativo de análise da Temporada das Equipes - Futebol Brasileiro")

st.subheader(
    """
    Aqui, você pode ver todos os jogos da temporada de uma equipe, além de uma tabela de aproveitamento com informações de gols, 
    gols sofridos, vitórias, derrotas, empates e aproveitamento filtrado por data, mando de campo ou campeonato.
    """
)

# Exibir DataFrame de qualquer time (opcional)
time_selecionado = st.selectbox("Selecione o time para visualizar os jogos completos", nomes_times_br_2025)
df_selecionado = dataframes_times_br_2025[nomes_times_br_2025.index(time_selecionado)]

st.write(f"Dados para o time: {time_selecionado}")
st.dataframe(df_selecionado)

# Filtros para a tabela de aproveitamento
st.header("Tabela de Aproveitamento")

# Data inicial e final
data_inicial = st.date_input("Data Inicial", value=pd.to_datetime("2025-01-01"))
data_final = st.date_input("Data Final", value=pd.to_datetime("2025-12-31"))

# Seleção de campeonatos (com opção para selecionar todos)
campeonatos = pd.concat(dataframes_times_br_2025)['Campeonato'].unique()  # Pega campeonatos de todos os times
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
            dataframes_times_br_2025,  # Todos os DataFrames dos times
            nomes_times_br_2025,  # Lista de todos os times
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
