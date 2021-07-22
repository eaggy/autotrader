# -*- coding: utf-8 -*-
"""The file contains the class definition of scheduler."""

import os
import sys
import time
import inspect
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from autotrader.setup_logger import logger
from autotrader.toolkit import FWB_closed, time_plan_convertor, send_email
from autotrader.infrastructure import TradingClient


class Scheduler:
    """Scheduler class."""

    def __init__(self, host, port, password):
        self.verbose = True
        self.signedup = False
        self.host = host
        self.port = port
        self.password = password
        self.time_plan = []
        self.scheduler = None

    def create_time_plan(self, time_plan):
        """
        Create a time plan.

        Parameters
        ----------
        time_plan : str
            List of time points.

        Returns
        -------
        None.

        """
        # check if today is not a bank holiday
        if FWB_closed():
            logger.info('Today is a bank holiday')
        else:
            try:
                # create time plan
                self.time_plan = time_plan_convertor(time_plan)
            except Exception as e:
                logger.warning(e)

        if not self.time_plan:
            # stop trading server
            tc = TradingClient(self.host, self.port, self.password)
            tc.stop_server()
            logger.warning('No time points in the time plan.')
            sys.exit(0)

    def set_scheduler(self, task, recipient, relay, user, relay_password,
                      **kwargs):
        """
        Set scheduler for a task `task` according to the time plan.

        Parameters
        ----------
        task : callable
            Function which should be executed by scheduler.
        recipient : str
            Email address of a recipient
        relay : str
            URL of relay email-server.
        user : str
            Email user for relay.
        relay_password :str
            Email password for relay.
        **kwargs : dict
            Keyword arguments.

        Returns
        -------
        None.

        """
        try:
            # create scheduler
            if self.scheduler:
                self.scheduler.shutdown(wait=False)
            self.scheduler = BackgroundScheduler()

            for time_point in self.time_plan:
                self.scheduler.add_job(task, 'date', run_date=time_point,
                                       kwargs=kwargs)

            # run scheduler
            self.scheduler.start()
            if self.verbose:
                print('Press Ctrl+{0} to exit'.format(
                    'Z' if os.name == 'nt' else 'C'))

            # send notification
            subject = 'Scheduler is set for the task {}'.format(task.__name__)
            body = ('The scheduler is successfully set for {} tasks.\n'
                    'The first task execution on {}.\n'
                    'The last task execution on {}.'.format(
                        len(self.time_plan),
                        self.time_plan[0],
                        self.time_plan[-1]))
            send_email(subject, body, recipient, relay, user, relay_password)

        except Exception as e:
            logger.critical(e)

        if self.scheduler:
            try:
                # wait till the last time of time plan
                while datetime.now() <= self.time_plan[-1]:
                    # wait 25 seconds
                    time.sleep(25)
            except (KeyboardInterrupt, SystemExit):
                # shut down scheduler
                self.scheduler.shutdown(wait=False)

            # shut down scheduler if running
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)

            # stop trading server
            tc = TradingClient(self.host, self.port, self.password)
            tc.stop_server()

        return None
