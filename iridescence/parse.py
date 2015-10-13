from . import IridescentFormatter
import re
import logging
import time


class LogRecord:
    def __init__(self, level, msg, module, func,
                 created, file, line, traceback=None):
        self.level = level
        self.msg = msg
        self.module = module
        self.func = func
        self.created = created
        self.file = file
        self.line = line
        self.traceback = traceback

    def __repr__(self):
        return ("<LogRecord {} {} [{}:{} - {} - {}:{}] "
                "traceback={}>".format(self.levelname, self.msg, self.module,
                                       self.func, self.asctime, self.file,
                                       self.line, self.traceback is not None))

    @property
    def levelname(self):
        return logging.getLevelName(self.level)

    @property
    def asctime(self):
        return time.strftime(IridescentFormatter.datefmt,
                             time.localtime(self.created))

    def formatted(self, formatter):
        assert isinstance(formatter, IridescentFormatter)
        return formatter.do_format(self.level, self.msg, self.module,
                                   self.func, self.created, self.file,
                                   self.line, self.traceback)


class IridescentParser:
    ansi_color_re = re.compile(r"\033\[1;(\d+)?m")
    line_re = re.compile(r"(.*?) \[([^:]+):(.*?) - "
                         r"(\d+:\d+:\d+) - (.*?):(\d+)]$")
    datefmt = IridescentFormatter.datefmt
    levels = IridescentFormatter.levels

    def decolorise(self, text):
        return self.ansi_color_re.sub("", text)

    def level_from_color(self, color):
        for level, (lcolor, *_) in self.levels.items():
            if lcolor.value == color:
                return level
        return "unknown"

    def level_from_letter(self, letter):
        for level, (_, lletter, *_) in self.levels.items():
            if lletter == letter:
                return level
        return "unknown"

    def extract_traceback(self, log, line):
        decol_line = self.decolorise(line)
        if not decol_line.startswith("Traceback"):
            return line, None
        lines = [decol_line + "\n"]
        nls = ""
        for line in log:
            decol_line = self.decolorise(line)
            if any(True for *_, arrow, _ in self.levels.values()
                   if decol_line.startswith(arrow)  # use_color=True
                   or decol_line[1:].startswith(arrow)):  # use_color=False
                break
            if decol_line.startswith("  File"):
                decol_line += "\n" + self.decolorise(next(log))
            if not decol_line:
                nls += "\n"
            elif decol_line.startswith("Traceback"):
                lines[-1] += nls
                lines.append(decol_line + "\n")
                nls = ""
            else:
                lines.append(nls + decol_line + "\n")
                nls = ""
        if lines[-1] == "\n":
            lines.pop()
        return line, lines

    def remove_arrow(self, line):
        start = max([arrow + " " + name
                     for *_, name, arrow, _ in self.levels.values()
                     if line.startswith(arrow + " " + name)] + [""], key=len)
        return line[len(start):]

    def parse(self, log):
        log = iter(log.splitlines())
        last_record = None
        for line in log:
            if last_record is not None:
                line, last_record.traceback = self.extract_traceback(log, line)
                yield last_record
            decol_line = self.decolorise(line)

            match = self.ansi_color_re.match(line)
            if match:  # use_color=True
                level = self.level_from_color(int(match.group(1)))
            else:  # use_color=False
                level = self.level_from_letter(decol_line[0])
                decol_line = decol_line[1:]

            line = self.remove_arrow(decol_line)
            msg, module, func, created, file, line = self.line_re.match(line).groups()
            created = time.mktime(time.strptime(created, self.datefmt))
            last_record = LogRecord(level, msg.rstrip(" "),
                                    module, func, created, file, line)
        if last_record is not None:
            yield last_record


if __name__ == "__main__":
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument("file")
    argparser.add_argument("--no-color", action="store_true")
    args = argparser.parse_args()

    iriparser = IridescentParser()
    records = iriparser.parse(open(args.file).read())

    iriformatter = IridescentFormatter(use_color=not args.no_color)
    for record in records:
        print(record.formatted(iriformatter))
