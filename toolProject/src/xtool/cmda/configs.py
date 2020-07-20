#!/usr/bin/env python
# coding=utf-8
# Filename: configs.py
# :   

NAME = "dog"
VERSION = "0.1.0"

def get_enginedir(xcfg):
    return xcfg.getValue("dog", "enginedir")

def get_scriptdir(xcfg):
    return xcfg.getValue("dog", "scriptdir")

def get_datasetdir(xcfg):
    return xcfg.getValue("dog", "datasetdir")

def get_storydir(xcfg):
    return xcfg.getValue("dog", "storydir")

def get_skilldir(xcfg):
    return xcfg.getValue("dog", "skilldir")
