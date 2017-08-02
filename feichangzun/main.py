import getflight
import getflightdata
from multiprocessing import Process
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from cmreslogging.handlers import CMRESHandler
from Utils.config import config
from Service.api import run as ApiRun


def config_logging():
    esConf = config['es']
    logging.basicConfig(level=logging.DEBUG)
    if esConf['enabled']:
        handler = CMRESHandler(hosts=[{'host': esConf['host'], 'port': esConf['port']}],
                                auth_type=CMRESHandler.AuthType.NO_AUTH,
                                es_index_name=esConf['index'],
                                es_additional_fields={'App': 'AutoPushOrder', 'Environment': 'Dev'})
        log = logging.getLogger()
        log.addHandler(handler)
        log.setLevel(level=logging.DEBUG)

def main():
    config_logging()
    logging.info("Crawling the start")
    fp = getflight.FCZPAC()
    gt = getflightdata.GETFLIGHTDATA()
    fp.start()
    gt.getFlightData()
    logging.info("Crawling the end")

def run():
    logging.info("The program has started")
    scheduler = BlockingScheduler()
    main()
    scheduler.add_job(main, 'interval', hours=12)
    scheduler.start()


if __name__ == '__main__':
    apiProc = Process(target=ApiRun, name='ApiRunProc')
    collectProc = Process(target=run, name='CollectRunProc')
    p_list = []
    p_list.append(apiProc)
    p_list.append(collectProc)
    for p in p_list:
        p.start()
    for p in p_list:
        p.join()
