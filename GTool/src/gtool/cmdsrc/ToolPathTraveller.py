#!/usr/bin/env python
# coding=utf-8
# Filename: ToolPathTraveller.py
# :   

import sys
import os
import os.path
import re

from . import predefs, logutil
logger = logutil.getLogger()

# traverse orders
TOPDOWN = "topdown"
BOTTOMUP = "bottomup"
UNSPECIFIC = None

ACT_VISITFILE = 0
ACT_ENTERDIR = 1
ACT_LEAVEDIR = 2

DEFAULT_EXCLUDING_DIRS = r'^(\..*)$'

class ToolPathTraveller(object):
    def __init__(self):
        super(ToolPathTraveller, self).__init__()
        self.userIgnoreRule = None
        self._filenamePattern = None
        self._excludedDirPattern = None

    def setFilenameFilter(self, filterPattern):
        self._filenamePattern = filterPattern

    def getFilenameFilter(self):
        return self._filenamePattern

    def setExcludedDirPattern(self, pattern):
        self._excludedDirPattern = pattern

    def getExcludedDirPattern(self):
        return self._excludedDirPattern

    def _shouldSkip(self, fullPath, shortName, isdir):
        if isdir:
            if self._excludedDirPattern!=None and \
                self._excludedDirPattern.match(shortName)!=None:
                return True
        else:
            if self._filenamePattern!=None and \
                self._filenamePattern.match(shortName)==None:
                return True
        if self.userIgnoreRule!=None:
            return self.userIgnoreRule.isIgnored(fullPath, isdir)
        return False

    def _walk(self, path, depth):
        items = os.listdir(path)
        splited = os.path.split(path)
        yield (path, splited[0], splited[1]), ACT_ENTERDIR
        for name in items:
            joinedPath = os.path.join(path, name)
            isdir = os.path.isdir(joinedPath)
            if not self._shouldSkip(joinedPath, name, isdir):
                # joinedPath, yield path, name, isdir
                if isdir:
                    for names, act in self._walk(joinedPath, depth+1):
                        yield names, act
                else:
                    yield (joinedPath, path, name), ACT_VISITFILE
        yield (path, splited[0], splited[1]), ACT_LEAVEDIR

    def _walkTopdown(self, path, depth):
        items = os.listdir(path)
        splited = os.path.split(path)
        yield (path, splited[0], splited[1]), ACT_ENTERDIR
        idx = 0
        for name in items:
            joinedPath = os.path.join(path, name)
            isdir = os.path.isdir(joinedPath)
            if self._shouldSkip(joinedPath, name, isdir):
                items[idx] = None
            elif not isdir:
                items[idx] = None
                yield (joinedPath, path, name), ACT_VISITFILE
            else:
                items[idx] = joinedPath
            idx = idx+1
        for dirpath in items:
            if dirpath!=None:
                for names, act in self._walkTopdown(dirpath, depth+1):
                    yield names, act
        yield (path, splited[0], splited[1]), ACT_LEAVEDIR

    def _walkBottomup(self, path, depth):
        items = os.listdir(path)
        splited = os.path.split(path)
        yield (path, splited[0], splited[1]), ACT_ENTERDIR
        idx = 0
        for name in items:
            joinedPath = os.path.join(path, name)
            isdir = os.path.isdir(joinedPath)
            if self._shouldSkip(joinedPath, name, isdir):
                items[idx] = None
            elif isdir:
                items[idx] = None
                if joinedPath!=None:
                    for names, act in self._walkBottomup(joinedPath, depth+1):
                        yield names, act
            else:
                items[idx] = (joinedPath, path, name)
            idx = idx+1
        for item in items:
            if item!=None:
                yield (item[0], item[1], item[2]), ACT_VISITFILE
        yield (path, splited[0], splited[1]), ACT_LEAVEDIR

    def walk(self, path, order=UNSPECIFIC):
        if order==TOPDOWN:
            return self._walkTopdown(path, 1)
        elif order==BOTTOMUP:
            return self._walkBottomup(path, 1)
        elif order==UNSPECIFIC:
            return self._walk(path, 1)
