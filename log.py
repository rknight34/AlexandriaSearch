"""provides method to amend line to global log file"""

import datetime


def addLog(event, freeText):
    myFile = open(("LogFile"), "a")
    myFile.write(str(datetime.datetime.now())+ "    "
                 + "[" + event + "]" + "    "
                 + freeText + "\n")
    myFile.close()