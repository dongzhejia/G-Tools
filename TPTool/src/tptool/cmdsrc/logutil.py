#!/usr/bin/env python
# coding=utf-8
# Filename: logutil.py
# :   


import os, sys
import ctypes
import logging
import re

################################################################################
# Ref: http://plumberjack.blogspot.ca/2010/12/colorizing-logging-output-in-terminals.html
class ColorizingStreamHandler(logging.StreamHandler):

    @property
    def is_tty(self):
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if not self.is_tty:
                stream.write(self.uncolorize(message))
            else:
                self.output_colorized(message)
            stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    ansi_esc = re.compile(r'\x1b\[((\d+)(;(\d+))*)m')

    def uncolorize(self, message):
        return self.ansi_esc.sub("", message)

    if os.name != 'nt':
        def output_colorized(self, message):
            self.stream.write(message)
    else:
        nt_color_map = {
            0: 0x00,    # black
            1: 0x04,    # red
            2: 0x02,    # green
            3: 0x06,    # yellow
            4: 0x01,    # blue
            5: 0x05,    # magenta
            6: 0x03,    # cyan
            7: 0x07,    # white
        }

        def output_colorized(self, message):
            parts = self.ansi_esc.split(message)
            write = self.stream.write
            h = None
            fd = getattr(self.stream, 'fileno', None)
            if fd is not None:
                fd = fd()
                if fd in (1, 2): # stdout or stderr
                    h = ctypes.windll.kernel32.GetStdHandle(-10 - fd)
            while parts:
                text = parts.pop(0)
                if text:
                    write(text)
                if len(parts) > 4:
                    params = parts[0]
                    parts = parts[4:]
                    if h is not None:
                        params = [int(p) for p in params.split(';')]
                        color = 0
                        for p in params:
                            if 40 <= p <= 47:
                                color |= self.nt_color_map[p - 40] << 4
                            elif 30 <= p <= 37:
                                color |= self.nt_color_map[p - 30]
                            elif p == 1:
                                color |= 0x08 # foreground intensity on
                            elif p == 0: # reset to default color
                                color = 0x07
                            else:
                                pass # error condition ignored
                        ctypes.windll.kernel32.SetConsoleTextAttribute(h, color)

__color_map = {
    'black': 0,
    'red': 1,
    'green': 2,
    'yellow': 3,
    'blue': 4,
    'magenta': 5,
    'cyan': 6,
    'white': 7,
}

def colorCode(fg=None, bg=None, bold=None):
    params = []
    if bg in __color_map:
        params.append(str(__color_map[bg] + 40))
    if fg in __color_map:
        params.append(str(__color_map[fg] + 30))
    if bold:
        params.append('1')
    if params:
        return '\x1b['+';'.join(params)+'m'
    return '\x1b[0m'

class ExtendedFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        # can't do super(...) here because Formatter is an old school class
        logging.Formatter.__init__(self, *args, **kwargs)

        msgpattern = re.compile(r"%\((msgtitle|msgbody)\)s")
        self._should_split_message = msgpattern.search(self._fmt)!=None

        colorpattern = re.compile(r"%\((levelcolor)\)s")
        if colorpattern.search(self._fmt)!=None:
            self._level_colors = self.DEFAULT_LEVEL_COLORS
        else:
            self._level_colors = None

    DEFAULT_LEVEL_COLORS = {
        logging.DEBUG: colorCode('magenta', None, False),
        logging.INFO: colorCode(None, None, False),
        logging.WARNING: colorCode('yellow', None, False),
        logging.ERROR: colorCode('red', None, False),
        logging.CRITICAL: colorCode('white', 'red', True),
    }

    @staticmethod
    def hasExtendedVariables(fmt):
        pattern = re.compile(r"%\((levelcolor|resetcolor|msgtitle|msgbody)\)s")
        return fmt and pattern.search(fmt)!=None

    def setLevelColors(self, colors):
        self._level_colors = colors

    def format(self, record):
        if self._level_colors:
            record.levelcolor = self._level_colors.get(record.levelno, '\x1b[0m')
            record.resetcolor = '\x1b[0m'
        else:
            record.levelcolor = ''
            record.resetcolor = ''
        if self._should_split_message:
            message = record.getMessage()
            parts = message.split('\n', 1)
            record.msgtitle = parts[0]
            record.msgbody = '\n'+parts[1] if len(parts)>=2 else ""
        return logging.Formatter.format(self, record)

################################################################################

from . import predefs
__LOG_ROOT__ = predefs.NAME

# console = logging.StreamHandler()
console = ColorizingStreamHandler()
console.setLevel(logging.DEBUG)

logger = logging.getLogger(__LOG_ROOT__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console)

def getLogger(name = None):
    finalName = __LOG_ROOT__
    if name!=None:
        finalName = finalName + "." + name
    return logging.getLogger(finalName)

def setFormats(fmt=None, datefmt=None, levelcolors=None):
    if ExtendedFormatter.hasExtendedVariables(fmt):
        formatter = ExtendedFormatter(fmt=fmt, datefmt=datefmt)
        if levelcolors != None:
            if isinstance(levelcolors, dict):
                formatter.setLevelColors(levelcolors)
            else:
                formatter.setLevelColors(None)
    else:
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    console.setFormatter(formatter)

def applySettings(xcfg):
    logfmt = xcfg.getValue("tptool.logger", "format")
    if logfmt!=None:
        levelcolors = None
        logcolors = xcfg.getValue("tptool.logger", "levelcolors")
        if logcolors:
            levelcolors = {}
            pattern = re.compile(r'''(?P<level>\w+)\s*\:\s*\(\s*(?:(?P<fg>\w*)(?:\s*,\s*(?P<bg>\w*)(?:\s*,\s*(?P<bold>\w*))?)?)?\s*\)''')
            levelnames = {
                "debug": logging.DEBUG,
                "info": logging.INFO,
                "warning": logging.WARNING,
                "error": logging.ERROR,
                "critical": logging.CRITICAL,
            }
            mr = pattern.search(logcolors)
            while mr:
                level = mr.group("level").lower()
                if level in levelnames:
                    fg = mr.group("fg").lower() if mr.group("fg") else None
                    bg = mr.group("bg").lower() if mr.group("bg") else None
                    bold = mr.group("bold").lower() if mr.group("bold") else None
                    levelcolors[levelnames[level]] = colorCode(
                        fg = fg,
                        bg = bg,
                        bold = bold in ("true", "yes", "1", "bold"),
                    )
                mr = pattern.search(logcolors, mr.end())
        setFormats(fmt=logfmt, levelcolors=levelcolors)

# def echo(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
def echo(*objects, **options):
    sep = options.sep if ("sep" in options) else ' '
    end = options.end if ("end" in options) else '\n'
    file = options.file if ("file" in options) else sys.stdout
    flush = options.flush if ("flush" in options) else False
    print(*objects, sep=sep, end=end, file=file)
    if flush:
        file.flush()

#### Set the default log format
setFormats(fmt='[%(name)s %(levelname)s] %(message)s')
# setFormats(
#     fmt = '%(levelcolor)s[%(name)s %(levelname)s] %(message)s%(resetcolor)s',
#     levelcolors = ExtendedFormatter.DEFAULT_LEVEL_COLORS,
# )
# setFormats(
#     fmt='%(levelcolor)s[%(name)s %(levelname)s] %(msgtitle)s%(resetcolor)s%(msgbody)s',
#     levelcolors = ExtendedFormatter.DEFAULT_LEVEL_COLORS,
# )
