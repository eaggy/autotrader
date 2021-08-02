# -*- coding: utf-8 -*-
"""The file contains the class definition of autotrader."""

from autotrader.setup_logger import logger
from brokers.degiro import Degiro


class Autotrader(Degiro):
    """Class representation of autotrader."""

    def __init__(self, user, password, budget, trading_info):
        self.user = user
        self.password = password
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

    def trade(self):
        """
        Execute a trade.

        Parameters
        ----------
        TO DO

        Returns
        -------
        None.

        """
        for trading_data in self.trading_data:
            # get ISIN from trading data
            try:
                isin = trading_data['isin']
            except KeyError:
                logger.error('Unexpected key in trading info '
                             '("isin" expected).')
                continue

            # get transaction from trading data
            try:
                transaction = trading_data['transaction']
            except KeyError:
                logger.error('Unexpected key in trading info '
                             '("transaction" expected).')
                continue

            # get price from trading data
            try:
                price = float(trading_data['price'])
            except KeyError:
                logger.error('Unexpected key in trading info '
                             '("price" expected).')
                continue
            except ValueError:
                logger.error('The price is not valid')
                continue

            # get size from trading data
            try:
                size = float(trading_data['size'])
                # if size is quotient
                if size < 1.0:
                    if price > 0.0:
                        size = round(self.budget * size/price)
                    else:
                        continue
                else:
                    size = round(size)
            except KeyError:
                logger.error('Unexpected key in trading info '
                             '("size" expected).')
                continue
            except ValueError:
                logger.error('The size is not valid')
                continue

            # check volume
            if price*size < self.budget/100.0:
                logger.error('Position size is too small.')
                continue

            # get broker info
            self.login(self.user, self.password)
            self.get_config()
            self.get_user_info()
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
                continue

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
                    continue

            # execute trade
            print('Executing {} for {} of {} at {}.'.format(transaction, product_id, size, price))
            #self.place_order(transaction, product_id, size,
            #                 limit=price, stop_loss=None,
            #                 order_type=0, validity=1)

