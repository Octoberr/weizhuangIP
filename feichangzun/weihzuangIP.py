import requests
from bs4 import BeautifulSoup
from retrying import retry
import re
import pymongo
import datetime
import random
from apscheduler.schedulers.blocking import BlockingScheduler

import config



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
        client = pymongo.MongoClient(host=config.mongo_config['host'], port=config.mongo_config['port'])
        db = client.swmdb
        eagleyedates = db.feichangzun
        cursor = eagleyedates.find({"Info.fno": aircarfNo}, {"Info.Date": 1}).sort("Info.Date", -1).limit(1)
        for el in cursor:
            havedate = datetime.datetime.strptime(el["Info"]['Date'], "%Y-%m-%dT%H:%M:%S").date()
            return havedate

    def insertintomongo(self, flightdata):
        client = pymongo.MongoClient(host=config.mongo_config['host'], port=config.mongo_config['port'])
        db = client.swmdb
        eagleyedates = db.feichangzun
        eagleyedates.insert(flightdata)
        print(datetime.datetime.now(), 'insert mongodb success')

    @retry(stop_max_attempt_number=5)
    def getchuanghanglist(self):
        print('getchuanghanglist')
        try:
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
        except Exception as e:
            print(e)

    def getListData(self, flightlink, flightstr):
        print('getListData')
        today = datetime.datetime.now().date()
        allflightLink = []
        for i in range(len(flightlink)):
            alreadydate = self.getquerydate(flightstr[i])
            print("查询结果", alreadydate)
            if alreadydate is not None:
                looptimes = (today + datetime.timedelta(days=7) - alreadydate).days
                tmpurl = (feichangzun + flightlink[i]).split('=')[0]
                for n in range(1, looptimes+1):
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
                        print("find a flight")
                        allflightLink.append(flightlist)
                    else:
                        print("no data:", n)
                        continue
            else:
                tmpurl2 = (feichangzun + flightlink[i]).split('=')[0]
                for n in range(0, 7):
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
                        print("find a flight")
                        allflightLink.append(flightlist)
                    else:
                        break
        return allflightLink                  # [[一个航班],[]]

    @retry(stop_max_attempt_number=5)
    def getaflightinfo(self, aflight):     # 传进来一个航班的[link],获取到这个航班的信息
        flightinfolist = []
        for el in aflight:
            flightinfo = {}
            url = feichangzun + el
            # 发送请求
            listHtml = requests.get(url, headers=self.get_headers())
            listSoup = BeautifulSoup(listHtml.text, 'lxml')
            qfcity = listSoup.find('div', class_='cir_l curr').get_text().strip()
            ddcity = listSoup.find('div', class_='cir_r').get_text().strip()
            code = el.split('/')[2].split('-')
            qfcitycode = code[0]
            ddcitycode = code[1]
            fno = code[2].split('.')[0]
            city = listSoup.find_all('div', class_='fly_mian')
            qfsimple = city[0].find('h2').get('title').split(qfcity)[1]
            if 'T' in qfsimple:
                qfTerminal = 'T' + qfsimple.split('T')[1]
            else:
                qfTerminal = ""
            qf = qfcity + " " + qfsimple
            ddsimple = city[len(city)-1].find('h2').get('title').split(ddcity)[1]
            if 'T' in ddsimple:
                ddTerminal = 'T' + ddsimple.split('T')[1]
            else:
                ddTerminal = ""
            dd = ddcity + " " + ddsimple
            qftimestr = city[0].find('span', class_='date').get_text().strip()
            qfdate = re.compile('\d{4}[-/]\d{2}[-/]\d{2}').findall(qftimestr)
            qftime = qfdate[0] + "T" + re.compile('\d{2}[:/]\d{2}').findall(qftimestr)[0]
            ddtimestr = city[len(city)-1].find('span', class_='date').get_text().strip()
            dddate = re.compile('\d{4}[-/]\d{2}[-/]\d{2}').findall(ddtimestr)
            ddtime = dddate[0] + "T" + re.compile('\d{2}[:/]\d{2}').findall(ddtimestr)[0]
            state = listSoup.find('div', class_='reg').get_text()
            if state == '计划':
                stateid = 1
            else:
                stateid = 0
            flightinfo['qf'] = qf
            flightinfo['qf_city'] = qfcity
            flightinfo['qf_citycode'] = qfcitycode
            flightinfo['qf_simple'] = qfsimple
            flightinfo['dd'] = dd
            flightinfo['dd_simple'] = ddsimple
            flightinfo['dd_city'] = ddcity
            flightinfo['dd_citycode'] = ddcitycode
            flightinfo['qfTerminal'] = qfTerminal
            flightinfo['ddTerminal'] = ddTerminal
            flightinfo['jhqftime_full'] = qftime
            flightinfo['sjqftime_full'] = None
            flightinfo['jhddtime_full'] = ddtime
            flightinfo['sjddtime_full'] = None
            flightinfo['State'] = state
            flightinfo['stateid'] = stateid
            flightinfo['djk'] = '--'
            flightinfo['zjgt'] = '--'
            flightinfo['xlzp'] = '--'
            flightinfo['date'] = qfdate[0]
            flightinfo['fno'] = fno
            print('get a schedule from a schedule list')
            flightinfolist.append(flightinfo)
        return flightinfolist

    def start(self):
        print('start')
        flightdata = self.getchuanghanglist()
        flightlink = flightdata.flightlink
        flightstr = flightdata.flight
        listLink = self.getListData(flightlink, flightstr)
        for flight in listLink:
            flightdic = {}
            info = {}
            flightinfo = self.getaflightinfo(flight)
            if len(flightinfo) == 1:
                init = 0
                info['from'] = flightinfo[init]['qf']
                info['to'] = flightinfo[init]['dd']
                info['from_simple'] = flightinfo[init]['qf_simple']
                info['to_simple'] = flightinfo[init]['dd_simple']
                info['FromTerminal'] = flightinfo[init]['qfTerminal']
                info['ToTerminal'] = flightinfo[init]['ddTerminal']
                info['from_city'] = flightinfo[init]['qf_city']
                info['to_city'] = flightinfo[init]['dd_city']
                info['from_code'] = flightinfo[init]['qf_citycode']
                info['to_code'] = flightinfo[init]['dd_citycode']
                info['fno'] = flightinfo[init]['fno']
                info['Company'] = '3U'
                info['Date'] = flightinfo[init]['date']+"T00:00:00"
                info['zql'] = ""
            else:
                init = 1
                info['from'] = flightinfo[init]['qf']
                info['to'] = flightinfo[init]['dd']
                info['from_simple'] = flightinfo[init]['qf_simple']
                info['to_simple'] = flightinfo[init]['dd_simple']
                info['FromTerminal'] = flightinfo[init]['qfTerminal']
                info['ToTerminal'] = flightinfo[init]['ddTerminal']
                info['from_city'] = flightinfo[init]['qf_city']
                info['to_city'] = flightinfo[init]['dd_city']
                info['from_code'] = flightinfo[init]['qf_citycode']
                info['to_code'] = flightinfo[init]['dd_citycode']
                info['fno'] = flightinfo[init]['fno']
                info['Company'] = '3U'
                info['Date'] = flightinfo[init]['date']+"T00:00:00"
                info['zql'] = ""
            flightdic['Info'] = info
            flightdic['List'] = flightinfo
            self.insertintomongo(flightdic)

if __name__ == '__main__':
    fp = FCZPAC()
    print(datetime.datetime.now(), "The program has started")
    fp.start()
    scheduler = BlockingScheduler()
    # scheduler.add_job(some_job, 'interval', hours=1)
    scheduler.add_job(fp.start, 'interval', hours=12)
    scheduler.start()
