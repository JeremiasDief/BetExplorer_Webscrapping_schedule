from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager, ChromeType
from bs4 import BeautifulSoup
import time
from datetime import date, timedelta, datetime
import pandas as pd
import numpy as np
import sys
import os

# Para uso quando precisar rodar o código para mais de uma data (em casos de erros no run do schedule)
# Lembrar de criar o laço for logo abaixo > for data_passada in datas_passadas: <
datas_passadas = [(date(2025, 1, 31) + timedelta(days=i)) for i in range(6)]

for data_passada in datas_passadas:
    # Credenciais
    login = os.getenv("BETEXPLORER_LOGIN")
    password = os.getenv("BETEXPLORER_PASSWORD")
    # Se for rodar na máquina local, usar o login e password

    # Iniciar medição de tempo
    start_time = time.time()

    # Options
    options = Options()
    chrome_options = [
        "--headless",
        # "--disable-gpu",
        # "--window-size=1920,1200",
        # "--ignore-certificate-errors",
        # "--disable-extensions",
        "--no-sandbox",
        "--remote-debugging-port=9222"
        # "--disable-dev-shm-usage"
    ]
    for option in chrome_options:
        options.add_argument(option)

    # Configurar o WebDriver usando webdriver-manager
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    # service = Service(ChromeDriverManager().install()) # Para uso do código na máquina local
    driver = webdriver.Chrome(service=service, options=options)

    # # Obter a data de ontem mais dois dias (de uso no código da automação)
    # ontem = date.today() - timedelta(1)
    # ontem_ano = ontem.year
    # ontem_mes = ontem.month
    # ontem_dia = ontem.day

    # Obter a data passada (para uso quando tiverem muitas datas com erro no schedule)
    ontem = data_passada
    ontem_ano = ontem.year
    ontem_mes = ontem.month
    ontem_dia = ontem.day

    # Lista para armazenar os dados
    data = []

    try:
        # Acessar a página inicial
        url = f"https://www.betexplorer.com/football/results/?year={ontem_ano}&month={ontem_mes}&day={ontem_dia}"
        driver.get(url)
        time.sleep(2)

        # Aceitar cookies se a mensagem aparecer
        try:
            accept_cookies_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
            )
            accept_cookies_button.click()
        except:
            print("Não foi encontrado o botão de aceitar cookies")
            pass

        # Cancelar aviso site br se a mensagem aparecer
        try:
            cancel_br_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div/div/div[16]/div[2]/button[2]'))
            )
            cancel_br_button.click()
        except:
            print("Não foi encontrado o botão de cancelar site br")
            pass

        # Ajustar o timezone
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="js-timezone"]'))
        ).click()
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="js-timezone"]/ul/li[22]/button'))
        )

        # Usar JavaScript para clicar no elemento
        driver.execute_script("""
            var element = document.evaluate('//*[@id="js-timezone"]/ul/li[22]/button', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (element) {
                element.click();
            }
        """)

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
        time.sleep(10)  # Esperar 5 segundos após o login

        # Verificar se o login foi bem-sucedido e a página está completamente carregada
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="nr-all"]'))
        )

        print("Login realizado com sucesso.")

        # Obter o código-fonte da página após o login
        page_source = driver.page_source

        # Criar o objeto BeautifulSoup
        site = BeautifulSoup(page_source, 'html.parser')

        # Encontrar o novo elemento 'nr-ko-all'
        results_table = site.find('div', attrs={'id': 'nr-all'})

        # Encontrar todas as ligas favoritas e seus jogos
        tbodys = results_table.find_all('tbody')
        for tbody in tbodys:
            favourite = tbody.find('a', class_='myleague active')
            if favourite:
                tds_ft = tbody.find_all('td', class_='table-main__result')
                for td_ft in tds_ft:
                    match_link = td_ft.find('a')['href']
                    ft_result = td_ft.find('a').get_text()

                    if td_ft.find('span'):
                        event = td_ft.find('span').get_text(strip=True)
                        if event in ("POSTP.", "CAN."):
                            ft_result_home = event
                            ft_result_away = ht_result_home = ht_result_away = t2_result_home = t2_result_away = ""
                        elif event in ("ABN.", "AWA."):
                            score_part = ft_result.split()[0]
                            # Verifique se o primeiro caractere de score_part é um dígito
                            if score_part[0].isdigit():
                                ft_result_home = int(score_part.split(":")[0])
                                ft_result_away = int(score_part.split(":")[1])
                            else:
                                ft_result_home = 0
                                ft_result_away = 0

                            ht_result_home = event
                            ht_result_away = t2_result_home = t2_result_away = ""

                    else:
                        event = False
                        ft_result_home = int(ft_result.split(":")[0])
                        ft_result_away = int(ft_result.split(":")[1])

                    # Navegar para o link do jogo
                    driver.get(f"https://www.betexplorer.com{match_link}")
                    
                    # Adicionar um tempo de espera para carregar a nova página
                    time.sleep(2)  # Esperar 5 segundos para carregar a nova página

                    # Obter o código-fonte da página após o login
                    page_source_match = driver.page_source

                    # Criar o objeto BeautifulSoup
                    site_match = BeautifulSoup(page_source_match, 'html.parser')

                    table_match_odds = site_match.find('table', attrs={'data-handicap': '0'})
                    if table_match_odds:
                        rows = table_match_odds.find_all('tr', class_=['odd', 'even'])

                        for i, row in enumerate(rows):
                            bookmaker = row.find('td', class_='h-text-left').get_text(strip=True)
                            odds_cells = row.find_all('td', class_='table-main__detail-odds')

                            if "Pinnacle" in bookmaker:
                                odd_home = odds_cells[0].get_text(strip=True)
                                odd_draw = odds_cells[1].get_text(strip=True)
                                odd_away = odds_cells[2].get_text(strip=True)
                                break

                            elif i == 0:
                                odd_home = odds_cells[0].get_text(strip=True)
                                odd_draw = odds_cells[1].get_text(strip=True)
                                odd_away = odds_cells[2].get_text(strip=True)

                            elif "Betfair" in bookmaker:
                                odd_home = odds_cells[0].get_text(strip=True)
                                odd_draw = odds_cells[1].get_text(strip=True)
                                odd_away = odds_cells[2].get_text(strip=True)

                            else:
                                continue

                    else:
                        odd_home, odd_draw, odd_away = "", "", ""

                    if event not in ("POSTP.", "CAN.", "ABN.", "AWA."):
                        partial_result = site_match.find('div', class_='list-details__item__partial bold').get_text(strip=True)
                    
                        if partial_result != None and partial_result[0] == "(":
                            if event in ("ET", "PEN."):
                                results = partial_result.strip("()").split(", ")
                                ht_result_home, ht_result_away = map(int, results[0].split(":"))
                                t2_result_home, t2_result_away = map(int, results[1].split(":"))
                                ft_result_home = ht_result_home + t2_result_home
                                ft_result_away = ht_result_away + t2_result_away
                            else:
                                results = partial_result.strip("()").split(", ")
                                ht_result_home, ht_result_away = map(int, results[0].split(":"))
                                t2_result_home, t2_result_away = map(int, results[1].split(":"))
                        else:
                            ht_result_home = ht_result_away = t2_result_home = t2_result_away = ""

                    infos_header = site_match.find('div', class_='componentDividerFirst containerResponseMax')
                    country = infos_header.find_all('li')[2].get_text(strip=True)
                    league = infos_header.find_all('li')[3].get_text(strip=True).rsplit(' ', 1)[0]
                    home_team = infos_header.find_all('li')[4].get_text(strip=True).split(' - ')[0]
                    away_team = infos_header.find_all('li')[4].get_text(strip=True).split(' - ')[1]
                    date_text = site_match.find('p', class_='list-details__item__date headerTournamentDate')
                    if date_text:
                        date_parts = date_text.get_text(strip=True).split(' - ')
                        if len(date_parts) > 1:  # Verifica se a lista tem pelo menos dois elementos
                            match_hour = date_parts[1]
                        else:
                            match_hour = ""  # Caso o segundo item não esteja disponível
                    else:
                        match_hour = ""  # Caso o elemento não seja encontrado

                    # if len(site_match.find('p', class_='list-details__item__date headerTournamentDate').get_text(strip=True).split(' - ')) > 0:
                    #     match_hour = site_match.find('p', class_='list-details__item__date headerTournamentDate').get_text(strip=True).split(' - ')[1]

                    # Clicar no elemento específico dentro da página do jogo
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="bettype_menu_best"]/li[2]'))
                    )

                    # Usar JavaScript para clicar no elemento
                    driver.execute_script("""
                        var element = document.evaluate('//*[@id="bettype_menu_best"]/li[2]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (element) {
                            element.click();
                        }
                    """)
                    
                    # Adicionar um tempo de espera para garantir que a ação seja concluída
                    time.sleep(2)

                    # Obter o código-fonte da página após o login
                    page_source_match = driver.page_source

                    # Criar o objeto BeautifulSoup
                    site_match = BeautifulSoup(page_source_match, 'html.parser')

                    table_odds_over = site_match.find('table', attrs={'data-handicap': '2.50'})
                    if table_odds_over:
                        rows = table_odds_over.find_all('tr', class_=['odd', 'even'])

                        for i, row in enumerate(rows):
                            bookmaker = row.find('td', class_='h-text-left').get_text(strip=True)
                            odds_cells = row.find_all('td', class_='table-main__detail-odds')

                            if "Pinnacle" in bookmaker:
                                odd_over = odds_cells[0].get_text(strip=True)
                                odd_under = odds_cells[1].get_text(strip=True)
                                break

                            elif i == 0:
                                odd_over = odds_cells[0].get_text(strip=True)
                                odd_under = odds_cells[1].get_text(strip=True)

                            elif "Betfair" in bookmaker:
                                odd_over = odds_cells[0].get_text(strip=True)
                                odd_under = odds_cells[1].get_text(strip=True)

                            else:
                                continue

                    else:
                        odd_over, odd_under = "", ""

                    # Clicar no elemento específico dentro da página do jogo
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="bettype_menu_best"]/li[6]'))
                    )

                    # Usar JavaScript para clicar no elemento
                    driver.execute_script("""
                        var element = document.evaluate('//*[@id="bettype_menu_best"]/li[6]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                        if (element) {
                            element.click();
                        }
                    """)
                    
                    # Adicionar um tempo de espera para garantir que a ação seja concluída
                    time.sleep(2)

                    # Obter o código-fonte da página após o login
                    page_source_match = driver.page_source

                    # Criar o objeto BeautifulSoup
                    site_match = BeautifulSoup(page_source_match, 'html.parser')

                    table_btts = site_match.find('table', attrs={'data-handicap': '0'})
                    if table_btts:
                        rows = table_btts.find_all('tr', class_=['odd', 'even'])

                        for i, row in enumerate(rows):
                            bookmaker = row.find('td', class_='h-text-left').get_text(strip=True)
                            odds_cells = row.find_all('td', class_='table-main__detail-odds')

                            if "Pinnacle" in bookmaker:
                                odd_btts_yes = odds_cells[0].get_text(strip=True)
                                odd_btts_no = odds_cells[1].get_text(strip=True)
                                break

                            elif i == 0:
                                odd_btts_yes = odds_cells[0].get_text(strip=True)
                                odd_btts_no = odds_cells[1].get_text(strip=True)

                            elif "Betfair" in bookmaker:
                                odd_btts_yes = odds_cells[0].get_text(strip=True)
                                odd_btts_no = odds_cells[1].get_text(strip=True)

                            else:
                                continue

                    else:
                        odd_btts_yes, odd_btts_no = "", ""

                    # Adicionar os dados à lista
                    data.append([
                        event, country, league, ontem, match_hour, home_team, away_team,  
                        ft_result_home, ft_result_away, ht_result_home, ht_result_away, t2_result_home, t2_result_away,
                        odd_home, odd_draw, odd_away,
                        odd_over, odd_under, odd_btts_yes, odd_btts_no, match_link
                    ])

            # else:
            #     country = "Any"
            # if country == "Brazil":
            #     break

    finally:
        # Fechar o navegador
        driver.quit()

        # Criar um DataFrame com os dados e salvar em um arquivo Excel
        df_results = pd.DataFrame(data, columns=[
                                        "Evento", "País", "Campeonato", "Data", "Hora", "Home", "Away", 
                                        "H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T", 
                                        "Odd H", "Odd Draw", "Odd A", 
                                        "Ov. 2.5", "Un. 2.5", "BTTS Y", "BTTS N", "Link"
                                    ])

        df_results.replace("", np.nan, inplace=True)
        df_results["País"] = df_results["País"].str.upper()
        df_results["Campeonato"] = df_results["Campeonato"].str.upper()
        df_results["Home"] = df_results["Home"].str.replace("-", " ")
        df_results["Away"] = df_results["Away"].str.replace("-", " ")
        df_results["Odd H"] = pd.to_numeric(df_results["Odd H"])
        df_results["Odd Draw"] = pd.to_numeric(df_results["Odd Draw"])
        df_results["Odd A"] = pd.to_numeric(df_results["Odd A"])
        df_results["Ov. 2.5"] = pd.to_numeric(df_results["Ov. 2.5"])
        df_results["Un. 2.5"] = pd.to_numeric(df_results["Un. 2.5"])
        df_results["BTTS Y"] = pd.to_numeric(df_results["BTTS Y"])
        df_results["BTTS N"] = pd.to_numeric(df_results["BTTS N"])

        # Caminho para salvar o arquivo Excel no repositório privado
        output_path = f"./private-arquivos/Results_{ontem}.xlsx"
        
        df_results.to_excel(output_path,
                                sheet_name="Jogos",
                                columns=[
                                        "Evento", "País", "Campeonato", "Data", "Hora", "Home", "Away", 
                                        "H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T", 
                                        "Odd H", "Odd Draw", "Odd A", 
                                        "Ov. 2.5", "Un. 2.5", "BTTS Y", "BTTS N", "Link"
                                    ],
                                header=False, index=False)

        # Medir o tempo total de execução
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Tempo total de execução: {total_time:.2f} segundos")
