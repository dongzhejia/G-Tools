#!/usr/bin/env python
# coding=utf-8
# Filename: XIgnore.py
# :   
# Description: Module that implements the git-like ignore rules.

import os
import sys
import re

class XIgnore(object):
    def __init__(self):
        super(XIgnore, self).__init__()
        self._ignoreRootPath = None

    def setIgnoreRoot(self, ignoreRootPath):
        self._ignoreRootPath = ignoreRootPath

    def isIgnored(self, path, isDirectory=False):
        return False

# zgitignore implementation
import zgitignore
class ZGitIgnore(XIgnore):
    def __init__(self, ignoreObject):
        super(XIgnore, self).__init__()
        self._ignoreObject = ignoreObject

    @staticmethod
    def fromLines(lines):
        ignoreObject = zgitignore.ZgitIgnore(ignore_case = True)
        for line in lines:
            pat = line.strip()
            if not pat or pat[0] == '#' or pat == '/':
                continue
            ignoreObject.add_pattern(pat)
            if pat.endswith('/'):
                ignoreObject.add_pattern(pat + '**')
            elif not re.search(r'\*$', pat):
                ignoreObject.add_pattern(pat + '/**')
        return ZGitIgnore(ignoreObject)

    def isIgnored(self, path, isDirectory=False):
        if self._ignoreObject==None:
            return False

        filePath = path
        if os.path.isabs(filePath):
            filePath = os.path.realpath(filePath)
            if self._ignoreRootPath==None:
                filePath = os.path.relpath(filePath, os.getcwd())
            else:
                filePath = os.path.relpath(filePath, self._ignoreRootPath)

        if sys.platform == 'win32':
            filePath = filePath.decode('gbk')
        # else:
            # filePath = filePath.decode('utf8')

        return self._ignoreObject.is_ignored(filePath, isDirectory)
