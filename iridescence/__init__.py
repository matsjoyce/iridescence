import logging
import re
import traceback
import enum
import shutil
import time
import inspect
import pathlib
import textwrap
import threading

try:
    import __main__
    main_fname = pathlib.Path(inspect.getabsfile(__main__)).resolve().parent
except:
    main_fname = None


def log_record_factory(*args, factory=logging.getLogRecordFactory(), **kwargs):
    """Allow str.format style for log messages"""
    msg, format_args = args[4:6]
    msg = str(msg)
    if format_args:
        try:
            msg = msg % format_args
        except TypeError:
            try:
                msg = msg.format(*format_args)
            except:
                pass
        except:
            pass

    return factory(*(args[:4] + (msg, ()) + args[6:]), **kwargs)

logging.setLogRecordFactory(log_record_factory)


class ANSIColors(enum.Enum):
    black, red, green, yellow, blue, magenta, cyan, white = range(30, 38)

    # Shorter aliases
    r, g, b = red, green, blue
    c, m, y = cyan, magenta, yellow


class IridescentFormatter(logging.Formatter):
    # Color, single letter for non-color mode, level indicator, arrow, color message
    levels = {logging.DEBUG: (ANSIColors.b, "D", "", " ->", False),
              logging.INFO: (ANSIColors.g, "I", "", "==>", False),
              logging.WARNING: (ANSIColors.y, "W", "WARNING: ", "==>", False),
              logging.ERROR: (ANSIColors.r, "E", "ERROR: ", "==>", False),
              logging.CRITICAL: (ANSIColors.r, "C", "CRITICAL: ", "==>", True)}

    fmt = "[{name}:{funcName} - {asctime}:{thread_name} - {filename}:{lineno}]"
    datefmt = "%H:%M:%S"

    traceback_top_line = (re.compile(r"(Traceback)"
                                     r"( \(most recent call last\):)$"),
                          (ANSIColors.r, ANSIColors.white))

    traceback_file_line = (re.compile(r"(  File )(\".*?\")(, line )"
                                      r"(\d+)(, in )(.*)(\n.*)$"),
                           (ANSIColors.white, ANSIColors.black,
                            ANSIColors.white, ANSIColors.black,
                            ANSIColors.white, ANSIColors.y, None))

    traceback_name_line = (re.compile(r"([.\w]+:?)(.*)$"),
                           (ANSIColors.r, ANSIColors.white))

    traceback_cause_line = (re.compile("(\nThe above exception.*:\n|"
                                       "\nDuring handling of.*:\n)"),
                            (ANSIColors.y,))

    def __init__(self, use_color=True, width=None, *args, **kwargs):
        if not kwargs:
            kwargs = {"fmt": self.fmt, "datefmt": self.datefmt}

        super().__init__(*args, **kwargs)

        self.use_color = use_color
        if width is not None:
            self.width = width
        else:
            self.width = shutil.get_terminal_size((80, 80)).columns

    def colorise(self, text, col, background=False):
        if not self.use_color or col is None:
            return text
        col = col.value if isinstance(col, ANSIColors) else col
        if background:
            col += 10
        return "\033[1;{}m{}\033[1;m".format(col, text)

    def format_exc_text(self, exc_text):
        if not self.use_color:
            yield from exc_text
            return
        for line in exc_text:
            for regex, colors in [self.traceback_top_line,
                                  self.traceback_file_line,
                                  self.traceback_name_line,
                                  self.traceback_cause_line]:
                match = regex.match(line)
                if match:
                    yield "".join(map(self.colorise,
                                      match.groups(), colors)) + "\n"
                    break
            else:
                yield line

    def format(self, record):
        exc = record.exc_info and traceback.format_exception(*record.exc_info)
        return self.do_format(record.levelno, str(record.msg),
                              record.name, record.funcName,
                              record.created, record.pathname,
                              record.lineno, exc)

    def do_format(self, level, msg, module,
                  func, created, file, line, exc_text):
        if level not in self.levels:
            for i in self.levels:
                if i >= level:
                    level = i
                    break

        color, letter, name, arrow, color_msg = self.levels[level]

        path = pathlib.Path(file)
        file = path.name
        if main_fname is not None:
            try:
                file = str(path.resolve().relative_to(main_fname))
            except ValueError:
                pass

        created = time.strftime(self.datefmt, time.localtime(created))
        thread = threading.current_thread()
        fmsg = self._fmt.format(asctime=created,
                                level=level, name=module,
                                funcName=func, created=created,
                                filename=file, lineno=line,
                                thread_name=thread.name,
                                thread_id=thread.ident)

        arrow = " ".join([arrow, name])
        if not self.use_color:
            arrow = letter + arrow
        tw = textwrap.TextWrapper(initial_indent=" " * len(arrow), subsequent_indent=" " * len(arrow), width=self.width)
        wrapped_msg = []
        for part in msg.splitlines():
            wrapped_msg.extend(tw.wrap(part))
            tw.initial_indent = tw.subsequent_indent

        if len(wrapped_msg[-1]) + len(fmsg) > self.width:
            wrapped_msg.append(" " * (self.width - len(fmsg)) + fmsg)
        else:
            wrapped_msg[-1] += " " * (self.width - len(fmsg) - len(wrapped_msg[-1])) + fmsg

        fmsg = "\n".join(wrapped_msg)[len(arrow):]

        fmsg = (self.colorise(arrow, color)
                + self.colorise(fmsg,
                                color if color_msg else ANSIColors.white))

        if exc_text is not None:
            fmsg += "\n" + "".join(self.format_exc_text(exc_text))
        return fmsg


def quick_setup(name=None, level=logging.DEBUG, **kwargs):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    log_formatter = IridescentFormatter(**kwargs)

    stream_hndlr = logging.StreamHandler()
    stream_hndlr.setFormatter(log_formatter)

    logger.handlers = [stream_hndlr]
    return logger
