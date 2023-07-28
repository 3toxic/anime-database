from config import username, password, anidbpath as path
from mystuff import ScrapeLog
import requests
import csv
import os
import sys
from bs4 import BeautifulSoup as bs

#payload to log in
payload = {
    'show': 'main',
    'xuser': username,
    'xpass': password,
    'do.auth': 'Login'
}

header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"}

#data to scrape for
anime = {
    "id": None, #anidb id
    'title': None, #english title
    'japanese': None, #japanese title
    "type": None, #media format
    "rating": None, #this is weighted per user
    'average': None, #pure average score
    "users": None, #number of users
    'aired': None, #airing duration
    "episode": None, #number of episodes
    "duration": None, #episode length
    "studio": None, #animation studios
    "director": None, #director
    "music": None, #main composer
    "tags": None, #tags
}

# anime = {
#     "id": None
#     "title": None,
#     "japanese": None, 
#     "type": None, 
#     "score": None,
#     "users": None,
#     "favorites": None,
#     "aired": None, 
#     "episode": None, 
#     "duration": None,
#     "studio": None, 
#     "source": None, 
#     "genre": None, 
#     "theme": None,
#     "director": None,
#     "music": None,
#     "creator": None,
#     }

#tags to look for
get = {
    'data': ('Type', 'Year', 'Rating', 'Average', 'Stats'),
    'people': ('Direction:', "Music:", "Animation Work:", "Work:")
}

#mapping tags to dictionary
animemap = {
    'Direction:': 'director',
    "Music:": 'music',
    "Animation Work:": 'studio',
    "Stats": "users",
    "Year": 'aired',
    "Work:": "director"
}

#finds data 
def getdata(item):
    check = lambda tag: True if item.find(tag) else False
    if check('a'):
        bruh = item.find('a')
        temp = bruh.text.strip()
        return temp[:[i for i,n in enumerate(temp) if n.isdigit()][-1]+1]
    # elif check('span'):
    #     bruh = item.find('span')
    #     return bruh.text.strip()
    else:
        return item.text.strip()

#gets staff
def getperson(item):
    guy = item.find_all('a')
    tempstr = ", ".join(map(lambda i: i.text.strip(), guy)).rstrip(", ")
    return tempstr if tempstr else ""

#gets show title
def gettitle(item):
    parent = item.parent
    name = parent.select_one('td.value')
    return name.find('label').text.strip() if name.find('label') else name.find('span').text.strip()

#checks if there is a number in a string
def hasnum(str):
    for x in str:
        if x.isdigit():
            return True
        
    return False

#get the data for a show
def getshow(sess, url):
    show = sess.get(url, headers=header)
    soup = bs(show.content, "html.parser")
    html = soup.find('div', "g_content anime_all sidebar")
    results = html.find('div', class_="data")

    dict=anime.copy()

    tags = results.find('a', string='Tags').parent
    tags = tags.find_next_sibling('td')
    dict['tags'] = ", ".join(map(lambda i: i.text.strip(), tags.find_all('span', class_='tagname')))

    #new manual title time this shit should never break
    names = results.find_all('th', string=lambda text: text if 'Title' in text else None)
    japindex = [i for i,n in enumerate(names) if "Official Title" in n][1]
    names = list(map(gettitle, names[japindex-1:japindex+1]))
    dict['title'] = names[0]
    dict['japanese'] = names[1]
    dict['id'] = "".join([x for x in url if x.isdigit()])

    for item in get['data']:
        title = results.find('th', string=item)
        parent = title.parent #the tr

        if item in animemap:
            try:
                dict[animemap[item]] = getdata(parent.find('td', class_='value'))
            except:
                print(f"finding {item} in {dict['id']} fucking broke lmao")
                dict[animemap[item]] = ""
        else:
            try:
                dict[item.lower()] = getdata(parent.find('td', class_='value'))
            except:
                print(f"finding {item} in {dict['id']} fucking broke lmao")
                dict[item.lower()] = ""
            
    if hasnum(dict['type']):
        dict['episode'] = "".join([x for x in dict['type'] if x.isdigit()]) 
    elif dict['type']=="Movie":
        dict['episode'] = 1
    elif dict['aired'][-1]=='?':
        dict['episode'] = "ongoing" 
    else:
        dict['episode'] = ""
    dict['type'] = dict['type'].split()[0].rstrip(", ")

    length = html.find('div', class_="g_bubble duration")
    length = length.find('div', class_='val')
    length = length.text.strip().split()
    duration = 0
    for x in length:
        if x[-1]=='h':
            duration += 60*int(x[:len(x)-1])
        elif x[-1]=='m':
            duration += int(x[:len(x)-1])
    if dict['type']=="Movie" or dict['episode']==1:
        dict['duration'] = duration
    elif dict['episode']!="ongoing":
        dict['duration'] = round(duration/int(dict['episode'])) 
    else:
        None

    people = results.find('div', class_=lambda text: text if "g_bubble staff" in text else None)
    if people is not None:
    
        for role in get['people']:
            if dict[animemap[role]] is None:
                try:
                    person = people.find('a', string=role)
                    if person is not None:
                        person = person.parent.parent.find('td', class_="name creator")
                        dict[animemap[role]] = getperson(person)
                except:
                    print(f"{role} in {dict['id']} broke")
                    dict[animemap[role]] = ""
    else:
        for role in get['people']:
            dict[animemap[role]] = ""
                    
    return dict.values()

def main():

    log = ScrapeLog()
    currpage = log.getAnidb()

    try:
        getpage = sys.argv[1]
    except:
        getpage = 10
    with open("anidb.csv", 'w', newline='', encoding='utf-16') as f:
        writer = csv.writer(f, delimiter='\t')

        if f.mode=='w':
            writer.writerow(anime)
        
        with requests.Session() as session:
            session.post('https://anidb.net/user/login', data=payload, headers=header)
            for i in range(currpage, currpage+getpage):  
                pop_page = "https://anidb.net/anime/?noalias=1&orderby.name=1.1&orderby.rank_popularity=0.1&page=" + str(i) + "&view=list"
                pop_shows = session.get(pop_page, headers=header)
                pop_soup = bs(pop_shows.content, "html.parser")
                shows = pop_soup.find("tbody")

                for child in shows.select('tr'):
                    writer.writerow(getshow(session, "https://anidb.net" + child.find("a")['href']))

        log.progUpdate("anidb", currpage+getpage+1)

    os.startfile(path)

if __name__=="__main__":
    # main()
    with requests.Session() as session:
        session.post('https://anidb.net/user/login', data=payload, headers=header)
        url = "https://anidb.net/anime/6424"

        info = getshow(session, url)
        for x in info:
            print(x)