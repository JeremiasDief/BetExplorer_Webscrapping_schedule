from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from datetime import date, timedelta
import pandas as pd
import numpy as np
import subprocess

CHROME_VERSION = '114.0.5735'
CHROMEDRIVER_URL = f'https://chromedriver.storage.googleapis.com/{CHROME_VERSION}/chromedriver_linux64.zip'

# Credenciais
login = "jeremias_dief"
password = "BetExplorer2023"

# Iniciar medição de tempo
start_time = time.time()

# Use o Chromedriver manualmente
#driver_path = './chromedriver'  # Defina o caminho onde o arquivo chromedriver está localizado
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--remote-debugging-port=9222')

# Configurar o WebDriver usando webdriver-manager
# service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(options=options)

hoje = date.today()#-timedelta(1)
hoje_ano = hoje.year
hoje_mes = hoje.month
hoje_dia = hoje.day

# Lista para armazenar os dados
data = []

try:
    # Acessar a página inicial
    driver.get("https://www.betexplorer.com/?year=2024&month=5&day=24")

    # Aceitar cookies se a mensagem aparecer
    try:
        accept_cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Aceito']"))
        )
        accept_cookies_button.click()
    except:
        print("Não foi encontrado o botão de aceitar cookies")
        pass

    # Ajustar o timezone
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="js-timezone"]'))
    ).click()
    
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="js-timezone"]/ul/li[21]/button'))
    ).click()

    # Clicar no botão de login
    login_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="js-header"]/div[1]/div/div/ul/li[1]/a'))
    )
    login_button.click()

    # Preencher o formulário de login
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="login_nick"]'))
    )
    password_field = driver.find_element(By.XPATH, '//*[@id="login_pass"]')
    username_field.send_keys(login)
    password_field.send_keys(password)

    # Clicar no botão de login
    login_submit = driver.find_element(By.XPATH, '//*[@id="js-window-action-login"]')
    login_submit.click()

    # Adicionar um tempo de espera após o login
    time.sleep(5)  # Esperar 5 segundos após o login

    # Verificar se o login foi bem-sucedido e a página está completamente carregada
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="nr-ko-all"]'))
    )

    print("Login realizado com sucesso.")

    # Obter o código-fonte da página após o login
    page_source = driver.page_source

    # Criar o objeto BeautifulSoup
    site = BeautifulSoup(page_source, 'html.parser')

    # Encontrar o novo elemento 'nr-ko-all'
    next_matches_table = site.find('div', attrs={'id': 'nr-ko-all'})

    # Encontrar todas as ligas favoritas e seus jogos
    leagues = next_matches_table.find_all('ul', class_='leagues-list topleague')
    for league in leagues:
        favourite_star = league.find('a', class_='myleague active table-main__FavouriteStar')
        if favourite_star:
            country = league.find('p', class_='table-main__truncate table-main__leaguesNames leaguesNames').get_text(strip=True).split(': ')[0]
            league_name = league.find('p', class_='table-main__truncate table-main__leaguesNames leaguesNames').get_text(strip=True).split(': ')[1]

            matches = league.find_all('ul', class_='table-main__matchInfo')
            for match in matches:
                if match.find('span', class_='table-main__matchHour matchDateStatus'):
                    match_hour = match.find('span', class_='table-main__matchHour matchDateStatus').get_text(strip=True)
                    status = True
                else:
                    match_hour = match.find('span', class_='table-main__matchStatus matchDateStatus').get_text(strip=True)
                    status = False
                home_team = match.find('div', class_='participantsHomeAwayMobileWidth table-main__participantHome participantHomeOrder').find('p').get_text(strip=True)
                away_team = match.find('div', class_='participantsHomeAwayMobileWidth table-main__participantAway').find('p').get_text(strip=True)

                odds = match.find_all('div', class_='table-main__odds table-main__odd oddMobile')
                for i, odd in enumerate(odds):
                    if i == 0:
                        odd_home = odd.find('button').get_text(strip=True) if status else odd.find('p').get_text(strip=True)
                    elif i == 1:
                        odd_draw = odd.find('button').get_text(strip=True) if status else odd.find('p').get_text(strip=True)
                    elif i == 2:
                        odd_away = odd.find('button').get_text(strip=True) if status else odd.find('p').get_text(strip=True)

                match_link = match.find('a', class_='table-main__participants participantsMobile participantsHomeAwayMobileWidth')['href']

                # Navegar para o link do jogo
                driver.get(f"https://www.betexplorer.com{match_link}")
                
                # Adicionar um tempo de espera para carregar a nova página
                time.sleep(2)  # Esperar 5 segundos para carregar a nova página

                # Clicar no elemento específico dentro da página do jogo
                ou_25_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="bettype_menu_best"]/li[2]'))
                )
                ou_25_element.click()
                
                # Adicionar um tempo de espera para garantir que a ação seja concluída
                time.sleep(2)

                # Obter o código-fonte da página após o login
                page_source_match = driver.page_source

                # Criar o objeto BeautifulSoup
                site_match = BeautifulSoup(page_source_match, 'html.parser')

                table_odds_over = site_match.find('table', attrs={'data-handicap': '2.50'})
                if table_odds_over:
                    tfoot_odds_over = table_odds_over.find('tfoot', attrs={"id": "match-add-to-selection"})
                    odd_over = tfoot_odds_over.find_all('td', class_='table-main__detail-odds')[0].get_text(strip=True)
                    odd_under = tfoot_odds_over.find_all('td', class_='table-main__detail-odds')[1].get_text(strip=True)
                else:
                    odd_over = ""
                    odd_under = ""

                # Clicar no elemento específico dentro da página do jogo
                btts_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="bettype_menu_best"]/li[6]'))
                )
                btts_element.click()
                
                # Adicionar um tempo de espera para garantir que a ação seja concluída
                time.sleep(2)

                # Obter o código-fonte da página após o login
                page_source_match = driver.page_source

                # Criar o objeto BeautifulSoup
                site_match = BeautifulSoup(page_source_match, 'html.parser')

                table_btts = site_match.find('table', attrs={'data-handicap': '0'})
                if table_btts:
                    tfoot_btts = table_btts.find('tfoot', attrs={"id": "match-add-to-selection"})
                    odd_btts_yes = table_btts.find_all('td', class_='table-main__detail-odds')[0].get_text(strip=True)
                    odd_btts_no = table_btts.find_all('td', class_='table-main__detail-odds')[1].get_text(strip=True)
                else:
                    odd_btts_yes = ""
                    odd_btts_no = ""

                print(f"Liga (País): {league_name} ({country})")
                print(f"Hora/Status: {match_hour}")            
                print(f"Jogo: {home_team} vs {away_team}")
                print(f"Match Odds: {odd_home} - {odd_draw} - {odd_away}")
                print(f"OU 2.5 Odds: Over: {odd_over} - Under: {odd_under}")
                print(f"BTTS Odds: Yes: {odd_btts_yes} - No: {odd_btts_no}")
                print(f"Link: https://www.betexplorer.com{match_link}")
                print("-" * 40)

                # Adicionar os dados à lista
                data.append([
                    country, league_name, date.today(), match_hour, home_team, away_team,
                    odd_home, odd_draw, odd_away, odd_over, odd_under, odd_btts_yes, odd_btts_no,
                    match_link
                ])

        if country == "Brazil":
            break

