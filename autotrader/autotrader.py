# -*- coding: utf-8 -*-
"""The file contains the class definition of autotrader."""

from setup_logger import logger
from brokers.degiro import Degiro


class Autotrader(Degiro):
    """Class representation of autotrader."""

    def __init__(self, budget, trading_info):
        self.budget = budget
        self.source = None
        self.origin = None
        self.exchange = None
        try:
            self.source = trading_info['from']
            self.origin = trading_info['to']
            self.trading_data = trading_info['data']
            if self.origin.lower() == 'degiro':
                Degiro.__init__(self)
                self.exchange = 'XET'
            else:
                logger.warning('Unknown broker.')
                return None

        except KeyError:
            logger.error('Unexpected key in trading info.')
            return None

    def trade(self, user, password,
              isin='', transaction='', price=0.0, size=0):
        """
        Send a message.

        Parameters
        ----------
        message : str or dict
            Message to be sent.

        Returns
        -------
        None.

        """
        # get ISIN from trading data
        if isin == '':
            try:
                isin = self.trading_data['isin']
            except KeyError:
                logger.error('Unexpected key in trading info '
                             '("isin" expected).')
                return None

        # get transaction from trading data
        if transaction == '':
            try:
                transaction = self.trading_data['transaction']
            except KeyError:
                logger.error('Unexpected key in trading info '
                             '("transaction" expected).')
                return None

        # get price from trading data
        if price == 0.0:
            try:
                price = float(self.trading_data['price'])
            except KeyError:
                logger.error('Unexpected key in trading info '
                             '("price" expected).')
                return None
            except ValueError:
                logger.error('The price is not valid')
                return None

        # get size from trading data
        if size == 0:
            try:
                size = float(self.trading_data['size'])
                # if size is quotient
                if size < 1.0:
                    if price > 0.0:
                        size = round(self.budget * size/price)
                    else:
                        return None
                else:
                    size = round(size)
            except KeyError:
                logger.error('Unexpected key in trading info '
                             '("size" expected).')
                return None
            except ValueError:
                logger.error('The size is not valid')
                return None

        # check volume
        if price*size < self.budget/100.0:
            logger.error('Position size is too small.')
            return None

        # get broker info
        self.login(user, password)
        self.get_config()
        self.get_client_info()
        self.get_data('cashFunds')
        self.get_data('portfolio')
        #self.get_orders(active=True)

        # get product iD
        try:
            product_id = self.search_product_id(
                isin, by='isin', exchange=self.exchange)[self.exchange]
        except Exception as e:
            logger.error(e)
            logger.warning('No product ID was found.')
            return None

        # check sell size
        if transaction == 'SELL':
            try:
                # get actual size of position
                actual_size = self.portfolio.loc[
                    self.portfolio['id'] == product_id, 'size'].values[0]
                # adjust sell size, if required
                if (actual_size - size)*price < self.budget/100.0:
                    size = actual_size
            except Exception as e:
                logger.error(e)
                return None

        # execute trade
        self.place_order(transaction, product_id, size,
                         limit=price, stop_loss=None,
                         order_type=0, validity=1)
