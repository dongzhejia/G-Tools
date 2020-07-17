#!/usr/bin/env python
# coding=utf-8
# Filename: XConfig.py
# :   

import os
import re
import sys
import shutil
if sys.version_info.major<3:
    import configparser as configparser
else:
    import configparser

from . import predefs
# from .wildcard import *

__cfg_filename__ = predefs.CFG_FILENAME
__cfg_dirname__ = predefs.CFG_DIRNAME
__cfg_header__ = """# Configurations for xtool.
# Builtin variables:
#     XCFGDIR: the directory where this file exists
#     XPROJROOT: the project root directory (which contains `.xtool` sub-directory)

"""
__cfg_mainsec__ = "xtool"
__cfg_defaults__ = {
    __cfg_mainsec__: {
        "projroot": "%(XPROJROOT)s",
        # "cachedir": "%(XCFGDIR)s/cache",
        # "settings": "%(XPROJROOT)s/xtool.settings",
    },
}

# convert a string contains wildcards to regex string
_wildcard2regex_p = re.compile(r'(\\\*|\\\?)|(\*{1,})|(\?)|(\\[^*?]|\.)')
def _wildcard2regex_repl(m):
    x = m.group(1)
    if x!=None:
        return x
    x = m.group(2)
    if x!=None:
        return ".*" if len(x)>1 else "[\w-]*"
    x = m.group(3)
    if x!=None:
        return "[\w-]"
    x = m.group(4)
    if x!=None:
        return ("\\"+x[0]) + ("\\\\" if x[1:]=="\\" else x[1:])
    return m.group(0)

def wildcard2regex(wildcard):
    rawpattern = re.sub(_wildcard2regex_p, _wildcard2regex_repl, wildcard)
    return "^" + rawpattern + "$"

def wildcardCompile(wildcard, ignoreCase = True):
    pstr = wildcard2regex(wildcard)
    return re.compile(pstr, re.I) if ignoreCase else re.compile(pstr)

def parseKey(key, defaultSecName="xtool"):
    sectionName = defaultSecName
    seppos = key.rfind(".")
    if seppos>0:
        sectionName = key[:seppos]
    optionName = key[seppos+1:]
    return (sectionName, optionName)

def loadSettings(filepath):
    try:
        with open(filepath, 'r') as stream:
            import yaml
            return yaml.load(stream) or {}
    except:
        pass
    return {}

# Error: Project not initialized
class UnInitedError(Exception):
    def __init__(self):
        self.msg = "fatal: Not a xtool project (or any of the parent directories): .xtool"
    def __str__(self):
        return repr(self.msg)

