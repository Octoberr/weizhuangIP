import getflight
import getflightdata

import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
from cmreslogging.handlers import CMRESHandler
from Utils.config import config


def config_logging():
    esConf = config['es']
    logging.basicConfig(level=logging.DEBUG)
    handler = CMRESHandler(hosts=[{'host': esConf['host'], 'port': esConf['port']}],
                            auth_type=CMRESHandler.AuthType.NO_AUTH,
                            es_index_name=esConf['index'],
                            es_additional_fields={'App': 'AutoPushOrder', 'Environment': 'Dev'})
    log = logging.getLogger()
    log.addHandler(handler)
    log.setLevel(level=logging.DEBUG)

def main():
    config_logging()
    logging.info(datetime.datetime.now(), "Crawling the start")
    fp = getflight.FCZPAC()
    gt = getflightdata.GETFLIGHTDATA()
    fp.start()
    gt.getFlightData()
    logging.info(datetime.datetime.now(), "Crawling the end")


if __name__ == '__main__':
    logging.info(datetime.datetime.now(), "The program has started")
    scheduler = BlockingScheduler()
    main()
    scheduler.add_job(main, 'interval', hours=12)
    scheduler.start()
