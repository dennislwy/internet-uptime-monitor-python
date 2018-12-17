import logging
from httplib import HTTPConnection, socket

class Internet(object):
    def __init__(self, log=None):
        self.log = log or logging.getLogger(__name__)

    def Reachable(self, urls=None):
        """
        Check if internet reachable
        :param urls: List of url(s) to check
        :return: True if any of the url reachable, else False
        """
        try:
            if urls is None:
                urls = ["www.google.com", 'www.yahoo.com', 'www.facebook.com']

            for i in range(len(urls)):
                if self._get_site_status(urls[i]):
                    return True  # we are connected to the net
        except Exception as e:
            self.log.error(e, exc_info=True)
        return False  # either internet is down or the world has ended

    def _get_site_status(self, url):
        self.log.debug("Checking site: '%s'" % url)
        response = self._get_response(url)
        try:
            status_code = getattr(response, 'status')
            self.log.debug('Status code: %d' % status_code)
            if status_code == 200 or \
                    status_code == 301 or \
                    status_code == 302:
                self.log.debug("Site reachable")
                return True
            else:
                self.log.debug("Site unreachable")
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