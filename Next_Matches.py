import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager, ChromeType
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from time import sleep
import getpass
import keyring
import pandas as pd
import numpy as np
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment

#service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
#service = Service(ChromeDriverManager().install())
CHROME_VERSION = '114.0.5735'
CHROMEDRIVER_URL = f'https://chromedriver.storage.googleapis.com/{CHROME_VERSION}/chromedriver_linux64.zip'
login = "jeremias_dief"
#password = getpass.getpass(prompt='Digite a Senha: ', stream=None)
password = "BetExplorer2023"

headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/104.0.5112.102 Safari/537.36 OPR/90.0.4480.117"}

def verificar_casas(trs: list):
    list_databid = []
    for tr in trs:
        list_databid.append(tr["data-bid"])
    #print(list_databid)

    if "44" in list_databid:
        databid = "44"
    elif "429" in list_databid:
        databid = "429"
    elif "18" in list_databid:
        databid = "18"
    elif "16" in list_databid:
        databid = "16"
    elif "417" in list_databid:
        databid = "417"
    else:
        databid = False
        print("Nenhuma casa usual disponível!")
        
    return databid


def get_odd_over(over: str, table, odds_dict: dict):
    if table.find("td", attrs={"class": "table-main__doubleparameter"}).get_text() == over:
        #print(table.find("td", attrs={"class": "table-main__doubleparameter"}).get_text())

        trs = table.find("tbody").find_all("tr")

        databid = verificar_casas(trs)

        if databid:
            for tr in trs:
                if databid in tr.attrs["data-bid"]:
                    casa = tr.find("td", attrs={"class": "h-text-left over-s-only"}).get_text()
                    tds = tr.find_all('td')
                    for td in tds:
                        if "table-main__detail-odds" in td.attrs["class"]:                    
                            odds_dict[f"Over_{over.replace('.', '')}"] = td.find("span").text
                            break # o break faz ele parar o looping e pegar só a odd do Over
        else:
            odds_dict[f"Over_{over.replace('.', '')}"] = "Sem casas disponíveis"


# options = Options()
# options.add_argument('--headless')
# options.add_argument('--no-sandbox')
# options.add_argument('--remote-debugging-port=9222')
#options.binary_location = '/usr/bin/google-chrome'
#options.add_argument('window-size=400,800')

# Use o Chromedriver manualmente
#driver_path = './chromedriver'  # Defina o caminho onde o arquivo chromedriver está localizado
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--remote-debugging-port=9222')

hoje = date.today()#-timedelta(1)
hoje_ano = hoje.year
hoje_mes = hoje.month
hoje_dia = hoje.day

url_base = "https://www.betexplorer.com"
url_nextmatches = f'https://www.betexplorer.com/next/football/?year={hoje_ano}&month={hoje_mes}&day={hoje_dia}'

#navegador = webdriver.Chrome(options=options, service=service, executable_path="/usr/local/bin/chromedriver")
#navegador = webdriver.Chrome(options=options, service=service)
navegador = webdriver.Chrome(options=options)
navegador.implicitly_wait(60)

navegador.get(url_nextmatches)

sleep(2)
cookies = navegador.find_element(By.XPATH, '//*[@id="onetrust-accept-btn-handler"]')
if cookies:
    cookies.click()
navegador.find_element(By.XPATH, '//*[@id="js-timezone"]').click()
timezone = navegador.find_element(By.XPATH, '//*[@id="js-timezone"]/ul/li[21]/a').click()

sleep(2)
login_button = navegador.find_element(By.XPATH, '//*[@id="js-header"]/div[1]/div/div/ul/li[1]/a')
login_button.click()
login_button.find_element(By.XPATH, '//*[@id="login_nick"]').send_keys(login)
login_button.find_element(By.XPATH, '//*[@id="login_pass"]').send_keys(password)
login_button.find_element(By.XPATH, '//*[@id="js-window-action-login"]').click()

navegador.find_element(By.XPATH, '//*[@id="next-filter-myonly-checkbox"]').click()
navegador.find_element(By.XPATH, '//*[@id="next-filter-sort"]/li[2]/div').click()
navegador.find_element(By.XPATH, '//*[@id="next-filter-sort"]/li[2]/div/ul/li[2]').click()

sleep(2)
page_source = navegador.page_source

site = BeautifulSoup(page_source)

