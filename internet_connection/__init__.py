import logging
import commands
from datetime import datetime
from random import shuffle
from httplib import HTTPConnection, socket
from urllib import urlopen

class Connection(object):
    OFFLINE = 0
    ONLINE = 1
    UNKNOWN = 2

    # free external IP address providers
    _external_ip_providers = ['http://icanhazip.com',
                              'http://myip.dnsomatic.com',
                              'https://api.ipify.org',
                              'https://ipapi.co/ip',
                              'https://ident.me']

    # reference sites to check for internet availability
    _sites = ['www.google.com',
              'www.apple.com',
              'www.facebook.com',
              'www.amazon.com',
              'www.cnn.com']

    def __init__(self, sites=None, log=None):
        self.log = log or logging.getLogger(__name__)
        if sites is not None:
            self._sites = sites
            self.log.debug("Loading custom sites, %s" % sites)
        self._state = Connection.ONLINE
        self._dt_online = datetime.now()
        self._dt_offline = None

        self._on_online = None
        self._on_offline = None
        self._on_change = None

    def is_online(self):
        """
        Check if internet reachable
        :return: True if any of the internet sites reachable, else False
        """
        dt_offline = None

        try:
            shuffle(self._sites) # randomly shuffle site urls so we don't keep spamming same site all the time

            for i in range(len(self._sites)):
                if self._get_site_status(self._sites[i]): # site responded
                    if self._state == Connection.OFFLINE:
                        self._state = Connection.ONLINE # internet resumed
                        self._dt_online = datetime.now() # record down since when is online
                        if self._on_online is not None: self._on_online(self)
                        if self._on_change is not None: self._on_change(self, Connection.ONLINE)
                    return True  # we are connected to the net

                elif not dt_offline: # not response from site
                    # when internet down, checking through site list might be time consuming,
                    # so we record the datetime when we first detects internet was down (for accuracy purposes)
                    dt_offline = datetime.now()

        except Exception as e:
            self.log.error(e, exc_info=True)

        if self._state == Connection.ONLINE:
            self._state = Connection.OFFLINE # internet down
            self._dt_offline = dt_offline if dt_offline else datetime.now() # record down since when is offline
            if self._on_offline is not None: self._on_offline(self)
            if self._on_change is not None: self._on_change(self, Connection.OFFLINE)
        return False  # either internet is down or the world has ended

    def is_offline(self):
        return not self.is_online()

    def ip(self):
        """
        Get internal IP address
        :return: Internet IP address
        """
        return commands.getoutput('hostname -I').rstrip()

    def external_ip(self):
        """
        Get external IP address (public IP address)
        :return: External IP address if successful, else None
        """
        try:
            # randomly shuffle urls so we don't keep spamming same site all the time
            shuffle(self._external_ip_providers)

            # get external ip from providers and stop if valid ip address found, redundancy supported
            for i in range(len(self._external_ip_providers)):
                result = urlopen(self._external_ip_providers[i]).read().rstrip()
                self.log.debug("External IP returned by '%s' is '%s'" % (self._external_ip_providers[i], result))
                # simple validation for ip address
                if 6 < len(result) < 16 and result.count('.') == 3: return result
        except Exception as e:
            self.log.error(e, exc_info=True)
        return None

    #region Properties

    @property
    def state(self):
        """
        Get the current internet state
        :return: 0 means internet connection offline, 1 means internet connection online
        """
        return self._state

    @property
    def online_since(self):
        """Get the recent internet online datetime"""
        return self._dt_online

    @property
    def offline_since(self):
        """Get the recent internet offline datetime"""
        return self._dt_offline

    @property
    def duration(self):
        """Get the online or offline duration"""
        if self._dt_offline is None or self._dt_online >= self._dt_offline:
            return datetime.now() - self._dt_online
        else:
            return datetime.now() - self._dt_offline

    #region Events

    @property
    def on_online(self):
        """If implemented, called when internet connection state was first detected online"""
        return self._on_online

    @on_online.setter
    def on_online(self, func):
        """ Define the internet connection online state callback implementation.

        Expected signature is:
            on_online_callback(sender)

        sender:     the instance of this callback
        """
        self._on_online = func

    @property
    def on_offline(self):
        """If implemented, called when internet connection state was first detected offline"""
        return self._on_offline

    @on_offline.setter
    def on_offline(self, func):
        """ Define the internet connection offline state callback implementation.

        Expected signature is:
            on_offline_callback(sender)

        sender:     the instance of this callback
        """
        self._on_offline = func

    @property
    def on_change(self):
        """If implemented, called when internet connection state changed (either online or offline)"""
        return self._on_change

    @on_change.setter
    def on_change(self, func):
        """ Define the internet connection state changed callback implementation.

        Expected signature is:
            on_change_callback(sender, state)

        sender:     the instance of this callback
        state:      the current internet connection state (0 is offline, 1 is online)
        """
        self._on_change = func

    #endregion

    #endregion

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
        """Return response object from URL"""
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