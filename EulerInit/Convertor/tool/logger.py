import sys


class Logger(object):
    def __init__(self, filename: str = "out.log", display: bool = True):
        self.terminal = sys.stdout
        self.log = open(filename, "a")
        self.display = display

    def write(self, message):
        if self.display:
            self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass
