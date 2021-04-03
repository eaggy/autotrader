#!/opt/miniconda3/envs/flask/bin/python
# -*- coding: utf-8 -*-
"""Example of trading server."""

import os
import sys
import inspect
import configparser

currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from setup_logger import logger
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

except Exception as e:
    logger.critical(e)
    sys.exit(-1)


def trading_server(host, port, password):
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

    Returns
    -------
    None.

    """
    # initialize trading server
    ts = TradingServer(host=host,
                       port=port,
                       password=password)

    # run trading server
    ts.run()


if __name__ == "__main__":
    trading_server(host=HOST,
                   port=PORT,
                   password=LISTENER_PASSWORD)
