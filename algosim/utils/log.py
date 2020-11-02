import sys
import logbook
from logbook import Logger, StreamHandler


def logger(logger_name, file=None):
    logbook.set_datetime_format("local")
    StreamHandler(sys.stdout).push_application()
    if file is not None:
        FileHandler(os.path.join(file, 'log.log'), bubble=False).push_application()
    log = Logger(logger_name)
    return log