finally:
    # Fechar o navegador
    driver.quit()

    # Medir o tempo total de execução
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Tempo total de execução: {total_time:.2f} segundos")

    # Criar um DataFrame com os dados e salvar em um arquivo Excel
    df_nextmatches = pd.DataFrame(data, columns=[
        "País", "Campeonato", "Data", "Hora", "Home", "Away", "Odd Home", "Odd Draw", "Odd Away",
        "Over 2.5", "Under 2.5", "BTTS Sim", "BTTS Não", "Link"
    ])

    df_nextmatches.replace("", np.nan, inplace=True)
    df_nextmatches["País"] = df_nextmatches["País"].str.upper()
    df_nextmatches["Campeonato"] = df_nextmatches["Campeonato"].str.upper()
    df_nextmatches["Home"] = df_nextmatches["Home"].str.replace("-", " ")
    df_nextmatches["Away"] = df_nextmatches["Away"].str.replace("-", " ")
    df_nextmatches["Odd Home"] = pd.to_numeric(df_nextmatches["Odd Home"])
    df_nextmatches["Odd Draw"] = pd.to_numeric(df_nextmatches["Odd Draw"])
    df_nextmatches["Odd Away"] = pd.to_numeric(df_nextmatches["Odd Away"])
    df_nextmatches["Over 2.5"] = pd.to_numeric(df_nextmatches["Over 2.5"])
    df_nextmatches["Under 2.5"] = pd.to_numeric(df_nextmatches["Under 2.5"])
    df_nextmatches["BTTS Sim"] = pd.to_numeric(df_nextmatches["BTTS Sim"])
    df_nextmatches["BTTS Não"] = pd.to_numeric(df_nextmatches["BTTS Não"])
    df_nextmatches[["H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T"]] = np.nan
    df_nextmatches = df_nextmatches[["País", "Campeonato", "Data", "Hora", "Home", "Away",
                                 "H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T",
                                 "Odd Home", "Odd Draw", "Odd Away", "Over 2.5", "Under 2.5",
                                 "BTTS Sim", "BTTS Não", "Link"]]
    
    df_nextmatches.to_excel(f"./Next_Matches/Matches_{date.today()}.xlsx",
                            sheet_name="Jogos",
                            columns=["País", "Campeonato", "Data", "Hora", "Home", "Away",
                                 "H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T",
                                 "Odd Home", "Odd Draw", "Odd Away", "Over 2.5", "Under 2.5",
                                 "BTTS Sim", "BTTS Não", "Link"],
                            header=False, index=False)
