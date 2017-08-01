# coding:utf-8

import requests
from bs4 import BeautifulSoup
from retrying import retry
import re
import pymongo
import datetime
import random
import os

import config

feichangzun = 'http://www.variflight.com'


class GETFLIGHTDATA:
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

    def writeErrorLog(self, url):
        logfile = datetime.datetime.now().strftime("%Y%m%d") + '.log'
        if os.path.isfile(logfile):
            f = open(logfile, 'a+')
        else:
            f = open(logfile, 'w')
        f.write("Cant connect error:{}".format(url))
        f.close()

    @retry(stop_max_attempt_number=5)
    def getaflightinfo(self, aflight):     # 传进来一个航班的[link],获取到这个航班的信息
        flightinfolist = []
        for el in aflight:
            flightinfo = {}
            url = feichangzun + el
            # 发送请求
            try:
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
                flightinfolist.append(flightinfo)
            except:
                self.writeErrorLog(url)
                return []
        return flightinfolist

    def insertintomongo(self, flightdata):
        client = pymongo.MongoClient(host=config.mongo_config['host'], port=config.mongo_config['port'])
        db = client.swmdb
        feichangzhundata = db.feichangzun
        feichangzhundata.insert(flightdata)
        print(datetime.datetime.now(), 'data insert mongodb success')

    def getflightlink(self):
        allflightlinks = []
        client = pymongo.MongoClient(host=config.mongo_config['host'], port=config.mongo_config['port'])
        db = client.swmdb
        feichangzhundata = db.flightlink
        cursor = feichangzhundata.find({"pacstatu": 0}, {"Link": 1})
        for el in cursor:
            allflightlinks.append(el)
        return allflightlinks

    def updatestatus(self, flightid):
        client = pymongo.MongoClient(host=config.mongo_config['host'], port=config.mongo_config['port'])
        db = client.swmdb
        feichangzhundata = db.flightlink
        feichangzhundata.update({'_id': flightid}, {"$set": {"pacstatu": 1}})
        print(datetime.datetime.now(), "pacstatu has uodate")

    def getFlightData(self):
        allLinks = self.getflightlink()
        if len(allLinks) == 0:
            return
        for flight in allLinks:
            flightdic = {}
            info = {}
            flightinfo = self.getaflightinfo(flight['Link'])
            if len(flightinfo) == 0:
                self.updatestatus(flight['_id'])
                continue
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
                info['Date'] = flightinfo[init]['date']
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
                info['Date'] = flightinfo[init]['date']
                info['zql'] = ""
            flightdic['Info'] = info
            flightdic['List'] = flightinfo
            self.insertintomongo(flightdic)
            self.updatestatus(flight['_id'])
