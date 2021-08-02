#!/opt/miniconda3/envs/flask/bin/python
# -*- coding: utf-8 -*-
"""Example of trading server."""
import sys
import configparser
import os
import sys
import inspect
currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from autotrader.setup_logger import logger
from autotrader.infrastructure import TradingServer

PATH_SETTINGS = '/var/www/flask/autotrader/settings.cfg'

# read configuration
try:
    logger.info('Reading configuration from {}...'.format(PATH_SETTINGS))
    config = configparser.ConfigParser()
    config.read_file(open(PATH_SETTINGS))

    HOST = config.get('LISTENER', 'HOST')
    PORT = int(config.get('LISTENER', 'PORT'))
    LISTENER_PASSWORD = config.get('LISTENER', 'PASSWORD')

    BROKER_USER = config.get('DEGIRO', 'USER')
    BROKER_PASSWORD = config.get('DEGIRO', 'PASSWORD')

except Exception as e:
    logger.critical(e)
    sys.exit(-1)


def trading_server(host, port, password, broker_user, broker_password, budget):
    """
    Create and run trading server.

    Parameters
    ----------
    host : str
        Host address which is being used by the Listener object.
    port : int
        Port which is being used by the Listener object.
    password : str
        Authentication key.
    broker_user : str
        Broker user.
    broker_password : str
        Broker password.
    budget : float
        Trading budget.

    Returns
    -------
    None.

    """
    # initialize trading server
    ts = TradingServer(host=host,
                       port=port,
                       password=password,
                       broker_user=broker_user,
                       broker_password=broker_password,
                       budget=budget)

    # run trading server
    ts.run()


if __name__ == "__main__":
    trading_server(host=HOST,
                   port=PORT,
                   password=LISTENER_PASSWORD,
                   broker_user=BROKER_USER,
                   broker_password=BROKER_PASSWORD,
                   budget=31000.0)
