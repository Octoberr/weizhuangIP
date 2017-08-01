import getflight
import getflightdata

import datetime
from apscheduler.schedulers.blocking import BlockingScheduler


def main():
    print(datetime.datetime.now(), "Crawling the start")
    fp = getflight.FCZPAC()
    gt = getflightdata.GETFLIGHTDATA()
    fp.start()
    gt.getFlightData()
    print(datetime.datetime.now(), "Crawling the end")


if __name__ == '__main__':
    print(datetime.datetime.now(), "The program has started")
    scheduler = BlockingScheduler()
    main()
    scheduler.add_job(main, 'interval', hours=12)
    scheduler.start()
