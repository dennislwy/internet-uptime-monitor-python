import os
import time
import signal
import logging.handlers
import logging.config
import apprise
from ago import human
from datetime import datetime
from ConfigParser import SafeConfigParser
import internet_connection

def main():
    try:
        while True:
            connection.is_online()
            #log.debug("Internet %s for %s" % (("up" if connection.state else "down"), human(connection.duration, 2, past_tense='{0}')))
            time.sleep(REFRESH)

    except KeyboardInterrupt:
        log.warn("Application interrupted")

    except Exception as e:
        log.error(e, exc_info=True)

#region Events

def onStateChange(sender, state):
    if state == connection.ONLINE:
        log.debug("Internet is up")

        diff = sender.online_since - sender.offline_since

        # if downtime was less than a day, no need include date in the message body
        if diff.days < 1:
            precision = 2 if diff.total_seconds() > 60 else 1
            title = "Internet resumed, it was down for %s" % human(diff, precision, past_tense='{0}')
            body = "Internet resumed back at %s, it was down since %s for %s" % \
                   (_trimDateTimeLeadingZero(sender.online_since.strftime("%I:%M:%S%p")),
                    _trimDateTimeLeadingZero(sender.offline_since.strftime("%I:%M:%S%p")), human(diff, precision, past_tense='{0}'))
        else:
            title = "Internet resumed, it was down for %s" % human(diff, 3, past_tense='{0}')
            body = "Internet resumed on %s, it was down since %s for %s" % \
                   (_trimDateTimeLeadingZero(sender.online_since.strftime("%d/%m/%y %I:%M:%S%p")),
                    _trimDateTimeLeadingZero(sender.offline_since.strftime("%d/%m/%y %I:%M:%S%p")), human(diff, 3, past_tense='{0}'))

        log.info(title)

        if INCLUDE_IPADDRESS: body += "\nInternal IP: %s, External IP: %s" % (sender.ip(), sender.external_ip())

        # notify all of the services loaded into our Apprise object
        _sendNotification(title, body)
    else:
        log.info("Internet is down since %s" % sender.offline_since.strftime("%I:%M:%S%p"))

def onTerminate(signum, frame):
    log.info("Application terminated (OS shutdown/reboot)")
    _sendNotification("Internet Uptime Monitor terminated")
    exit(1)

#endregion

#region Private methods

def _addNotificationService(cfgParser):
    """Add all of the notification services by their server url"""
    for option in cfgParser.options('apprise'):
        value = cfgParser.get('apprise', option)
        if value:
            log.debug("Adding services '%s://%s'" % (option, value))
            apobj.add("%s://%s" % (option, value))

def _sendNotification(title, body=None):
    if body is None: body = title
    log.debug("Send out notification, '%s'" % body)
    apobj.notify(title=title, body=body)

def _trimDateTimeLeadingZero(dt):
    return dt.lstrip("0").replace(" 0", " ")

#endregion

if __name__ == "__main__":
    currentPath = os.path.dirname(os.path.abspath(__file__))

    # refer https://pymotw.com/2/ConfigParser/
    cfgParser = SafeConfigParser()
    cfgParser.read('%s/settings.conf' % currentPath)
    DEBUG = cfgParser.getboolean('debugging', 'debug')
    SITES = [x.strip() for x in cfgParser.get('availability', 'sites').split(',')]
    REFRESH = cfgParser.getint('availability', 'refresh')
    INCLUDE_IPADDRESS = cfgParser.getboolean('general', 'include_ipaddress')

    # region logging
    # initialize logging
    logFilename = "%s/%s.log" % (currentPath, os.path.splitext(os.path.basename(__file__))[0])
    logging.config.fileConfig("%s/logging.ini" % currentPath)
    log = logging.getLogger()
    fileHandler = logging.handlers.TimedRotatingFileHandler(logFilename,'D',7,2)
    logLevel = logging.DEBUG if DEBUG else logging.INFO
    log.handlers[0].level = logLevel
    fileHandler.setLevel(logLevel)
    fileHandler.setFormatter(log.handlers[0].formatter)
    log.addHandler(fileHandler)

    # starting service
    log.info("Starting Internet Uptime Monitor%s" % (' (DEBUG mode)' if DEBUG else ''))
    # endregion

    # create internet connection monitor instance
    connection = internet_connection.Connection(SITES)
    connection.on_change = onStateChange

    # Python detect linux shutdown and run a command before shutting down
    # credits to code_onkel
    # https://stackoverflow.com/questions/39275948/python-detect-linux-shutdown-and-run-a-command-before-shutting-down
    signal.signal(signal.SIGTERM, onTerminate)

    # create an Apprise instance
    apobj = apprise.Apprise()

    # add Apprise notification settings
    _addNotificationService(cfgParser)

    # application started
    body = "Application started since %s" % _trimDateTimeLeadingZero(datetime.now().strftime("%d/%m/%y %I:%M:%S%p"))
    if INCLUDE_IPADDRESS: body += "\nInternal IP: %s, External IP: %s" % (connection.ip(), connection.external_ip())
    _sendNotification("Internet Uptime Monitor started", body)

    main()
