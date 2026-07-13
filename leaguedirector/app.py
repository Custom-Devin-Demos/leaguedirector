import logging
from leaguedirector.mainwindow import LeagueDirector


if __name__ == '__main__':
    try:
        LeagueDirector()
    except Exception as exception:
        logging.exception(exception)
