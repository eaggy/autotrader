#!/opt/miniconda3/envs/flask/bin/python
# -*- coding: utf-8 -*-
"""Example of wikifolio notifier."""

import sys
import configparser
from autotrader.setup_logger import logger
from autotrader.scheduler import Scheduler
from provider.wikifolio import WikifolioMonitor

PATH_SETTINGS = '/var/www/flask/autotrader/settings.cfg'

# read configuration
try:
    logger.info('Reading configuration from {}...'.format(PATH_SETTINGS))
    config = configparser.ConfigParser()
    config.read_file(open(PATH_SETTINGS))

    USER_NAMES = config.get('WIKIFOLIO', 'USER').split()
    USER_PASSWORDS = config.get('WIKIFOLIO', 'PASSWORD').split()
    SYMBOL = config.get('WIKIFOLIO', 'SYMBOL')

    RECIPIENT = config.get('EMAIL', 'RECIPIENT')
    RELAY = config.get('EMAIL', 'RELAY')
    RELAY_USER = config.get('EMAIL', 'USER')
    RELAY_PASSWORD = config.get('EMAIL', 'PASSWORD')

    HOST = config.get('LISTENER', 'HOST')
    PORT = int(config.get('LISTENER', 'PORT'))
    LISTENER_PASSWORD = config.get('LISTENER', 'PASSWORD')

    TIME_PLAN = config.get('TIMING', 'PLAN').replace('\n', '').split(',')

except Exception as e:
    logger.critical(e)
    sys.exit(-1)


def wikifolio_notifier(host, port, listener_password, time_plan,
                       recipient, relay, relay_user, relay_password):
    """
    Set a wikifolio notifier according to the time plan.

    Parameters
    ----------
    host : str
        Host address which is being used by the Listener object.
    port : int
        Port which is being used by the Listener object.
    listener_password : str
        Authentication key.

    Returns
    -------
    None.

    """
    # initialize wikifolio monitor
    wfm = WikifolioMonitor()

    # login
    wfm.login(USER_NAMES, USER_PASSWORDS)

    # get wikifolio ID
    wfm.get_wikifolio_id(SYMBOL)

    # create scheduler
    sdl = Scheduler(host, port, listener_password)

    # create time plan
    sdl.create_time_plan(time_plan)

    # set scheduler
    sdl.set_scheduler(wfm.notify, recipient,
                      relay, relay_user, relay_password,
                      host=host, port=port, password=listener_password)


if __name__ == "__main__":
    wikifolio_notifier(HOST, PORT, LISTENER_PASSWORD, TIME_PLAN,
                       RECIPIENT, RELAY, RELAY_USER, RELAY_PASSWORD)
