# Written by Jason Li
# Script to scrape data for anime databases from popular sorted page on MyAnimeList

# imports
from config import malpath as path
import requests
import csv
import os
import sys
from bs4 import BeautifulSoup as bs
from mystuff import ScrapeLog

# counts number of items in iterable
def itercount(i):
    return sum(1 for e in i)

# finds first instance of number in a string
def badstrip(str):
    for x in str:
        if x.isdigit():
            return str.index(x)

# removes all commas in a string
def removecomma(str):
    tag = list(str)
    while "," in tag:
        tag.remove(",")

    return "".join(tag)

# scrape a webpage
def grabpage(link, log):
    
    page = requests.get(link) #make a request

    #if internet breaks
    # if page.status_code=="403":

    # create beautiful soup object
    soup = bs(page.content, "html.parser")
    results = soup.find(id="contentWrapper")

    # dictionary with target values and stores scraped data
    dict = { 
    "id": None,
    "title": None,
    "japanese": None, 
    "type": None, 
    "score": None,
    "users": None,
    "favorites": None,
    "aired": None, 
    "episode": None, 
    "duration": None,
    "studio": None, 
    "source": None, 
    "genre": None, 
    "theme": None,
    }

    # get basic information on the show
    split_url = link.split("/")
    dict['id'] = split_url[split_url.index("anime")+1]
    dict["title"] = results.find("h1", class_="title-name").text.strip() # grab title
    dict["score"] = results.find("div", class_="score-label").text.strip() # grab score

    # grab number of users
    people = results.find("div", class_="di-ib ml12 pl20 pt8") 
    *_, member = iter(people.children) # gets last value in list or something
    dict["users"] = member.text.strip()[badstrip(member.text.strip()):]

    # get data from left sidebar
    for element in dict:
        if dict[element] is None:
            try: 
                dict[element] = getsidebar(element, results)
            except:
                dict[element] = ""
                log.writeError(f"Error in show {dict.get('id')} trying to get sidebar element {element}")

    # format data
    dict['duration'] = "".join([x for x in dict.get('duration') if x.isdigit()]) # removes text from episode length
    dict['users'] = removecomma(dict.get("users")) # remove commas from number of users
    dict['favorites'] = removecomma(dict.get("favorites")) # remove commas from number of favourites
    
    # split airing dates into start and end dates
    dates = dict['aired'].split('to')
    dict.update({'start date': dates[0]})
    if len(dates) == 2:
        dict.update({'end date': dates[1].strip()})

    dict.pop('aired')

    # get some staff on the show
    getstaff(soup, dict, log)

    # write data to csv file
    with open("mal.csv", 'a', encoding="utf-16", newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(dict.values())

# get data from the sidebar
def getsidebar(item, soup):

    # checks if element exists
    date = soup.find("span", string = lambda text: item in text.lower() if text else None)
    if date is None:
        return ""
    
    div = date.parent # moves up html tree to access element value

    # checks if value is a list or single value
    if itercount(div)>3:
        # if value is a list format and return as a list
        tempstr = ""
        for x in div:
            if x.name =="a":
                tempstr += x.text.strip() + ", "

        tempstr = tempstr.rstrip(", ")
        return tempstr
    else:
        # return value as is
        div.span.decompose()
        return div.text.strip()

# get names of staff
def getstaff(soup, dict, log):

    # moves to tab with list of staff
    nav = soup.find(id="horiznav_nav")
    tabs = nav.find('ul')
    stafflink = tabs.contents[3].find('a')['href']
    page = requests.get(stafflink)
    soup = bs(page.content, 'html.parser')
    results = soup.find(id="content")
    staff = results.find_all('h2', class_="h2_overwrite")[1].parent.find_all_next('table') # finds objects for each staff

    # staff to scrape
    positions = {
    "director": "", 
    "music": "", 
    "creator": "",
    "original creator": ""
    }

    # loops through each staff listed
    for person in staff:
        role = person.find("div", class_="spaceit_pad")
        split = list(map(lambda s: s.strip().lower(), role.text.split(",")))
        tag = role.parent.find("a").text
        man = removecomma(tag) # name of staff

        # checks if role is a target role and updates dictionary
        for x in positions:
            try:
                if x in split:
                    positions[x] = f"{positions.get(x)} {man}," 
            except:
                positions[x] = ""
                log.writeError(f"Error in show {dict.get('id')} trying to get staff {x}")

    # adds original creator to show creator
    positions['creator'] = f"{positions.get('creator')}{positions.get('original creator')}"
    positions.pop('original creator')

    # updates overall dictionary
    for x in positions:
        positions[x] = positions.get(x).rstrip(", ").strip()
        dict.update({x: positions.get(x)})

# main script
def main():

    log = ScrapeLog() # create object for log scraping progress

    # takes number of pages to scrape from console input
    currpage = log.getMal() # gets current page number
    try: 
        endpage = currpage + sys.argv[1]
    except:
        endpage = currpage + 10

    # gets each anime on the page and scrape their corresponding page
    for i in range(currpage, endpage):
        # requests shows on popularity page
        url = "https://myanimelist.net/topanime.php?&limit=" + str(i*50)
        poppage = requests.get(url)
        popsoup = bs(poppage.content, "html.parser")
        popresults = popsoup.find(id="contentWrapper")
        table = popresults.select("tr.ranking-list") # finds each show object

        # gets the data for each show
        for element in table:
            show = element.find("a", class_="hoverinfo_trigger")["href"]
            grabpage(show, log)

    log.progUpdate("mal", endpage) # update progress
    os.startfile(path) # open the csv file

if __name__=="__main__":
    main()