import sys
import termcolor as tc

class Log:
    logLevel = 0

    def debug(self, msg, *args):
        if self.logLevel >= 4:
            print(tc.colored("*", "white", attrs=['dark']), msg % args, file=sys.stderr)
    def info(self, msg, *args):
        if self.logLevel >= 3:
            print(tc.colored("*", "cyan"), msg % args, file=sys.stderr)
    def warning(self, msg, *args):
        if self.logLevel >= 2:
            print(tc.colored("*", "yellow", attrs=['bold']), msg % args, file=sys.stderr)
    def error(self, msg, *args):
        if self.logLevel >= 1:
            print(tc.colored("*", "red", attrs=['bold']), msg % args, file=sys.stderr)
    def critical(self, msg, *args):
        if self.logLevel >= 0:
            print(tc.colored("*", "white", "on_red", attrs=['bold']), msg % args, file=sys.stderr)


def loggingSetup(level):
    l = level.lower()
    if l == 'debug':
        Log.logLevel = 4
    elif l == 'info':
        Log.logLevel = 3
    elif l == 'warning':
        Log.logLevel = 2
    elif l == 'error':
        Log.logLevel = 1
    elif l == 'critical':
        Log.logLevel = 0
    else:
        raise RuntimeError("Invalid log level")

log = Log()
