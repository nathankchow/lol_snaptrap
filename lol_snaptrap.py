'''
takes a list of newline-separated summoner names in names.csv,
uses riot api key stored in api_key.txt to check availability date,
outputs results to log.txt
TODO:
- email user if name is available, or use an alternate form of notification 
- add option to suppress email/other notification if name is available
'''

import os
from pathlib import Path
import requests
import datetime
import calendar
from time import time

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.datetime(year, month, day, sourcedate.hour, sourcedate.minute, sourcedate.second)

class Summoner:
    key = open('api_key.txt').read()
    def __init__(self, username, region="NA"):
        self.name = username
        self.puuid = None
        self.lvl = None
        self.available = None
        self.last_played = None
        self.revision_date = None
        r = requests.get(
            "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + username,
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": "https://developer.riotgames.com",
                "X-Riot-Token": Summoner.key
            }
        )
        if r.status_code == 404:
            self.exists = False
            self.available = True
        else: 
            response = r.json()
            try:
                self.puuid = response["puuid"]
                self.lvl = response["summonerLevel"]
                self.exists = True
                self.revision_date = datetime.datetime.fromtimestamp(int(response['revisionDate']/1000))
            except KeyError:
                pass
    
    def get_last_played(self, debug=False):
        if self.puuid != None:
            response = requests.get(
                "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/"+self.puuid +"/ids?start=0&count=20",
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://developer.riotgames.com",
                    "X-Riot-Token": Summoner.key
                }
            ).json()
        try:
            self.latest_match = response[0]
        except:
            self.last_played = self.revision_date
            return self.last_played

        if self.latest_match != None:
            response = requests.get(
                "https://americas.api.riotgames.com/lol/match/v5/matches/" + self.latest_match,
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://developer.riotgames.com",
                    "X-Riot-Token": Summoner.key
                }
            ).json()
            if debug == True:
                return response
            self.last_played = datetime.datetime.fromtimestamp(int(response["info"]["gameStartTimestamp"]/1000))
            return self.last_played

    
    def get_availability(self):
        if self.exists == False:
            self.available = True
            return self.available
        else:
            if self.last_played == None:
                return None
            self.until_available = add_months(self.last_played, min(30,max(6,self.lvl))) - datetime.datetime.fromtimestamp(time())
            if self.until_available.days > 0:
                self.available = self.until_available
            else:
                self.available = True
        return self.available

def get_availability(name):
    sum = Summoner(name)
    sum.get_last_played()
    return sum.get_availability()

def main(log=True):
    if os.path.isfile('names.csv') != True:
        _ = os.path.join(os.path.dirname(__file__),'names.csv')
        if os.path.isfile(_) == True:
            file = _ 
        else:
            raise BaseException('names.csv not found in current directory or script directory.')
    else:
        file = 'names.csv'

    with open(file) as f:
        txt = f.read()
    names = txt.split('\n')
    results = []

    for name in names: 
        if name == '':
            continue
        print(f'{names.index(name)+1}/{len(names)}: {name}')
        results.append(f'{name.strip()}: {str(get_availability(name))}')
    for result in results:
        print(result)
    if log == True:
        with open('log.txt', 'w+') as f:
            f.write("\n".join(results))

if __name__ == "__main__":
    main()
