# -*- coding: utf-8 -*-
"""The file contains the class definition of unofficial Degiro API."""

import os
import sys
import json
import inspect
import requests
import urllib3
import pandas as pd
from datetime import datetime, timedelta
from brokers import urls

currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from autotrader.setup_logger import logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Degiro:
    """Class representation of unofficial Degiro API."""

    def __init__(self,
                 url_login=urls.URL_DEGIRO_LOGIN,
                 url_config=urls.URL_DEGIRO_CONFIG,
                 url_client=urls.URL_DEGIRO_CLIENT,
                 url_data=urls.URL_DEGIRO_DATA,
                 url_order=urls.URL_DEGIRO_ORDER,
                 url_orders=urls.URL_DEGIRO_ORDERS,
                 url_place_order=urls.URL_DEGIRO_PLACE_ORDER,
                 url_search=urls.URL_DEGIRO_SEARCH,
                 url_logout=urls.URL_DEGIRO_LOGOUT
                 ):
        self.url_login = url_login
        self.url_config = url_config
        self.url_client = url_client
        self.url_data = url_data
        self.url_order = url_order
        self.url_orders = url_orders
        self.url_place_order = url_place_order
        self.url_search = url_search
        self.url_logout = url_logout
        self.signedup = False
        self.session_id = None
        self.client = None
        self.configuration = None
        self.capital = None
        self.orders = None
        self.headers = {'User-Agent':
                        ('Mozilla/5.0 (X11; Linux x86_64) '
                         'AppleWebKit/537.11 (KHTML, like Gecko) '
                         'Chrome/23.0.1271.64 Safari/537.11'),
                        'Accept': ('text/html,application/xhtml+xml,'
                                   'application/xml;q=0.9,*/*;q=0.8'),
                        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                        'Accept-Encoding': 'none',
                        'Accept-Language': 'en-US,en;q=0.8',
                        'Connection': 'keep-alive',
                        'content-type': 'application/json'}
        try:
            # create session
            logger.info('Creating new session...')
            self.session = requests.Session()
        except Exception as e:
            logger.critical(e)
            sys.exit(-1)

    def login(self, user, password):
        """
        Log into Degiro.

        Parameters
        ----------
        user : str
            User name.
        password : str
            User password.

        Returns
        -------
        None.

        """
        # check if signed up
        if self.signedup:
            logger.warning('Already signed up.')
            return None

        payload = {'username': user,
                   'password': password,
                   'isPassCodeReset': False,
                   'isRedirectToMobile': False}

        try:
            auth = self.session.post(self.url_login,
                                     headers=self.headers,
                                     json=payload)

            # check if response ok
            if auth.status_code == requests.codes.ok:
                auth_json = json.loads(auth.content)
                if auth_json['status'] == 0:
                    # signed in
                    self.session_id = auth_json['sessionId']
                    self.signedup = True
                    logger.info('Logged in as {}.'.format(user))
                    return None

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(auth.status_code))

        except Exception as e:
            logger.error(e)

        # notify about failed login and exit
        self.signedup = False
        message = 'Login failed.'
        logger.critical(message)
        sys.exit(-1)

    def logout(self):
        """
        Log off from Degiro.

        Returns
        -------
        None.

        """
        # check if signed up
        if not self.signedup:
            logger.warning('Not signed up.')
            return None

        # check if session ID is existing
        if not self.session_id:
            logger.warning('Session ID does not exist.')
            return None

        # check if account ID is existing
        if not self.client['intAccount']:
            logger.warning('Account ID does not exist.')
            return None

        payload = {'intAccount': str(self.client['intAccount']),
                   'sessionId': self.session_id}

        try:
            url = self.url_logout + ';jsessionid=' + self.session_id
            logout_response = self.session.get(url,
                                               headers=self.headers,
                                               params=payload)

            # check if response ok
            if logout_response.status_code == requests.codes.ok:
                logger.info('Logged out.')

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(logout_response.status_code))

        except Exception as e:
            logger.error(e)

        return None

    def get_config(self):
        """
        Get configuration.

        Returns
        -------
        None.

        """
        # check if signed up
        if not self.signedup:
            logger.warning('Not signed up.')
            return None

        # check if session ID is existing
        if not self.session_id:
            logger.warning('Session ID does not exist.')
            return None

        cookie = {'JSESSIONID': self.session_id}

        try:
            config_response = self.session.get(self.url_config,
                                               headers=self.headers,
                                               cookies=cookie)

            # check if response ok
            if config_response.status_code == requests.codes.ok:
                config_response_json = json.loads(config_response.content)

                # get configuration
                self.configuration = config_response_json['data']
                logger.info('Got configuration.')

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(config_response.status_code))

        except Exception as e:
            logger.error(e)

        return None

    def get_user_info(self):
        """
        Get information about the logged user.

        Returns
        -------
        None.

        """
        # check if signed up
        if not self.signedup:
            logger.warning('Not signed up.')
            return None

        # check if session ID is existing
        if not self.session_id:
            logger.warning('Session ID does not exist.')
            return None

        payload = {'sessionId': self.session_id}

        try:
            client_response = self.session.get(self.url_client,
                                               headers=self.headers,
                                               params=payload)

            # check if response ok
            if client_response.status_code == requests.codes.ok:
                client_response_json = json.loads(client_response.content)

                # get client info
                self.client = client_response_json['data']
                logger.info('Got client information.')

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(client_response.status_code))

        except Exception as e:
            logger.error(e)

        return None

    def get_data(self, data_type):
        """
        Get amount of cash or actual portfolio.

        Parameters
        ----------
        data_type : str
            `cashFunds` to get amount of cash or
            `portfolio` to get actual portfolio.

        Returns
        -------
        None.

        """
        # check if signed up
        if not self.signedup:
            logger.warning('Not signed up.')
            return None

        # check if session ID is existing
        if not self.session_id:
            logger.warning('Session ID does not exist.')
            return None

        # check if account ID is existing
        if not self.client['intAccount']:
            logger.warning('Account ID does not exist.')
            return None

        # check if data_type is correct
        if data_type not in ['cashFunds', 'portfolio']:
            logger.warning('Wrong data_type.')
            return None

        payload = {data_type: 0}

        try:
            url = self.url_data + str(self.client['intAccount']) \
                + ';jsessionid=' + self.session_id
            data_response = self.session.get(url,
                                             headers=self.headers,
                                             params=payload)

            # check if response ok
            if data_response.status_code in [requests.codes.ok,
                                             requests.codes.created]:
                data_response_json = json.loads(data_response.content)

                # get capital
                if data_type == 'cashFunds':
                    capital = {item['value'][1]['value']:
                               item['value'][2]['value']
                               for item in
                               data_response_json['cashFunds']['value']}
                    self.capital = capital
                    logger.info('Got capital of {} EUR.'
                                .format(capital['EUR']))

                # get portfolio
                elif data_type == 'portfolio':
                    positions = []
                    names = ['positionType',
                             'breakEvenPrice',
                             'price',
                             'size',
                             'value']
                    for item in data_response_json['portfolio']['value']:
                        position = {}
                        position['id'] = item['id']
                        for i in item['value']:
                            for name in names:
                                if i['name'] == name:
                                    position[name] = i['value']
                        if position:
                            if position[
                                    'positionType'] == 'PRODUCT' and position[
                                        'size'] > 0.0:
                                positions.append(position)

                    if positions:
                        self.portfolio = pd.DataFrame(positions)
                        logger.info('Got portfolio of {} positions.'
                                    .format(self.portfolio.shape[0]))

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(data_response.status_code))

        except Exception as e:
            logger.error(e)

        return None

    def get_orders(self, from_date=None, to_date=None, active=True):
        """
        Get orders.

        With the default parameters it gets only active orders placed
        between today and 90 days ago.

        Parameters
        ----------
        from_date : str, optional
            Start date for the selection of time period. The default is None.
        to_date : str, optional
            End date for the selection of time period. The default is None.
        active : bool, optional
            Select active orders only, if it is true. The default is True.

        Returns
        -------
        None.

        """
        # check if signed up
        if not self.signedup:
            logger.warning('Not signed up.')
            return None

        # check if session ID is existing
        if not self.session_id:
            logger.warning('Session ID does not exist.')
            return None

        # check if account ID is existing
        if not self.client['intAccount']:
            logger.warning('Account ID does not exist.')
            return None

        # check to_date
        if to_date:
            try:
                to_date = datetime.strptime(to_date, '%d.%m.%Y')
            except ValueError:
                logger.warning('Date in format "dd.mm.YYYY" is required.')
                return None
        else:
            # set as today
            to_date = datetime.today()

        # check from_date
        if from_date:
            try:
                from_date = datetime.strptime(from_date, '%d.%m.%Y')
            except ValueError:
                logger.warning('Date in format "dd.mm.YYYY" is required.')
                return None
        else:
            # set as today - 90 days
            from_date = datetime.today() - timedelta(days=90)

        # check range between from_date and to_date:
        if (to_date - from_date).days > 90:
            logger.warning('The maximal time interval is 90 days.')
            return None

        # check if from_dateis less than to_date:
        if to_date < from_date:
            logger.warning('Negative time interval is not allowed.')
            return None

        payload = {'fromDate': from_date.strftime('%d/%m/%Y'),
                   'toDate': to_date.strftime('%d/%m/%Y'),
                   'intAccount': str(self.client['intAccount']),
                   'sessionId': self.session_id}

        try:
            orders_response = self.session.get(self.url_orders,
                                               headers=self.headers,
                                               params=payload)

            # check if response ok
            if orders_response.status_code == requests.codes.ok:
                orders_response_json = json.loads(orders_response.content)

                # get orders
                orders = pd.DataFrame(orders_response_json['data'])
                if active:
                    orders = orders.loc[orders['isActive'], :]
                self.orders = orders
                logger.info('Got {} order{}.'.format(
                    self.orders.shape[0],
                    '' if self.orders.shape[0] == 1 else 's'))

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(orders_response.status_code))

        except Exception as e:
            logger.error(e)

        return None

    def place_order(self, buy_sell, product_id, size, limit=None,
                    stop_loss=None, order_type=0, validity=1):
        """
        Place a buy or sell order.

        Parameters
        ----------
        buy_sell : str
            Order type: `BUY` for buy orders or `SELL` for sell orders.
        product_id : str
            Product ID.
        size : int
            Product size.
        limit : float, optional
            Limit of the order. The default is None.
        stop_loss : float, optional
            Stop loss of the order. The default is None.
        order_type : int, optional
            Order type: `0` (limit order), `1` (stop limit order),
            `2` (market order), or `3` (stop loss order). The default is `0`.
        validity : int, optional
            Order validity: `1` (daily) or `3` (unlimited). The default is `1`.

        Returns
        -------
        None.

        """
        # check if signed up
        if not self.signedup:
            logger.warning('Not signed up.')
            return None

        # check if session ID is existing
        if not self.session_id:
            logger.warning('Session ID does not exist.')
            return None

        # check if account ID is existing
        if not self.client['intAccount']:
            logger.warning('Account ID does not exist.')
            return None

        # check if buy_sell is correct
        if buy_sell not in ['BUY', 'SELL']:
            logger.warning('Only values "BUY" or "SELL" are allowed.')
            return None

        # check if order size is correct
        if size == 0:
            logger.warning('Order size must be not equal zero.')
            return None

        # check if order type is correct
        # limit order
        if order_type == 0:
            if not limit:
                logger.warning('Limit is required for limit order.')
                return None
            if stop_loss:
                logger.warning('Stop loss is not required for limit order.')
                return None
        # stop limit order
        elif order_type == 1:
            pass
        # market order
        elif order_type == 2:
            if limit:
                logger.warning('Limit is not required for market order.')
                return None
            if stop_loss:
                logger.warning('Stop loss is not required for market order.')
                return None
        # stop loss order
        elif order_type == 3:
            pass
        else:
            logger.warning('Only values 0 (limit), '
                           '1 (stoplimit), '
                           '2 (market), '
                           'or 3 (stop loss), '
                           'are allowed.')
            return None

        # check if order validity is correct
        if validity not in [1, 3]:
            logger.warning('Only values 1 (daily) or 3 (unlimited) '
                           'are allowed.')
            return None

        confirmation_id = ''
        params = {'intAccount': str(self.client['intAccount']),
                  'sessionId': self.session_id}
        payload = {'buySell': buy_sell,
                   'orderType': order_type,
                   'productId': product_id,
                   'timeType': validity,
                   'size': size,
                   'price': limit,
                   'stopPrice': stop_loss}

        try:
            url = self.url_place_order + ';jsessionid=' + self.session_id
            place_order_response = self.session.post(url,
                                                     headers=self.headers,
                                                     params=params,
                                                     json=payload)

            # check if response ok
            if place_order_response.status_code == requests.codes.ok:
                place_order_response_json = json.loads(
                    place_order_response.content)
                confirmation_id = place_order_response_json[
                    'data']['confirmationId']
                transaction_fees = place_order_response_json[
                    'data']['transactionFees']
                currencies = self.capital.keys()
                total_fee = {}
                for currency in currencies:
                    total_fee[currency] = 0.0
                    for fee in transaction_fees:
                        if fee['currency'] == currency:
                            total_fee[currency] += fee['amount']

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(place_order_response.status_code))

            if confirmation_id:
                url = self.url_order + confirmation_id + ';jsessionid=' \
                    + self.session_id
                confirm_response = self.session.post(url,
                                                     headers=self.headers,
                                                     params=params,
                                                     json=payload)

                # check if response ok
                if confirm_response.status_code == requests.codes.ok:
                    confirm_response_json = json.loads(
                        confirm_response.content)
                    order_id = confirm_response_json['data']['orderId']
                    logger.info('Placed order with ID {}.'.format(order_id))

                # response is not ok
                else:
                    logger.error('Response status code: {}'
                                 .format(confirm_response.status_code))

        except Exception as e:
            logger.error(e)

        return None

    def cancel_order(self, order_id):
        """
        Cancel order by the order ID.

        Parameters
        ----------
        order_id : str
            Order ID.

        Returns
        -------
        None.

        """
        # check if signed up
        if not self.signedup:
            logger.warning('Not signed up.')
            return None

        # check if session ID is existing
        if not self.session_id:
            logger.warning('Session ID does not exist.')
            return None

        # check if account ID is existing
        if not self.client['intAccount']:
            logger.warning('Account ID does not exist.')
            return None

        payload = {'intAccount': self.client['intAccount'],
                   'sessionId': self.session_id}

        try:
            url = self.url_order + order_id + ';jsessionid=' + self.session_id
            delete_order_response = self.session.delete(url,
                                                        headers=self.headers,
                                                        data=payload)

            # check if response ok
            if delete_order_response.status_code == requests.codes.ok:
                logger.info('Deleted order with ID {}.'.format(order_id))

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(delete_order_response.status_code))

        except Exception as e:
            logger.error(e)

        return None

    def search_product_id(self, text, by='isin', limit=None, exchange=None):
        """
        Search product ID by a product name, ISIN, or symbol.

        Parameters
        ----------
        text : str
            Search text.
        by : str
            Search by name, isin, or symbol. The default is 'isin'.
        limit : int, optional
            Restrict search results by limit entries. The default is None.
        exchange : str, optional
            Search for the given exchange only. The default is None.

        Returns
        -------
        None.

        """
        # dictionary with exchanges
        exchanges = {'194': 'XET',
                     '195': 'FRA'}

        # check if signed up
        if not self.signedup:
            logger.warning('Not signed up.')
            return None

        # check if session ID is existing
        if not self.session_id:
            logger.warning('Session ID does not exist.')
            return None

        # check if account ID is existing
        if not self.client['intAccount']:
            logger.warning('Account ID does not exist.')
            return None

        # check if 'by' has a correct value
        if by not in ['name', 'isin', 'symbol']:
            logger.warning('Only values "name", "isin", '
                           'or "symbol" are allowed.')
            return None

        # check if exchange is existing in the dictionary
        if exchange:
            if exchange not in exchanges.values():
                logger.warning('Unknown exchange: "{}".'.format(exchange))
                return None

        payload = {'searchText': text,
                   'limit': limit,
                   'offset': 0,
                   'intAccount': str(self.client['intAccount']),
                   'sessionId': self.session_id}

        try:
            search_response = self.session.get(self.url_search,
                                               headers=self.headers,
                                               params=payload)

            # check if response ok
            if search_response.status_code == requests.codes.ok:
                search_response_json = json.loads(
                        search_response.content)
                products = search_response_json['products']

                # build dictionary with codes of exchanges
                codes = dict((value, key) for key, value in exchanges.items())

                found = {}
                for product in products:
                    # search for the given exchange only
                    if exchange:
                        if codes[exchange] != product['exchangeId']:
                            continue

                    # search by isin
                    if by == 'isin':
                        if text.lower() == product['isin'].lower():
                            found[exchanges[product['exchangeId']]] = product[
                                'id']
                    # search by symbol
                    elif by == 'symbol':
                        if text.lower() == product['symbol'].lower():
                            found[exchanges[product['exchangeId']]] = product[
                                'id']
                    # search by name
                    else:
                        found[exchanges[product['exchangeId']]] = product['id']

                if found:
                    logger.info('The following product IDs were found: {}.'
                                .format(found))
                    return found

            # response is not ok
            else:
                logger.error('Response status code: {}'
                             .format(search_response.status_code))

        except Exception as e:
            logger.error(e)

        return None
