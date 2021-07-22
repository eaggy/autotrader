# -*- coding: utf-8 -*-
"""The file contains some useful functions."""

import re
import smtplib
import datetime
import requests
from random import randrange
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from setup_logger import logger


def FWB_closed():
    """
    Check if Frankfurt Stock Exchange (FWB) closed today.

    Returns
    -------
    closed : bool
        True if closed, False else.

    """
    closed = False
    url_calendar = ('https://www.xetra.com/'
                    'xetra-de/handel/handelskalendar-und-zeiten')

    headers = {'User-Agent': ('Mozilla/5.0 (X11; Linux x86_64) '
                              'AppleWebKit/537.11 (KHTML, like Gecko) '
                              'Chrome/23.0.1271.64 Safari/537.11'),
               'Accept': ('text/html,application/xhtml+xml,'
                          'application/xml;q=0.9,*/*;q=0.8'),
               'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
               'Accept-Encoding': 'none',
               'Accept-Language': 'en-US,en;q=0.8',
               'Connection': 'keep-alive'}

    months = {'Jan': 1,
              'Feb': 2,
              'Mär': 3,
              'Apr': 4,
              'Mai': 5,
              'Jun': 6,
              'Jul': 7,
              'Aug': 8,
              'Sep': 9,
              'Okt': 10,
              'Nov': 11,
              'Dez': 12}

    # check, if today is a weekend
    today = datetime.datetime.now()
    if today.weekday() in [5, 6]:
        closed = True
        return closed

    # get dates when FWB is closed
    try:
        # get content of the web-page
        r = requests.get(url_calendar, headers=headers)
        if r.status_code == requests.codes.ok:
            html = BeautifulSoup(r.content, 'html.parser')

            # get dates
            div = html.find('div', attrs={
                'class': 'accordion grid6Col embeddedTeaser'})
            h3_all = div.find_all('h3')
            for h3 in h3_all:
                d_m = ''
                d_m = re.search(r'^\d{1,2}\. [a-zA-Z]{3}', h3.text).group(0)
                if d_m:
                    d = int(d_m.split('.')[0])
                    m = months[d_m.split()[1]]
                    if today.day == d and today.month == m:
                        closed = True
                        return closed

    except Exception as e:
        logger.error(e)

    return closed


def time_plan_convertor(time_plan):
    """
    Convert time plan to the list of time points in datatime format.

    Current date is used. Function returns only future time points.

    Parameters
    ----------
    time_plan : str
        Time plan containing one or several comma-separated lines
        in format H1[-H2][:M][/F], where H1 - start hour of execution,
        H2 - stop hour of execution, M - minutes of execution,
        F - number of executions per hour.

    Returns
    -------
    time_points : list
        List of time points in datatime format.

    """
    # get current date and time
    now = datetime.datetime.now()

    time_points = []
    for line in time_plan:
        # split each string by '/'
        split_line = line.split('/')
        # if string split
        if len(split_line) > 1:
            # calculate time step in minutes
            delta_minutes = 60
            try:
                delta_minutes = int(split_line[1])
                if delta_minutes == 0:
                    delta_minutes = 60
            except Exception as e:
                logger.error(e)

            # get initial hours and minutes
            split_line_0 = split_line[0].split(':')
            initial_hours = 0
            initial_minutes = 0
            if len(split_line_0) > 1:
                try:
                    initial_hours = split_line_0[0]
                    initial_minutes = int(split_line_0[1])
                except Exception as e:
                    logger.error(e)
            else:
                try:
                    initial_hours = split_line_0[0]
                    initial_minutes = 0
                except Exception as e:
                    logger.error(e)

            # get hours list
            hours = initial_hours.split('-')
            if len(hours) > 1:
                hours = range(int(hours[0]), int(hours[1]) + 1)
            else:
                hours = [int(hours[0])]

            # loop over hours
            for hour in hours:
                # loop over minutes
                for step in range(int(60/delta_minutes) + 1):
                    current_minutes = initial_minutes + step * delta_minutes
                    if current_minutes < 60:
                        current_time = '{:02d}:{:02d}' \
                            .format(hour, current_minutes)
                        try:
                            time_points.append(
                                datetime.datetime
                                .combine(now.date(),
                                         datetime.time.
                                         fromisoformat(current_time)))
                        except Exception as e:
                            logger.error(e)
        else:
            # convert string to time, if no '/' in the string
            # get minutes
            initial_minutes = 0
            hours_minutes = split_line[0].split(':')
            if len(hours_minutes) > 1:
                initial_minutes = int(hours_minutes[1])

            # get hours list
            hours = hours_minutes[0].split('-')
            if len(hours) > 1:
                hours = range(int(hours[0]), int(hours[1]) + 1)
            else:
                hours = [int(hours[0])]

            # loop over hours
            for hour in hours:
                current_time = '{:02d}:{:02d}' \
                    .format(hour, initial_minutes)
                try:
                    time_points.append(
                        datetime.datetime
                        .combine(now.date(),
                                 datetime.time.
                                 fromisoformat(current_time)))
                except Exception as e:
                    logger.error(e)

    # select future time points
    time_points = [tp for tp in time_points if tp > now]

    # randomize time points
    time_points = [tp+datetime.timedelta(seconds=randrange(60))
                   for tp in time_points]

    # sort time points
    time_points = sorted(set(time_points))

    return time_points


def send_email(subject, body, recipient, relay, user, password):
    """
    Send email over SMTP relay.

    Parameters
    ----------
    subject : str
        Subject of email.
    body : string
        Body of email.
    recipient : str, optional
        Email address of receiver.
    relay : str, optional
        SMTP-server address.
    user : str, optional
        User name.
    password : str, optional
        User password.

    Returns
    -------
    None.

    """
    try:
        conn = smtplib.SMTP(relay, 587)
        conn.starttls()
        conn.login(user, password)
        sender_email = user
        message = MIMEMultipart()
        message['From'] = user
        message['To'] = recipient
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        text = message.as_string()
        conn.sendmail(sender_email, recipient, text)
    except Exception as e:
        logger.error(e)
    finally:
        conn.quit()
