import logging
import re
import traceback
import enum
import shutil


def log_record_factory(name, level, fn, lno, msg,
                       args, exc_info, func=None, sinfo=None,
                       old_log_record_factory=logging.getLogRecordFactory(),
                       **kwargs):
    """Allow str.format style for log messages"""
    msg = str(msg)
    if args:
        try:
            msg = msg % args
        except TypeError:
            msg = msg.format(*args)

    return old_log_record_factory(name, level, fn, lno, msg, (), exc_info,
                                  func, sinfo, **kwargs)

logging.setLogRecordFactory(log_record_factory)


class ANSIColors(enum.Enum):
    black, red, green, yellow, blue, magenta, cyan, white = range(30, 38)

    # Shorter aliases
    r, g, b = red, green, blue
    c, m, y = cyan, magenta, yellow


class IridescentFormatter(logging.Formatter):
    def __init__(self, use_color=True, width=None, *args, **kwargs):
        if not kwargs:
            kwargs = {"fmt": "{message} [{name}:{funcName} - {asctime} -"
                             " {filename}:{lineno}]",
                      "datefmt": "%H:%M:%S"}

        super().__init__(*args, **kwargs)

        self.use_color = use_color
        if width is not None:
            self.width = width
        else:
            self.width = shutil.get_terminal_size((0, 0)).columns

        self.levels = {logging.DEBUG: (ANSIColors.b, "D", "", " ->"),
                       logging.INFO: (ANSIColors.g, "I", "", "==>"),
                       logging.WARNING: (ANSIColors.y, "W", "WARNING: ",
                                         "==>"),
                       logging.ERROR: (ANSIColors.r, "E", "ERROR: ", "==>"),
                       logging.CRITICAL: (ANSIColors.r, "C", "CRITICAL: ",
                                          "==>")}

    def colorise(self, s, col, bg=False):
        if not self.use_color:
            return s
        col = col.value if isinstance(col, ANSIColors) else col
        if bg:
            col += 10
        return "\033[1;%dm%s\033[1;m" % (col, s)

    def format_traceback(self, exc):
        yield ""
        if exc.__cause__:
            yield from self.format_traceback(exc.__context__)
            yield ""
            yield self.colorise("The above exception was the direct cause"
                                " of the following exception:", ANSIColors.y)
            yield ""
        if exc.__context__ and not exc.__suppress_context__:
            yield from self.format_traceback(exc.__context__)
            yield ""
            yield self.colorise("During handling of the above exception,"
                                " another exception occurred:", ANSIColors.y)
            yield ""

        yield (self.colorise("Traceback", ANSIColors.r)
               + self.colorise(" (most recent call last):", ANSIColors.white))
        for file, line, func, text in traceback.extract_tb(exc.__traceback__):
            line = ""
            line += self.colorise("  File ", ANSIColors.white)
            line += self.colorise("\"" + file + "\"", ANSIColors.black)
            line += self.colorise(", line ", ANSIColors.white)
            line += self.colorise(line, ANSIColors.black)
            if func is not None:
                line += self.colorise(", in ", ANSIColors.white)
                line += self.colorise(func, ANSIColors.y)
            yield line
            yield "    " + text

        yield (self.colorise(exc.__class__.__name__
                             + (": " if exc.args else ""), ANSIColors.r)
               + self.colorise(" ".join(map(str, exc.args)), ANSIColors.white))
        yield ""

    def format(self, record):
        color, letter, name, arrow = self.levels[record.levelno]

        time = self.formatTime(record, self.datefmt)
        msg = self._fmt.format(message=str(record.msg),
                               asctime=time,
                               **record.__dict__)

        start = arrow + " " + name
        padding = " " * max(0, self.width - len(start) - len(msg)
                            - (not self.use_color))
        if padding:
            msg = self._fmt.format(message=str(record.msg + padding),
                                   asctime=time,
                                   **record.__dict__)

        text = (self.colorise(start, color)
                + self.colorise(msg, ANSIColors.white))

        if record.exc_info is not None:
            text += "\n".join(self.format_traceback(record.exc_info[1]))

        if not self.use_color:
            text = letter + text
        return text


def quick_setup(name=None, level=logging.DEBUG, **kwargs):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    log_formatter = IridescentFormatter(**kwargs)

    stream_hndlr = logging.StreamHandler()
    stream_hndlr.setFormatter(log_formatter)

    logger.addHandler(stream_hndlr)
    return logger
