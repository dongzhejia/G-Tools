#!/usr/bin/env python
# coding=utf-8
# Filename: common.py
# :   

import sys, os.path
import click

from . import predefs, logutil, ToolConfig
logger = logutil.getLogger()

def ensure_target(xcfg, arguments):
    target = arguments["target"]
    if not target:
        target = xcfg.getValue("gtool", "target", predefs.DEFAULT_TARGET)
        arguments["target"] = target
    return target

def ensure_outputdir(xcfg, arguments):
    outputdir = arguments["outputdir"]
    if not outputdir:
        outputdir = xcfg.getValue("gtool", "outputdir")
        if not outputdir:
            # logger.error("Output directory is not specified.")
            sys.exit(-1)
        if not os.path.isabs(outputdir):
            outputdir = os.path.join(xcfg.getProjectRoot(), outputdir)
        arguments["outputdir"] = outputdir
    return outputdir

def ensure_cachedir(xcfg, arguments):
    cachedir = arguments["cachedir"]
    if not cachedir:
        cachedir = xcfg.getCachedir() # xcfg.getValue("gtool", "cachedir")
        if not cachedir:
            cachedir = os.path.join(xcfg.getProjectRoot(), predefs.CFG_DIRNAME, "cache")
        arguments["cachedir"] = cachedir
    return cachedir

def ensure_ignorefile(xcfg, arguments):
    ignorefile = arguments["ignore_file"]
    if not ignorefile:
        ignorefile = xcfg.getValue("gtool", "ignorefile")
    if ignorefile:
        if not os.path.isabs(ignorefile):
            ignorefile = os.path.join(xcfg.getProjectRoot(), ignorefile)
        arguments["ignore_file"] = ignorefile
    return ignorefile
