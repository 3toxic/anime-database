from config import bravepath, driverpath, anilistpath as path
from mystuff import ScrapeLog
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException
import os
# import sys
import csv

def launch_browser():
    chrome_service = Service(executable_path=driverpath)
    chrome_option = Options()
    chrome_option.add_argument("--incognito")
    chrome_option.add_argument("--disabled-extensions")
    chrome_option.add_experimental_option('excludeSwitches', ['enable-logging']) #removes error messages
    # chrome_option.add_experimental_option("detach", True) #keeps the browser open
    chrome_option.binary_location = bravepath
    driver = webdriver.Chrome(service=chrome_service, options=chrome_option)
    return driver

def main():

    anime = {
    "id": None,
    'english': None,
    'native': None,
    "format": None,
    "episodes": None,
    'genres': None,
    'studios': None,
    "episode duration": None,
    "start date": None,
    "average score": None,
    "mean score": None,
    "users": None,
    "end date": None,
    "tags": None,
    "score-distr": None,
    }

    log = ScrapeLog()
    curr_page = log.anilist

    driver = launch_browser()
    url = "https://anilist.co/anime/98291/Tsurezure-Children/"
    driver.get(url)

    animeID = url.split("/")
    anime["id"] = animeID[animeID.index('anime')+1]

    try:
        #check to make sure page is loaded
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME, "ct-chart-bar")))

        #get data from sidebar
        sidebar = driver.find_element(By.CLASS_NAME, "data")
        stuff = sidebar.find_elements(By.CLASS_NAME, "data-set")
        data = map(lambda x: x.text.split("\n"), stuff)

        #display spoiler tags
        try:
            spoiler = driver.find_element(By.CLASS_NAME, "spoiler-toggle")
            spoiler.click()
        except NoSuchElementException as E:
            log.writeError(f"{E} in anilist {anime.get('id')} trying to get spoilers")

        #get show tags
        tags = driver.find_elements(By.CLASS_NAME, "tag")
        tags.append(driver.find_elements(By.CLASS_NAME, "tag spoiler"))
        tags.pop(-1)
        anime["tags"] = ", ".join(map(lambda x: x.text.split("\n")[0], tags))


        #get number of users
        status = driver.find_element(By.CLASS_NAME, "statuses")
        users = map(lambda x: x.find_element(By.CLASS_NAME, "amount").text, status.find_elements(By.CLASS_NAME, "status"))
        user_count = list(map(lambda x: "".join([n for n in x if n.isnumeric()]), users))
        anime["users"] = sum(int(i) for i in user_count[:-1])
        
        #get score distribution
        score_chart = driver.find_element(By.XPATH, "/html/body/div[2]/div[3]/div/div[2]/div[2]/div[6]/div[2]")
        scores = score_chart.find_elements(By.TAG_NAME, "text")
        anime["score-distr"] = [(i+1, int(n)) for i, n in enumerate(map(lambda x: x.get_attribute('textContent'), scores))]

    except TimeoutException:
        raise("took too long to load")
    except:
        raise("something went wrong")

    for x in data:
        if x[0].lower() in anime:
            anime[x[0].lower()] = ", ".join(x[1:])

    if anime.get("format") == "TV Short":
        anime.update({"format": "TV"})


    with open("anilist.csv", 'w', newline='', encoding='utf-16') as f:
        writer = csv.writer(f, delimiter='\t')

        if f.mode=="w":
            writer.writerow(anime)
        
        writer.writerow(anime.values())
            
    os.startfile(path)

if __name__=="__main__":
    main()
