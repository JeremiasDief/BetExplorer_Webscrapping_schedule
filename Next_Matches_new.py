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
datas_passadas = [(date(2025, 1, 31) + timedelta(days=i)) for i in range(7)]

for data_passada in datas_passadas:
    # Credenciais
    login = os.getenv("BETEXPLORER_LOGIN")
    password = os.getenv("BETEXPLORER_PASSWORD")

    # Iniciar medição de tempo
    start_time = time.time()

    # Options
    options = Options()
    chrome_options = [
        "--headless=new",
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

    options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )

    # Configurar o WebDriver usando webdriver-manager
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    driver = webdriver.Chrome(service=service, options=options)

    # Obter a data de hoje mais dois dias (de uso no código da automação)
    # hoje = date.today() #- timedelta(1)
    # hoje_ano = hoje.year
    # hoje_mes = hoje.month
    # hoje_dia = hoje.day

    # Obter a data passada (para uso quando tiverem muitas datas com erro no schedule)
    hoje = data_passada
    hoje_ano = hoje.year
    hoje_mes = hoje.month
    hoje_dia = hoje.day

    # Lista para armazenar os dados
    data = []

    try:
        # Acessar a página inicial com a data ajustada
        url = f"https://www.betexplorer.com/?year={hoje_ano}&month={hoje_mes}&day={hoje_dia}"
        print(f"Acessando URL: {url}")
        driver.get(url)
        time.sleep(5)

        # Aceitar cookies se a mensagem aparecer
        try:
            print("Tentando aceitar cookies...")
            WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
            ).click()
            print("Cookies aceitos!")
        except Exception as e:
            print(f"Erro ao aceitar cookies (pode não ser necessário): {e}")

        # # Cancelar aviso site br se a mensagem aparecer
        try:
            cancel_br_button = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="js-window-language-redirect"]/div[2]/button[2]'))
            )
            cancel_br_button.click()
        except:
            print("Não foi encontrado o botão de cancelar site br")
            pass

        # Ajustar o timezone
        WebDriverWait(driver, 30).until(
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
        login_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="js-header"]/div[1]/div/div/ul/li[1]/a'))
        )
        login_button.click()

        # Preencher o formulário de login
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="login_nick"]'))
        )
        password_field = driver.find_element(By.XPATH, '//*[@id="login_pass"]')
        username_field.send_keys(login)
        password_field.send_keys(password)

        # Clicar no botão de login
        login_submit = driver.find_element(By.XPATH, '//*[@id="js-window-action-login"]')
        login_submit.click()

        # Adicionar um tempo de espera após o login
        time.sleep(15)  # Esperar 15 segundos após o login

        # Verificar se o login foi bem-sucedido e a página está completamente carregada
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="nr-ko-all"]'))
        )

        print("Login realizado com sucesso.")

        # Obter o código-fonte da página após o login
        page_source = driver.page_source

        # Criar o objeto BeautifulSoup
        site = BeautifulSoup(page_source, 'html.parser')
        if site:
            print("site ok!")
        else:
            print("site não puxou")

        # Encontrar o novo elemento 'nr-ko-all'
        next_matches_table = site.find('div', attrs={'id': 'nr-ko-all'})
        if next_matches_table:
            print("next_matches_table ok!")
            # print(next_matches_table.prettify())  # Imprimir o conteúdo completo para depuração
        else:
            print("next_matches_table não puxou")

        # Encontrar todas as ligas favoritas e seus jogos
        leagues = next_matches_table.find_all('ul', class_='leagues-list topleague')
        if leagues:
            print("leagues ok!")
        else:
            print("leagues não puxou")
            sys.exit("Erro: leagues não foi encontrado.")
        for league in leagues:
            favourite_star = league.find('a', class_='myleague active table-main__FavouriteStar')
            if favourite_star:
                country = league.find('p', class_='table-main__truncate table-main__leaguesNames leaguesNames').get_text(strip=True).split(': ')[0]
                league_name = league.find('p', class_='table-main__truncate table-main__leaguesNames leaguesNames').get_text(strip=True).split(': ')[1]

                matches = league.find_all('ul', class_='table-main__matchInfo')
                for match in matches:
                    if match.find('span', class_='table-main__matchHour matchDateStatus table-main__isLive'):
                        data_dt = match['data-dt']
                        day, month, year, hour, minute = map(int, data_dt.split(','))
                        match_time = datetime(year, month, day, hour, minute)
                        new_match_time = match_time - timedelta(hours=4) #- timedelta(hours=5) # usada para horário de verao europeu
                        formatted_time = new_match_time.strftime('%H:%M')
                        match_hour = formatted_time
                        status = True
                    elif match.find('span', class_='table-main__matchHour matchDateStatus'):
                        match_hour = match.find('span', class_='table-main__matchHour matchDateStatus').get_text(strip=True)
                        status = True
                    else:
                        match_hour = match.find('span', class_='table-main__matchStatus matchDateStatus').get_text(strip=True)
                        status = False
                        if match_hour not in ("POSTP.", "CAN."):
                            data_dt = match['data-dt']
                            day, month, year, hour, minute = map(int, data_dt.split(','))
                            match_time = datetime(year, month, day, hour, minute)
                            new_match_time = match_time - timedelta(hours=5)
                            formatted_time = new_match_time.strftime('%H:%M')
                            match_hour = formatted_time

                    home_team = match.find('div', class_='participantsHomeAwayMobileWidth table-main__participantHome participantHomeOrder').find('p').get_text(strip=True)
                    away_team = match.find('div', class_='participantsHomeAwayMobileWidth table-main__participantAway').find('p').get_text(strip=True)

                    # odds = match.find_all('div', class_='table-main__odds table-main__odd oddMobile')
                    # for i, odd in enumerate(odds):
                    #     if i == 0:
                    #         odd_home = odd.find('button').get_text(strip=True) if status else odd.find('p').get_text(strip=True)
                    #     elif i == 1:
                    #         odd_draw = odd.find('button').get_text(strip=True) if status else odd.find('p').get_text(strip=True)
                    #     elif i == 2:
                    #         odd_away = odd.find('button').get_text(strip=True) if status else odd.find('p').get_text(strip=True)

                    match_link = match.find('a', class_='table-main__participants participantsMobile participantsHomeAwayMobileWidth')['href']

                    # # Navegar para o link do jogo
                    # driver.get(f"https://www.betexplorer.com{match_link}")

                    # # Adicionar um tempo de espera para carregar a nova página
                    # time.sleep(5)  # Esperar 5 segundos para carregar a nova página

                    MAX_TENTATIVAS = 5  # Aumentamos para 5 tentativas para garantir que a página carregue
                    tentativas = 0
                    pagina_carregada = False

                    while tentativas < MAX_TENTATIVAS:
                        print(f"🟡 Tentando abrir jogo: {match_link} (Tentativa {tentativas+1})")
                        driver.get(f"https://www.betexplorer.com{match_link}")
                        time.sleep(3)

                        try:
                            # Garantir que a página carregou corretamente (Título do jogo ou Odds)
                            WebDriverWait(driver, 15).until(
                                EC.presence_of_element_located((By.XPATH, '//h1[contains(@class, "list-details__item__header")]'))
                            )
                            print("✅ Página carregada com sucesso!")

                            # Verificar se as odds carregaram (caso contrário, tentar novamente)
                            odds_elements = driver.find_elements(By.CLASS_NAME, "table-main__detail-odds")
                            if odds_elements:
                                print("✅ Odds detectadas, página pronta para extração!")
                                pagina_carregada = True
                                break  # Sai do loop se tudo carregou corretamente
                            else:
                                print("⚠️ Página abriu, mas odds não carregaram. Tentando novamente...")

                        except Exception as e:
                            print(f"❌ Página não carregou corretamente. Tentando novamente... ({e})")
                        
                        tentativas += 1
                        if tentativas < MAX_TENTATIVAS:
                            driver.refresh()  # Dá refresh e tenta de novo

                    # Se falhar após todas as tentativas, registrar erro e seguir
                    if not pagina_carregada:
                        print(f"❌ Falha ao carregar o jogo após {MAX_TENTATIVAS} tentativas. Registrando erro e pulando...")
                        data.append(["Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", "Erro", match_link])
                        continue

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

                    # Clicar no elemento específico dentro da página do jogo

                    WebDriverWait(driver, 60).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="bettype_menu_best"]/li[2]'))
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
                    WebDriverWait(driver, 60).until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="bettype_menu_best"]/li[6]'))
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
                        country, league_name, hoje, match_hour, home_team, away_team,
                        odd_home, odd_draw, odd_away, odd_over, odd_under, odd_btts_yes, odd_btts_no,
                        match_link
                    ])

            # if country == "Algeria":
            #     break

    finally:
        # Fechar o navegador
        driver.quit()

        # Verifique se há dados coletados
        if len(data) == 0:
            print("Nenhum dado foi coletado.")
        else:
            print(f"Tem dados: \n{data}")

        # Criar um DataFrame com os dados e salvar em um arquivo Excel
        df_nextmatches = pd.DataFrame(data, columns=[
            "País", "Campeonato", "Data", "Hora", "Home", "Away", "Odd Home", "Odd Draw", "Odd Away",
            "Over 2.5", "Under 2.5", "BTTS Sim", "BTTS Não", "Link"
        ])

        # Adicionar 16 colunas em branco após "Odd Away"
        for i in range(16):
            df_nextmatches.insert(df_nextmatches.columns.get_loc("Over 2.5"), f'Blank {i+1}', np.nan)

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
                                        "Odd Home", "Odd Draw", "Odd Away"] + 
                                        [f'Blank {i+1}' for i in range(16)] +
                                        ["Over 2.5", "Under 2.5", "BTTS Sim", "BTTS Não", "Link"]]
        
        # Caminho para salvar o arquivo Excel no repositório privado
        output_path = f"./private-arquivos/Matches_{hoje}.xlsx"

        df_nextmatches.to_excel(output_path,
                                sheet_name="Jogos",
                                columns=["País", "Campeonato", "Data", "Hora", "Home", "Away",
                                        "H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T",
                                        "Odd Home", "Odd Draw", "Odd Away"] + 
                                        [f'Blank {i+1}' for i in range(16)] +
                                        ["Over 2.5", "Under 2.5", "BTTS Sim", "BTTS Não", "Link"],
                                header=False, index=False)
        
        # Medir o tempo total de execução
        end_time = time.time()
        total_time = end_time - start_time
        print(f"Tempo total de execução: {total_time:.2f} segundos")
