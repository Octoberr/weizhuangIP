import requests
from bs4 import BeautifulSoup
from retrying import retry
import pymongo
import datetime
import random
from Utils.config import config

# import config
mongoConf = config['mongo']

feichangzun = 'http://www.variflight.com'
allUrl = "http://www.variflight.com/sitemap.html?AE71649A58c77="
pausetime = 30000


class HANDL:
    def __init__(self, flight, flightlink):
        self.flight = flight
        self.flightlink = flightlink


class FCZPAC:
    def get_headers(self):
        headers = {
            "X-Forwarded-For": '%s.%s.%s.%s' % (
            random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
            'Host': "www.variflight.com",
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate'}
        return headers

    def getquerydate(self, aircarfNo):
        client = pymongo.MongoClient(host=mongoConf['host'], port=mongoConf['port'])
        db = client.swmdb
        feichangzhundata = db.feichangzun
        cursor = feichangzhundata.find({"Info.fno": aircarfNo}, {"Info.Date": 1}).sort("Info.Date", -1).limit(1)
        for el in cursor:
            havedate = datetime.datetime.strptime(el["Info"]['Date'], "%Y-%m-%dT%H:%M:%S").date()
            return havedate

    def insertFlight(self, flight):
        client = pymongo.MongoClient(host=mongoConf['host'], port=mongoConf['port'])
        db = client.swmdb
        feichangzhundata = db.flightlink
        feichangzhundata.insert(flight)
        print(datetime.datetime.now(), 'flight insert mongodb success')

    @retry(stop_max_attempt_number=5)
    def getchuanghanglist(self):
        startHtml = requests.get(allUrl, headers=self.get_headers())
        Soup = BeautifulSoup(startHtml.text, 'lxml')
        allA = Soup.find('div', class_='f_content').find_all('a')
        flight = []
        flightlink = []
        for i in range(1, len(allA)):
            if '3U' in allA[i].get_text():
                flight.append(allA[i].get_text())
                flightlink.append(allA[i].get('href'))
        return HANDL(flight, flightlink)

    def getListData(self, flightlink, flightstr):
        today = datetime.datetime.now().date()
        for i in range(len(flightlink)):
            alreadydate = self.getquerydate(flightstr[i])
            print("查询结果date:", alreadydate)
            if alreadydate is not None:
                looptimes = (today + datetime.timedelta(days=7) - alreadydate).days
                tmpurl = (feichangzun + flightlink[i]).split('=')[0]
                for n in range(1, looptimes+1):
                    flightjson = {}
                    flightlist = []
                    querydate = alreadydate + datetime.timedelta(days=n)
                    url = tmpurl + '&fdate={}'.format(querydate.strftime("%Y%m%d"))
                    listHtml = requests.get(url, headers=self.get_headers())
                    listSoup = BeautifulSoup(listHtml.text, 'lxml')
                    listUrl = listSoup.find('div', class_='fly_list')
                    if listUrl is not None:
                        listhref = listUrl.find('div', class_='li_box').find_all('a')
                        for link in listhref:
                            if '/schedule' in link.get('href'):
                                flightlist.append(link.get('href'))
                        flightjson['Link'] = flightlist
                        flightjson['pacstatu'] = 0  # 1为已经爬取，0为还没有爬取
                        self.insertFlight(flightjson)
                    else:
                        # 没有数据继续查询，寻找完7天
                        continue
            else:
                tmpurl2 = (feichangzun + flightlink[i]).split('=')[0]
                for n in range(0, 7):
                    flightjson = {}
                    flightlist = []
                    querydate2 = today + datetime.timedelta(days=n)
                    url2 = tmpurl2 + '&fdate={}'.format(querydate2.strftime("%Y%m%d"))
                    listHtml2 = requests.get(url2, headers=self.get_headers())
                    listSoup2 = BeautifulSoup(listHtml2.text, 'lxml')
                    listUrl2 = listSoup2.find('div', class_='fly_list')
                    if listUrl2 is not None:
                        listhref2 = listUrl2.find('div', class_='li_box').find_all('a')
                        for link2 in listhref2:
                            if '/schedule' in link2.get('href'):
                                flightlist.append(link2.get('href'))
                        flightjson['Link'] = flightlist
                        flightjson['pacstatu'] = 0  # 1为已经爬取，0为还没有爬取
                        self.insertFlight(flightjson)
                    else:
                        # 当没有找到数据就直接不找了
                        break

    def start(self):
        flightdata = self.getchuanghanglist()
        flightlink = flightdata.flightlink
        flightstr = flightdata.flight
        self.getListData(flightlink, flightstr)