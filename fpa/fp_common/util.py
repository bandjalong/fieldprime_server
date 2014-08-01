# util.py
# Michael Kirk 2014
#
# Handy functions.
#

import time, sys

def isInt(x):
    try:
        int(x)
        return True
    except ValueError:
        return False

def isNumeric(x):
    try:
        float(x)
        return True
    except ValueError:
        return False

def epoch2dateTime(timestamp):
# Return readable date/time string from timestamp (assumed to be in milliseconds).
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp/1000))

def formatJapDate(jdate):
    year = jdate / 10000
    month = (jdate % 10000) / 100
    day = jdate % 100
    return '{0}/{1}/{2}'.format(day, month, year)


###  Logging: ##################################################################
# We want a logging system that can be turned on or off by use of a flag file:
# 'dolog' in the app.config[FP_FLAG_DIR] folder.
#

def flog(msg) :
# Logging function called externally, initLogging should be called first.
# This default version does nothing, but may be overwritten.
# Note that initLogging() below changes this function. Hence you should
# not import this function by name, or you will just get a copy of this
# default version. You must instead import util, and call util.flog().
    pass

def initLogging(app, justPrint=False):
#----------------------------------------------------------------------------
# Set up logging, which is then done with the flog() function.
# By default flog() does nothing. This function can change that.
# If justPrint is true, then flog will just print its argument.
# Otherwise - if logging is flagged by the presence of file
# app.config['FP_FLAG_DIR'] + "/dolog" - it will append its argument
# to the file app.config['FPLOG_FILE']. We do this check once
# in this init function rather than with every call in the hope that
# it is less cost at each log call.
# MFK perhaps shouldn't write to FPLOG_FILE since this used by
# fpLog below, which is used for logging connections, and is always on.
#
    global flog
    import os.path
    if os.path.isfile(app.config['FP_FLAG_DIR'] + "/dolog"):
        if justPrint:
            flog = lambda x:sys.stdout.write('flog: ' + str(x)+'\n')
            return

        # Lookup the logging file name, create a function to log to it, and
        # set the flog module global func to that function. So hopefully
        # the module namespace will not end up with either logfilename or
        # flogServer in it, but the function will work nonetheless.
        logfilename = app.config['FPLOG_FILE']
        def flogServer(msg):
            print 'file flog'
            try:     # Don't crash out if logging not working
                f = open(logfilename, 'a')
                print >>f, 'flog@{0}\t{1}'.format(time.strftime("%Y-%m-%d %H:%M:%S"), msg)
                f.close
            except Exception, e:
                pass
        flog = flogServer


def fpLog(app, msg):
#-------------------------------------------------------------------------------------------------
# Write to fplog
# Could put switch here to turn logging on/off, or set level.
# Maybe should record IP address if we have it.
# app is expected to be the wsgi app, and it should have a config
# variable FPLOG_FILE specifying the full path to the file to log to.
# The msg is appended to that file.
#
    try:     # Don't crash out if logging not working
        f = open(app.config['FPLOG_FILE'], 'a')
        print >>f, '{0}\t{1}'.format(time.strftime("%Y-%m-%d %H:%M:%S"), msg)
        f.close
    except Exception, e:
        pass

### End Logging ################################################################
################################################################################

