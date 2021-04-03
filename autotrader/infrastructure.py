# -*- coding: utf-8 -*-
"""The file contains the class definition of trading server/client."""

from setup_logger import logger
from socket import error as SocketError
from socket import errno as SocketErrno
from multiprocessing.connection import Listener, Client


class TradingServer:
    """Class representation of trading server."""

    def __init__(self,
                 host='localhost',
                 port=6000,
                 password=''
                 ):
        self.host = host
        self.port = port
        self.password = password
        self.listener = None
        self.connection = None
        self.running = False
        self.message = ''
        try:
            self.listener = Listener(
                (self.host, self.port),
                authkey=bytes(self.password, encoding='UTF-8'))
        except SocketError as e:
            if e.errno == SocketErrno.EADDRINUSE:
                logger.error('Address {}:{} already in use.'
                             .format(self.host, self.port))
            else:
                logger.error('Attempt to bind socket to {}:{} '
                             'returned socket error {}.'
                             .format(self.host, self.port, e.errno))
        except Exception as e:
            logger.error(e)

    def run(self):
        """
        Run trading server.

        Returns
        -------
        None.

        """
        if not self.listener:
            return None

        self.running = True
        while self.running:
            try:
                self.connection = self.listener.accept()
                logger.info('Connection accepted from {}.'
                            .format(self.listener.last_accepted))
            except SocketError as e:
                if e.errno == SocketErrno.ECONNRESET:
                    logger.error('Connection reset by peer.')
                else:
                    logger.error('Connection to {}:{} '
                                 'returned socket error {}.'
                                 .format(self.host, self.port, e.errno))
            except Exception as e:
                logger.error(e)

            while True:
                self.message = self.connection.recv()
                # check type of message
                # message is str
                if isinstance(self.message, str):
                    # stop the server
                    if self.message.lower() == 'shutdown':
                        self.connection.close()
                        self.running = False
                        logger.info('Trading server has been stopped.')
                        break
                    else:
                        self.connection.close()
                        logger.warning('Got unknown text message.')
                        break

                # message is dict
                elif isinstance(self.message, dict):
                    self.connection.close()
                    logger.info('Got trading info: {}.'.format(self.message))
                    # plase trading code here
                    #
                    #
                    #
                    break

                # another type of message
                else:
                    self.connection.close()
                    logger.warning('Got unknown type of message.')
                    break

        # close listener
        self.listener.close()


class TradingClient:
    """Class representation of trading client."""

    def __init__(self,
                 host='localhost',
                 port=6000,
                 password=''
                 ):
        self.host = host
        self.port = port
        self.password = password
        self.connection = None
        try:
            self.connection = Client(
                (self.host, self.port),
                authkey=bytes(self.password, encoding='UTF-8'))
        except SocketError as e:
            if e.errno == SocketErrno.ECONNREFUSED:
                logger.error('Connection to {}:{} was refused. '
                             'The server is down.'
                             .format(self.host, self.port))
            else:
                logger.error('Connection to {}:{} returned socket error {}.'
                             .format(self.host, self.port, e.errno))
        except Exception as e:
            logger.error(e)

    def send(self, message):
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
        if self.connection:
            self.connection.send(message)

    def send_close(self, message):
        """
        Send a message and close connection.

        Parameters
        ----------
        message : str or dict
            Message to be sent.

        Returns
        -------
        None.

        """
        if self.connection:
            self.connection.send(message)
            self.connection.close()

    def close(self):
        """
        Close connection.

        Parameters
        ----------
        None.

        Returns
        -------
        None.

        """
        if self.connection:
            self.connection.close()
