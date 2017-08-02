import getflightdata
import requests
from bs4 import BeautifulSoup
import random
import json
import pymongo
import datetime
from Utils.config import config

# import config
mongoConf = config['mongo']


feichangzun = 'http://www.variflight.com/flight/fnum/'
feichangzunhouzui = '.html?AE71649A58c77&fdate='




def get_headers():
    headers = {
        "X-Forwarded-For": '%s.%s.%s.%s' % (
            random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
        'Host': "www.variflight.com",
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate'}
    return headers


def getqueryflight(flight, flightdate):
    allflightlinks = []
    client = pymongo.MongoClient(host=mongoConf['host'], port=mongoConf['port'])
    db = client.swmdb
    feichangzhundata = db.feichangzun
    cursor = feichangzhundata.find({"Info.fno": flight, "Info.Date": flightdate})
    for el in cursor:
        allflightlinks.append(el)
    return allflightlinks


def getDirectFlight(flight, flightdate):
    strDate = datetime.datetime.strptime(flightdate, "%Y-%m-%d").strftime("%Y%m%d")
    gt = getflightdata.GETFLIGHTDATA()
    url = feichangzun + flight + feichangzunhouzui + strDate
    flightlist = []
    listHtml = requests.get(url, headers=get_headers())
    listSoup = BeautifulSoup(listHtml.text, 'lxml')
    listUrl = listSoup.find('div', class_='fly_list')
    if listUrl is not None:
        listhref = listUrl.find('div', class_='li_box').find_all('a')
        for link in listhref:
            if '/schedule' in link.get('href'):
                flightlist.append(link.get('href'))
    flightdictlist = gt.getaflightinfo(flightlist)
    if len(flightdictlist) == 0:
        return None
    flightdict = getFlightJsonData(flightdictlist)
    querdata = getqueryflight(flight, flightdate)
    if len(querdata) == 0:
        gt.insertintomongo(flightdict)
        del(flightdict['_id'])
    # flightdictr = json.dumps(flightdict)
    return flightdict


def getFlightJsonData(flightinfo):
    flightdic = {}
    info = {}
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
    return flightdic

#
# flight = '3U3048'
# flightdate ='2017-08-02'
#
# jsodater = getDirectFlight(flight, flightdate)
# print(jsodater)

