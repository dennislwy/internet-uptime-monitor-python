import logging
from datetime import datetime
from random import shuffle
from httplib import HTTPConnection, socket
from urllib import urlopen

class Internet(object):
    DOWN = 0
    UP = 1

    # free external IP address providers
    _externalIpProviders = ["http://icanhazip.com",
                           "http://myip.dnsomatic.com",
                           "https://api.ipify.org",
                           "https://ipapi.co/ip",
                           "https://ident.me"]

    # default sites to check for internet availability
    _defaultSites = ["www.google.com",
                     'www.apple.com',
                     'www.facebook.com',
                     'www.amazon.com',
                     'www.yahoo.com',
                     'www.cnn.com']

    def __init__(self, onStateChangedCb=None, log=None):
        self.log = log or logging.getLogger(__name__)
        self._state = Internet.UP
        self._dt_up = datetime.now()
        self._dt_down = None
        self._onStateChangedCb = onStateChangedCb

    def Reachable(self, urls=None):
        """
        Check if internet reachable
        :param urls: List of url(s) to check
        :return: True if any of the url reachable, else False
        """
        dt_down = None

        try:
            if urls is None:
                urls = self._defaultSites

            shuffle(urls) # randomly shuffle urls so we don't keep spamming same site all the time

            for i in range(len(urls)):
                if self._get_site_status(urls[i]): # site responded
                    if self._state == Internet.DOWN: # internet resumed
                        self._dt_up = datetime.now()
                        self._state = Internet.UP
                        if self._onStateChangedCb is not None: self._onStateChangedCb(self, Internet.UP)

                    return True  # we are connected to the net

                elif not dt_down: # not response from site
                    # when internet down, checking through site list might be time consuming,
                    # so we record the datetime when we first detects internet was down (for accuracy purposes)
                    dt_down = datetime.now()

        except Exception as e:
            self.log.error(e, exc_info=True)

        if self._state == Internet.UP: # internet down
            self._dt_down = dt_down if dt_down else datetime.now()
            self._state = Internet.DOWN
            if self._onStateChangedCb is not None: self._onStateChangedCb(self, Internet.DOWN)
        return False  # either internet is down or the world has ended

    def ExternalIp(self):
        """Get external IP (public IP)"""
        try:
            # randomly shuffle urls so we don't keep spamming same site all the time
            shuffle(self._externalIpProviders)

            # get external ip from providers and stop if valid ip address found, redundancy supported
            for i in range(len(self._externalIpProviders)):
                result = urlopen(self._externalIpProviders[i]).read().rstrip()
                self.log.debug("External IP returned by '%s' is '%s'" % (self._externalIpProviders[i], result))
                #simple validation for ip address
                if 6 < len(result) < 16 and result.count('.') == 3: return result
        except Exception as e:
            self.log.error(e, exc_info=True)
        return None

    @property
    def State(self):
        """
        Get the current internet state
        :return: 0 means internet down, 1 means internet up
        """
        return self._state

    @property
    def DownSince(self):
        """Get the recent internet down datetime"""
        return self._dt_down

    @property
    def UpSince(self):
        """Get the recent internet up datetime"""
        return self._dt_up

    @property
    def Duration(self):
        """Get the duration of up/down time"""
        if self._dt_down is None or self._dt_up >= self._dt_down:
            return datetime.now() - self._dt_up
        else:
            return datetime.now() - self._dt_down

    #region Private methods

    def _get_site_status(self, url):
        self.log.debug("Checking site: '%s'" % url)
        response = self._get_response(url)
        try:
            status_code = getattr(response, 'status')
            if status_code == 200 or \
                    status_code == 301 or \
                    status_code == 302:
                self.log.debug("Site reachable, Status code: %d" % status_code)
                return True
            else:
                self.log.debug("Site unreachable, Status code: %d" % status_code)
        except AttributeError:
            pass
        except Exception as e:
            self.log.error(e, exc_info=True)
        return False # site down

    def _get_response(self, url):
        # Return response object from URL
        try:
            conn = HTTPConnection(url)
            conn.timeout = 3
            conn.request('HEAD', '/')
            return conn.getresponse()
        except socket.error:
            return None
        except Exception as e:
            self.log.error(e, exc_info=True)
            return None

    #endregion