import os
import time
import signal
import logging.config
import apprise
from ago import human
from datetime import datetime
from ConfigParser import SafeConfigParser
from lib.internet import Internet

def main():
    try:
        while True:
            internet.Reachable(SITES)
            #log.debug("Internet %s for %s" % (("up" if internet.State else "down"), human(internet.Duration, 2, past_tense='{0}')))
            time.sleep(REFRESH)

    except KeyboardInterrupt:
        log.warn("Application interrupted")

    except Exception as e:
        log.error(e, exc_info=True)

#region Events
def onStateChanged(sender, available):
    if available:
        log.debug("Internet is up")

        diff = sender.UpSince - sender.DownSince

        # if downtime was less than a day, no need include date in the message body
        if diff.days < 1:
            precision = 2 if diff.total_seconds() > 60 else 1
            title = "Internet resumed, it was down for %s" % human(diff, precision, past_tense='{0}')
            body = "Internet resumed back at %s, it was down since %s for %s" % \
                   (_trimDateTimeLeadingZero(sender.UpSince.strftime("%I:%M:%S%p")),
                    _trimDateTimeLeadingZero(sender.DownSince.strftime("%I:%M:%S%p")), human(diff, precision, past_tense='{0}'))
        else:
            title = "Internet resumed, it was down for %s" % human(diff, 3, past_tense='{0}')
            body = "Internet resumed on %s, it was down since %s for %s" % \
                   (_trimDateTimeLeadingZero(sender.UpSince.strftime("%d/%m/%y %I:%M:%S%p")),
                    _trimDateTimeLeadingZero(sender.DownSince.strftime("%d/%m/%y %I:%M:%S%p")), human(diff, 3, past_tense='{0}'))

        log.info(title)

        if EXTERNALIP: body += ". External IP: %s" % internet.ExternalIp()

        # notify all of the services loaded into our Apprise object
        apobj.notify(
            title=title,
            body=body,
        )
    else:
        log.info("Internet is down since %s" % sender.DownSince.strftime("%I:%M:%S%p"))

def onTerminate(signum, frame):
    log.info("Application terminated (OS shutdown/reboot)")
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
    EXTERNALIP = cfgParser.getboolean('general', 'include_external_ip')

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

    internet = Internet(onStateChanged)

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
    if EXTERNALIP: body += ". External IP: %s" % internet.ExternalIp()
    apobj.notify(
        title="Internet Uptime Monitor started",
        body=body,
    )

    main()
