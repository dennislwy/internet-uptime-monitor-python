import os
import time
import signal
import logging.config
import apprise
from ago import human
from datetime import datetime
from ConfigParser import SafeConfigParser
from lib.internet import Internet
from lib.newold import NewOld

def main():
    try:
        available = NewOld(onChangeCb=onNetStatusChanged)
        while True:
            available.Value = Internet().Reachable(SITES)
            time.sleep(REFRESH)

    except KeyboardInterrupt:
        log.warn("Application interrupted")

    except Exception as e:
        log.error(e, exc_info=True)

def onNetStatusChanged(available):
    global dt_down

    if available.New:
        dt_up = datetime.now()
        log.debug("Internet is up")

        diff = dt_up - dt_down

        # if downtime was less than a day, no need include date in the message body
        if diff.days < 1:
            precision = 2 if diff.total_seconds() > 60 else 1
            title = "Internet resumed, it was down for %s" % human(diff, precision, past_tense='{0}')
            body = "Internet resumed on %s, it was down since %s for %s" % (dt_up.strftime("%I:%M:%S%p"), dt_down.strftime("%I:%M:%S%p"), human(diff, precision, past_tense='{0}'))
        else:
            title = "Internet resumed, it was down for %s" % human(diff, 3, past_tense='{0}')
            body = "Internet resumed on %s, it was down since %s for %s" % (dt_up.strftime("%d/%m/%y %I:%M:%S%p"), dt_down.strftime("%d/%m/%y %I:%M:%S%p"), human(diff, 3, past_tense='{0}'))
        log.info(title)

        # notify all of the services loaded into our Apprise object
        apobj.notify(
            title=title,
            body=body,
        )
    else:
        dt_down = datetime.now()
        log.info("Internet is down")

def onTerminate(signum, frame):
    log.info("Application terminated (OS shutdown/reboot)")

def addNotificationService(cfgParser):
    """Add all of the notification services by their server url"""
    for option in cfgParser.options('apprise'):
        value = cfgParser.get('apprise', option)
        if not value:
            apobj.add("%s://%s" % (option, value))

if __name__ == "__main__":
    currentPath = os.path.dirname(os.path.abspath(__file__))

    # refer https://pymotw.com/2/ConfigParser/
    cfgParser = SafeConfigParser()
    cfgParser.read('%s/settings.conf' % currentPath)
    DEBUG = cfgParser.getboolean('debugging', 'debug')
    SITES = [x.strip() for x in cfgParser.get('availability', 'sites').split(',')]
    REFRESH = cfgParser.getint('availability', 'refresh')

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

    # Python detect linux shutdown and run a command before shutting down
    # credits to code_onkel
    # https://stackoverflow.com/questions/39275948/python-detect-linux-shutdown-and-run-a-command-before-shutting-down
    signal.signal(signal.SIGTERM, onTerminate)

    # create an Apprise instance
    apobj = apprise.Apprise()

    # add Apprise notification settings
    addNotificationService(cfgParser)

    main()