next_matches_table = site.find('div', attrs={'id': 'nr-lg'})
#print(next_matches_table.prettify())
tbodys = next_matches_table.find_all("tbody")

navegador.close()

jogos_do_dia = []
for tbody in tbodys:
    if "style" in tbody.attrs:
        continue
    elif "class" in tbody.attrs:
        continue 
    else:
        campeonato = tbody.find("th").get_text().strip()
        tds = tbody.find_all("td")
        for td in tds:
            if td["class"] == ["table-main__tt"]:
                infos_jogo = []
                infos_jogo.append(campeonato)
                link_jogo = td.a["href"]
                for span in td.find_all("span"):
                    infos_jogo.append(span.text)
                infos_jogo.append(link_jogo)
            elif td["class"] == ["table-main__odds"]:
                if td["data-oid"] == "":
                    infos_jogo.append("")
                else:
                    infos_jogo.append(td.a.text)
            elif td["class"] == ["table-main__result"]:
                #print(td.get_text())
                if td.get_text()[0] in [str(x) for x in list(range(20))]:
                    if "data-live-cell" not in td.attrs:
                        options = Options()
                        options.add_argument('--headless')
                        url_jogo = url_base + link_jogo
                        naveg_game = webdriver.Chrome(options=options)
                        naveg_game.implicitly_wait(60)
                        naveg_game.get(url_jogo)
                        sleep(0.5)
                        game_page_source = naveg_game.page_source
                        site_game = BeautifulSoup(game_page_source)
                        average = site_game.find('tfoot', attrs={'id': 'match-add-to-selection'})
                        if average == None:
                            td_odds = [None, None, None]
                            for odd in td_odds:
                                infos_jogo.append(odd)
                        else:
                            td_odds = average.find_all("td", attrs={"class": "table-main__detail-odds"})
                            for odd in td_odds:
                                infos_jogo.append(odd.text)
                        naveg_game.close()
                        
            else:
                continue
            
            if len(infos_jogo) == 8:
                jogos_do_dia.append(infos_jogo)

for i, x in enumerate(jogos_do_dia):
    if len(x) > 8:
        #print(x, i)
        x.remove("'")
                

df_nextmatches = pd.DataFrame(jogos_do_dia, columns=["Pais_e_Campeonato", "Hora", "Home", "Away", "Link",
                                                     "Odd_Home", "Odd_Draw", "Odd_Away"
                                                    ])
df_nextmatches.replace("", np.nan, inplace=True)
df_nextmatches[["País", "Campeonato"]] = df_nextmatches["Pais_e_Campeonato"].str.split(": ", expand=True)
df_nextmatches.drop(columns=["Pais_e_Campeonato"], inplace=True)
df_nextmatches["País"] = df_nextmatches["País"].str.upper()
df_nextmatches["Campeonato"] = df_nextmatches["Campeonato"].str.upper()
df_nextmatches["Home"] = df_nextmatches["Home"].str.replace("-", " ")
df_nextmatches["Away"] = df_nextmatches["Away"].str.replace("-", " ")
df_nextmatches["Odd_Home"] = pd.to_numeric(df_nextmatches["Odd_Home"])
df_nextmatches["Odd_Draw"] = pd.to_numeric(df_nextmatches["Odd_Draw"])
df_nextmatches["Odd_Away"] = pd.to_numeric(df_nextmatches["Odd_Away"])
df_nextmatches["Data"] = date.today()
df_nextmatches[["H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T"]] = np.nan
df_nextmatches = df_nextmatches[["País", "Campeonato", "Data", "Hora", "Home", "Away",
                                 "H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T",
                                 "Odd_Home", "Odd_Draw", "Odd_Away", 
                                 "Link"]]

# df_nextmatches.to_excel(f"./Next_Matches/Matches_{hoje}.xlsx",
#                          sheet_name="Jogos",
#                          columns=["País", "Campeonato", "Data", "Hora", "Home", "Away",
#                                  "H FT", "A FT", "H HT", "A HT", "H 2T", "A 2T",
#                                  "Odd_Home", "Odd_Draw", "Odd_Away", "Link"],
#                          header=False, index=False)

wb = Workbook()
ws = wb.active

ws.number_format = '#,##0.00'

for row in dataframe_to_rows(df_nextmatches, index=False, header=False):
    ws.append(row)

wb.save(f"./Next_Matches/Matches_{hoje}.xlsx")