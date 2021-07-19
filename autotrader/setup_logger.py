# -*- coding: utf-8 -*-
"""The file contains logger."""

import sys
import logging

PATH_LOGS = '/var/www/flask/autotrader/autotrader.log'


class Logger():
    """Logger class."""

    def __init__(self, file_name=None):
        self.logger = logging.getLogger(__name__)
        formatter = logging.Formatter(
            ('%(asctime)s %(threadName)-8s %(name)-8s '
             '%(funcName)-8s %(levelname)-6s %(message)s'),
            datefmt='%d.%m.%Y %H:%M:%S')
        handler = logging.StreamHandler(sys.stdout)
        error = ''
        if isinstance(file_name, str):
            try:
                handler = logging.FileHandler(file_name)
            except FileNotFoundError as e:
                error = e
        elif file_name is not None:
            error = 'Parameter "{}" is not a string'.format(file_name)

        if not len(self.logger.handlers):
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG)

        if error:
            self.logger.error(error)


logger = Logger(PATH_LOGS).logger
