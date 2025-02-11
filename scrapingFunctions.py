import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
from io import StringIO
from datetime import datetime

def obter_gols_tempo_normal(driver, url_jogo):
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            driver.get(url_jogo)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Localizar a div com id "sb-tore" dentro de "sb-ereignisse"
            div_gols = soup.find('div', id='sb-tore', class_='sb-ereignisse')
            
            if div_gols:
                # Contar os gols para cada time dentro desta div
                gols_casa = len(div_gols.find_all('li', class_='sb-aktion-heim'))
                gols_visitante = len(div_gols.find_all('li', class_='sb-aktion-gast'))
                return f"{gols_casa}:{gols_visitante}"
            else:
                # Se a div não existe, considerar como 0:0
                return "0:0"
        except Exception as e:
            print(f"Tentativa {attempt+1} falhou ao acessar {url_jogo}: {e}")
            if attempt < max_attempts - 1:
                time.sleep(5)  # Esperar 5 segundos antes de tentar novamente
            else:
                return "Erro"

def salvar_dataframes_partidas_timesbr_2025(urls, nomes_times):
    # Configuração do Selenium para usar o Chrome
    service = Service(executable_path='C:/Users/chromedriver.exe')
    driver = webdriver.Chrome(service=service)

    # Iterar sobre cada time e processar seu respectivo link
    for url, nome_time in zip(urls, nomes_times):
        print(f"Processando o time: {nome_time}")

        # Acessar a página inicial do time
        driver.get(url)
        driver.implicitly_wait(10)

        # Obter o conteúdo da página
        html = driver.page_source

        # Parsear o HTML com BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Encontrar todas as tabelas na página
        tables = soup.find_all('table')

        if len(tables) >= 2:
            # Selecionar a segunda tabela
            table = tables[1]
            
            current_championship = None
            rows = []
            
            for tr in table.find_all('tr'):
                cells = tr.find_all(['td', 'th'])
                row = [cell.text.strip() for cell in cells]
                
                # Verificar se algum 'td' tem a classe específica
                championship_cell = tr.find('td', class_='extrarow bg_blau_20 hauptlink')
                if championship_cell:
                    current_championship = championship_cell.text.strip()
                
                # Adicionar a coluna 'Campeonato' com o valor atual
                if current_championship:
                    row.insert(0, current_championship)
                
                rows.append(row)
            
            # Criar o DataFrame sem especificar os cabeçalhos primeiro
            df = pd.DataFrame(rows)
            
            # Verificar se a primeira linha parece ser o cabeçalho
            if df.iloc[1].str.match(r'^[A-Za-z]').all():
                headers = ['Campeonato'] + df.iloc[1, 1:].tolist()
                
                # Tornar os nomes dos cabeçalhos únicos
                headers = [f'{header}_{i+1}' if headers.count(header) > 1 else header for i, header in enumerate(headers)]
                
                df = df[2:]
                df.columns = headers
                df.reset_index(drop=True, inplace=True)
            
            # Remover a segunda coluna
            df.drop(df.columns[1], axis=1, inplace=True)

            # Remover as colunas 'None_4', 'None_5', 'None_7', 'None_11'
            columns_to_remove = ['None_4', 'None_5', 'None_7', 'None_11']
            df.drop(columns=[col for col in columns_to_remove if col in df.columns], axis=1, inplace=True)

            # Renomear as colunas conforme solicitado, incluindo 'None_12' para 'Resultado'
            df.rename(columns={
                'None_3': 'Data',
                'None_6': 'Time da casa',
                'None_8': 'Time visitante',
                'None_9': 'Formação',
                'None_10': 'Técnico',
                'None_12': 'Resultado'
            }, inplace=True)

            # Remover parênteses e números dentro deles nos valores de 'Time da casa' e 'Time visitante'
            df['Time da casa'] = df['Time da casa'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', x) if isinstance(x, str) else x)
            df['Time visitante'] = df['Time visitante'].apply(lambda x: re.sub(r'\s*\(.*?\)', '', x) if isinstance(x, str) else x)

            # Verificação para identificar jogos com "pen."
            responsive_table_div = soup.find('div', class_='responsive-table')

            if responsive_table_div:
                tbody = responsive_table_div.find('table').find('tbody')

                if tbody:
                    for i, row in df.iterrows():
                        resultado = row['Resultado']
                        if isinstance(resultado, str) and 'pen.' in resultado:
                            print(f"Jogo com 'pen.' encontrado: Data: {row['Data']}, Resultado: {row['Resultado']}")
                            data_jogo = row['Data']

                            # Iterar sobre os elementos <tr style> para encontrar o tr correto
                            for tr in tbody.find_all('tr', style=True):
                                tds = tr.find_all('td', class_='zentriert')
                                for td in tds:
                                    if td.text.strip() == data_jogo:
                                        print(f"tr_jogo encontrado para a data {data_jogo}.")
                                        # Encontrar o link para a ficha do jogo
                                        td_ficha_jogo = tr.find('a', title='Ficha de jogo')
                                        if td_ficha_jogo:
                                            link_ficha_jogo = "https://www.transfermarkt.com.br" + td_ficha_jogo['href']
                                            print(f"Link para a ficha do jogo: {link_ficha_jogo}")
                                            # Obter o número correto de gols no tempo normal
                                            resultado_correto = obter_gols_tempo_normal(driver, link_ficha_jogo)
                                            if resultado_correto == "Erro":
                                                print(f"Erro ao acessar o link do jogo: {link_ficha_jogo}")
                                            else:
                                                df.at[i, 'Resultado'] = resultado_correto
                                        break
                                else:
                                    continue
                                break
                            else:
                                print(f"tr_jogo NÃO encontrado para a data {data_jogo}.")
                else:
                    print("tbody não encontrado dentro da tabela.")
            else:
                print("Div 'responsive-table' não encontrada.")

            # Remover linhas onde o valor de 'Resultado' é '-:-'
            df = df[df['Resultado'] != '-:-']
            df = df[df['Resultado'] != 'adiado']

            # Remover linhas onde o valor de 'Data' é None
            df.dropna(subset=['Data'], inplace=True)

            # Criar colunas 'Gols Casa' e 'Gols Visitante' a partir da coluna 'Resultado'
            df[['Gols Casa', 'Gols Visitante']] = df['Resultado'].str.extract(r'(\d+):(\d+)').astype(int)

            # Criar a coluna 'Nome Time Vitorioso'
            df['Nome Time Vitorioso'] = df.apply(
                lambda row: row['Time da casa'] if row['Gols Casa'] > row['Gols Visitante'] else
                            (row['Time visitante'] if row['Gols Visitante'] > row['Gols Casa'] else 'Empate'),
                axis=1
            )

            # Manter a coluna 'Resultado'
            # Salvar o DataFrame em um arquivo CSV na pasta especificada
            caminho_arquivo = fr'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada {nome_time} 2025.csv'
            df.to_csv(caminho_arquivo, index=False)
            print(f"DataFrame do time {nome_time} salvo em: {caminho_arquivo}")
        else:
            print(f"Menos de duas tabelas encontradas na página para o time {nome_time}.")

    # Fechar o navegador apenas no final do processo
    driver.quit()

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

        # Adicionar os resultados à lista de resultados
        resultados.append({
            'Time': time,
            'Partidas': partidas,
            'Vitórias': vitorias,
            'Empates': empates,
            'Derrotas': derrotas,
            'Gols Marcados': total_gols_marcados,
            'Gols Sofridos': total_gols_sofridos,
            'Pontos': pontos,
            'Aproveitamento (%)': round(aproveitamento, 2)  # Arredondar para 2 casas decimais
        })

    # Criar o DataFrame final a partir da lista de resultados
    tabela_final = pd.DataFrame(resultados)

    return tabela_final

def obter_tabela_rodada_com_selenium(rodada):
    # Configuração do Selenium para usar o Chrome
    service = Service(executable_path='C:/Users/chromedriver.exe')
    driver = webdriver.Chrome(service=service)

    tabelas = []

    for ano_base in range(2003, 2025):
        # Ajuste do saison_id (ano_base) para que corresponda à temporada correta
        saison_id = ano_base - 1  # saison_id sempre será um ano antes da temporada real

        # Construir a URL com os parâmetros corretos
        url = f"https://www.transfermarkt.com.br/campeonato-brasileiro-serie-a/spieltagtabelle/wettbewerb/BRA1?saison_id={saison_id}&spieltag={rodada}"
        print(f"Acessando a tabela da temporada {ano_base} na rodada {rodada}...")

        # Acessar a página com o Selenium
        driver.get(url)
        time.sleep(3)  # Esperar um pouco para garantir que a página carregue completamente

        try:
            # Encontrar a div com id 'yw1' que contém a tabela
            div_tabela = driver.find_element(By.CSS_SELECTOR, '#yw1 > table')

            # Obter o HTML da tabela
            html_tabela = div_tabela.get_attribute('outerHTML')

            # Parsear o HTML com BeautifulSoup
            soup = BeautifulSoup(html_tabela, 'html.parser')

            # Envolver o HTML em um StringIO para passar para read_html
            df = pd.read_html(StringIO(str(soup)))[0]
            
            # Adicionar a coluna "Temporada"
            df['Temporada'] = f"{ano_base}"
            
            # Adicionar a tabela à lista de tabelas
            tabelas.append(df)
            print(f"Tabela da temporada {ano_base} na rodada {rodada} obtida com sucesso.")
        
        except Exception as e:
            print(f"Erro ao tentar acessar a tabela da temporada {ano_base} na rodada {rodada}: {e}")

    # Fechar o navegador
    driver.quit()

    # Concatenar todas as tabelas em um único DataFrame
    tabela_final = pd.concat(tabelas, ignore_index=True) if tabelas else pd.DataFrame()

    # Modificações solicitadas
    if 'Clube' in tabela_final.columns:
        tabela_final.drop(columns=['Clube'], inplace=True)  # Remover a coluna "Clube"
    if 'Clube.1' in tabela_final.columns:
        tabela_final.rename(columns={'Clube.1': 'Clube'}, inplace=True)  # Renomear "Clube.1" para "Clube"
    if 'Unnamed: 3' in tabela_final.columns:
        tabela_final.rename(columns={'Unnamed: 3': 'J'}, inplace=True)  # Renomear "Unnamed: 3" para "J"

    tabela_final['Gols_Marcados'] = tabela_final['Gols'].apply(lambda x: int(x.split(':')[0]) if isinstance(x, str) else 0)

    return tabela_final


urls_br_2025 = [
    "https://www.transfermarkt.com.br/fortaleza-ec/spielplandatum/verein/10870/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/botafogo-fr/spielplandatum/verein/537/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/cr-flamengo/spielplandatum/verein/614/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/se-palmeiras/spielplandatum/verein/1023/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/sao-paulo-fc/spielplandatum/verein/585/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/cruzeiro-ec/spielplandatum/verein/609/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/ec-bahia/spielplandatum/verein/10010/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/atletico-mineiro/spielplandatum/verein/330/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/cr-vasco-da-gama/spielplandatum/verein/978/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/rb-bragantino/spielplandatum/verein/8793/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/sc-internacional/spielplandatum/verein/6600/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/ec-juventude/spielplandatum/verein/10492/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/gremio-fbpa/spielplandatum/verein/210/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/ec-vitoria/spielplandatum/verein/2125/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/sc-corinthians/spielplandatum/verein/199/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/fluminense-fc/spielplandatum/verein/2462/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/santos-fc/spielplandatum/verein/221/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/ceara-sc/spielplandatum/verein/2029/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/sport-recife/spielplandatum/verein/8718/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1",
    "https://www.transfermarkt.com.br/mirassol-fc/spielplandatum/verein/3876/saison_id/2024/wettbewerb_id//datum_von/0000-00-00/datum_bis/0000-00-00/day/0/plus/1"
]

nomes_times_br_2025 = [
    "Fortaleza", "Botafogo", "Flamengo", "Palmeiras", "São Paulo", "Cruzeiro", "Bahia", "Atlético-MG", "Vasco da Gama",
    "Bragantino", "Internacional", "Juventude", "Grêmio", "Vitória", "Corinthians", "Fluminense", "Santos", "Ceará", "Sport", "Mirassol"
]

df_fortaleza = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Fortaleza 2025.csv')
df_botafogo = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Botafogo 2025.csv')
df_flamengo = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Flamengo 2025.csv')
df_palmeiras = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Palmeiras 2025.csv')
df_sao_paulo = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada São Paulo 2025.csv')
df_cruzeiro = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Cruzeiro 2025.csv')
df_bahia = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Bahia 2025.csv')
df_atletico_mg = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Atlético-MG 2025.csv')
df_vasco_da_gama = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Vasco da Gama 2025.csv')
df_bragantino = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Bragantino 2025.csv')
df_internacional = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Internacional 2025.csv')
df_juventude = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Juventude 2025.csv')
df_gremio = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Grêmio 2025.csv')
df_vitoria = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Vitória 2025.csv')
df_corinthians = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Corinthians 2025.csv')
df_fluminense = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Fluminense 2025.csv')
df_santos = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Santos 2025.csv')
df_ceara = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Ceará 2025.csv')
df_sport = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Sport 2025.csv')
df_mirassol = pd.read_csv(r'C:\Users\Anderson\Football Analytics Docs\Temporada Times Brasileiros 2025\Temporada Mirassol 2025.csv')

dataframes_times_br_2025 = [df_fortaleza, df_botafogo, df_flamengo, df_palmeiras, df_sao_paulo, df_cruzeiro, df_bahia,
              df_atletico_mg, df_vasco_da_gama, df_bragantino, df_internacional, df_juventude, df_gremio,
              df_vitoria, df_corinthians, df_fluminense, df_santos, df_ceara, df_sport, df_mirassol]  # Lista de DataFrames dos times