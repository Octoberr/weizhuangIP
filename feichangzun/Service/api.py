from flask import Flask, jsonify, Response
import gevent.monkey
from Utils.config import config
from directGetFlightData import getDirectFlight
from gevent.pywsgi import WSGIServer
gevent.monkey.patch_all()


app = Flask(__name__)


@app.route('/flight/<fno>/<date>')
def get_flight(fno, date):
    data = getDirectFlight(fno, date)
    return Response(data, content_type='application/json')


def run():
    httpConf = config['http']
    http_server = WSGIServer((httpConf['host'], httpConf['port']), app)
    try:
        print("Start at " + http_server.server_host +
              ':' + str(http_server.server_port))
        http_server.serve_forever()
    except(KeyboardInterrupt):
        print('Exit...')