# class XConfig
class XConfig(object):
    def __init__(self):
        self.config = None
        self.environments = None
        self._projroot = None
        self._cachedir = None
        self._projenv = None
        self._settingFile = None
        self._projSettings = {}

    @staticmethod
    def seekCfgDir(path):
        if path==None:
            return None
        current = os.path.abspath(path)
        while current!=None and current!="":
            if not os.path.exists(current):
                return None
            cfgdir = os.path.join(current, __cfg_dirname__)
            if os.path.isdir(cfgdir):
                return cfgdir
            parent = os.path.dirname(current)
            if parent==current:
                # reaches the root("/")
                break
            current = parent
        return None

    def getProjectRoot(self):
        if self._projroot != None:
            return self._projroot

        self._projroot = self.getValue(__cfg_mainsec__, "projroot")
        return self._projroot

    def getCachedir(self):
        return self._cachedir

    def getProjectSettings(self, *keys):
        value = self._projSettings
        if value and keys:
            try:
                for key in keys:
                    value = value[key]
            except:
                return None
        return value

    def _createNewConfig(self, sections):
        cfg = configparser.SafeConfigParser()
        for secname, values in list(sections.items()):
            cfg.add_section(secname)
            for option, value in list(values.items()):
                cfg.set(secname, option, str(value))
        return cfg

    def _saveConfigToFile(self, cfg, filepath):
        cfgfile = None
        try:
            cfgfile = open(filepath, "w")
            cfgfile.write(__cfg_header__)
            cfg.write(cfgfile)
        finally:
            if cfgfile!=None:
                cfgfile.close()

    def _loadConfigFromFile(self, filepath):
        cfg = configparser.SafeConfigParser()
        cfg.read(filepath)
        return cfg

    def _setupProjectEnvironments(self, cfgdir):
        projenv = {}
        if cfgdir!=None and os.path.isdir(cfgdir):
            projenv["XCFGDIR"] = os.path.abspath(cfgdir)
            self._projroot = self.getValue(__cfg_mainsec__, "projroot")

            cachedir = os.path.join(cfgdir, "cache")
            self._cachedir = cachedir
            self._settingFile = os.path.abspath(os.path.join(cfgdir, "../xtool.settings"))
            
            projenv["XPROJROOT"] = self._projroot

        self._projenv = projenv
        return self._projenv

    def reloadEnvironments(self):
        if self._projenv!=None:
            self.environments = dict(os.environ, **self._projenv)
        else:
            self.environments = dict(os.environ)
        return self.environments

    def getEnvVariable(self, name, defaultValue = None):
        env = self.environments
        if env!=None and name in env:
            return env[name]
        return defaultValue

    def loadConfigs(self, path):
        cfgdir = self.seekCfgDir(path)
        if cfgdir==None:
            raise UnInitedError
        self._setupProjectEnvironments(cfgdir)
        self.reloadEnvironments()
        cfgfilename = os.path.join(cfgdir, __cfg_filename__)
        if not os.path.isfile(cfgfilename):
            self.config = self._createNewConfig(__cfg_defaults__)
            self._saveConfigToFile(self.config, cfgfilename)
        else:
            self.config = self._loadConfigFromFile(cfgfilename)
        # load settings file
        if self._settingFile  and os.path.isfile(self._settingFile):
            self._projSettings = loadSettings(self._settingFile)
        else:
            self._projSettings = {}

    def saveConfigs(self):
        cfgdir = self.getEnvVariable("XCFGDIR")
        if cfgdir==None:
            raise UnInitedError
        cfgfilename = os.path.join(cfgdir, __cfg_filename__)
        self._saveConfigToFile(self.config, cfgfilename)

    def createOrReCreateProject(self, path):
        cfgdir = os.path.join(path, __cfg_dirname__)
        if os.path.exists(cfgdir):
            shutil.rmtree(cfgdir)
        os.mkdir(cfgdir)
        if os.name=="nt":
            os.popen("attrib +h "+cfgdir).close()
        self._setupProjectEnvironments(cfgdir)
        self.reloadEnvironments()
        self.config = self._createNewConfig(__cfg_defaults__)
        self._saveConfigToFile(self.config, os.path.join(cfgdir, __cfg_filename__))

    def setValue(self, section, option, value):
        if self.config==None:
            return False
        cfg = self.config
        if value==None:
            if cfg.has_option(section, option):
                cfg.remove_option(section, option)
        else:
            if not cfg.has_section(section):
                cfg.add_section(section)
            cfg.set(section, option, str(value))
        return True

    def getValue(self, section, option, defaultValue = None):
        if self.config!=None and self.config.has_option(section, option):
            return self.config.get(section, option)
            # return self.config.get(section, option, False, self.environments)
        else:
            return defaultValue

    def getInt(self, section, option, defaultValue = 0):
        if self.config!=None and self.config.has_option(section, option):
            return self.config.getint(section, option)
        else:
            return defaultValue

    def getFloat(self, section, option, defaultValue = 0.0):
        if self.config!=None and self.config.has_option(section, option):
            return self.config.getfloat(section, option)
        else:
            return defaultValue

    def getBoolean(self, section, option, defaultValue = False):
        if self.config!=None and self.config.has_option(section, option):
            return self.config.getboolean(section, option)
        else:
            return defaultValue

    def removeSection(self, section):
        if self.config!=None:
            return self.config.remove_section(section)
        return False

    def hasSection(self, section):
        if self.config!=None:
            return self.config.has_section(section)
        return False

    def hasOption(self, section, option):
        if self.config!=None:
            return self.config.has_option(section, option)
        return False

    def listSections(self):
        if self.config!=None:
            return self.config.sections()
        return []

    def listOptions(self, section):
        if self.config!=None and self.config.has_section(section):
            return self.config.options(section)
        return []

    def listItems(self, section, israw = False):
        cfg = self.config
        if cfg!=None and cfg.has_section(section):
            items = []
            env = self.environments
            for option in cfg.options(section):
                value = cfg.get(section, option, israw, env)
                items.append((option, value))
            return items
            # return cfg.items(section, israw, self.environments)
        return []

    def listValues(self, sectionFilter = None, optionFilter = None, israw = False):
        sectionPattern = None
        optionPattern = None
        if sectionFilter!=None:
            sectionPattern = wildcardCompile(sectionFilter)
        if optionFilter!=None:
            optionPattern = wildcardCompile(optionFilter)
        cfg = self.config
        env = self.environments
        items = []
        for sectionName in cfg.sections():
            if sectionPattern==None or re.match(sectionPattern, sectionName)!=None:
                for option in cfg.options(sectionName):
                    if optionPattern==None or re.match(optionPattern, option)!=None:
                        value = cfg.get(sectionName, option)
                        # value = cfg.get(sectionName, option, israw, env)
                        # items.append("%s.%s = %s" % (sectionName, option, value))
                        items.append((sectionName, option, value))
        return items


# global functions
_xcfg = None
def getXConfig(pwd = ".", ignoreLoadErrors = False):
    from . import logutil
    global _xcfg
    if _xcfg==None:
        _xcfg = XConfig()
    if _xcfg.config==None:
        try:
            _xcfg.loadConfigs(pwd)
            # logutil.applySettings(_xcfg)
        except UnInitedError as e:
            if not ignoreLoadErrors:
                logutil.echo(e.msg)
                exit(-1)
    return _xcfg

# def main():
#     xcfg = XConfig()
#     xcfg.loadConfigs(".")
#     # xcfg.createOrReCreateProject(".")

#     print xcfg.listSections()
#     print xcfg.listOptions("xtool")
#     print xcfg.listItems("xtool", True)
#     print xcfg.getValue("xtool", "hello", "No value")
#     xcfg.setValue("test", "msg", "Hello, xtool! $path=%(path)s")
#     print xcfg.listItems("test")
#     # xcfg.setValue("test", "msg", None)
#     # print xcfg.listItems("test")
#     print xcfg.listValues(sectionFilter="test*", israw=True)
#     print xcfg.removeSection("test")
#     print xcfg.listValues(sectionFilter="test", israw=True)

#     xcfg.saveConfigs()

# if __name__ == '__main__':
#     main()
