import os
import time
import logging.config
from ConfigParser import SafeConfigParser
from lib.internet import Internet
from lib.newold import NewOld
from ago import human
from datetime import datetime,timedelta

def main():
    available = NewOld()
    available.OnChange = OnNetChanged

    try:
        while True:
            available.Value = Internet().Reachable(URL)
            time.sleep(REFRESH)

    except KeyboardInterrupt:
        log.warn("Application interrupted")

    except Exception as e:
        log.error(e, exc_info=True)

def OnNetChanged(available):
    global dt_down

    if available:
        dt_up = datetime.now()
        log.debug("Internet available")

        diff = dt_up - dt_down

        if diff.days <= 0:
            if diff.total_seconds() > 60:
                percision = 2
            else:
                percision = 1
            log.info("Internet resumed on %s, it was down since %s for %s", dt_up.strftime("%I:%M:%S%p"), dt_down.strftime("%I:%M:%S%p"),
                     human(diff, percision, past_tense='{0}'))
        else:
            log.info("Internet resumed on %s, it was down since %s for %s", dt_up.strftime("%d/%m/%y %I:%M:%S%p"), dt_down.strftime("%d/%m/%y %I:%M:%S%p"),
                     human(diff, 3, past_tense='{0}'))

    else:
        dt_down = datetime.now()
        log.info("Internet not available")

def terminate():
    log.info("Application terminated")

if __name__ == "__main__":
    currentPath = os.path.dirname(os.path.abspath(__file__))

    # refer https://pymotw.com/2/ConfigParser/
    cfgParser = SafeConfigParser()
    cfgParser.read('%s/settings.conf' % currentPath)
    DEBUG = cfgParser.getboolean('debugging', 'debug')
    URL = [x.strip() for x in cfgParser.get('availability', 'url').split(',')]
    REFRESH = cfgParser.getint('availability', 'refresh')

    # region logging
    # initialize logging
    logFilename = "%s/%s.log" % (currentPath, os.path.splitext(os.path.basename(__file__))[0])
    logging.config.fileConfig("%s/logging.ini" % currentPath)
    log = logging.getLogger()
    fileHandler = logging.handlers.TimedRotatingFileHandler(logFilename,'D',7,1)
    logLevel = logging.DEBUG if DEBUG else logging.INFO
    log.handlers[0].level = logLevel
    fileHandler.setLevel(logLevel)
    fileHandler.setFormatter(log.handlers[0].formatter)
    log.addHandler(fileHandler)

    # starting service
    log.info("Starting Internet Uptime Monitor%s" % (' (DEBUG mode)' if DEBUG else ''))
    # endregion

    main()
    terminate()