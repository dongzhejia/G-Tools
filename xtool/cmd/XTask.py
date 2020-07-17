#!/usr/bin/env python
# coding=utf-8
# Filename: XTask.py
# :   

import sys
import os
from multiprocessing import Process, Manager, Lock

from . import predefs, logutil
logger = logutil.getLogger()

class TaskContext(object):
    def __init__(self, logger, xcfg):
        self._logger = logger
        self._xcfg = xcfg
        self._options = None

    def setLogger(self, logger):
        self._logger = logger

    def getLogger(self):
        return self._logger

    def setXConfig(self, xcfg):
        self._xcfg = xcfg

    def getXConfig(self):
        return self._xcfg

    def getEnv(self, name):
        # get environment variable with `name`
        return os.getenv(name)

    # `options`: a dict that contains task options
    def setOptions(self, options):
        self._options = options
    def getOptions(self):
        return self._options
    def getOptionValue(self, name, default=None):
        if self._options!=None and name in self._options:
            return self._options[name]
        return default


class BaseTask(object):
    def __init__(self, name, ctx):
        self.name = name
        self.context = ctx
        self.logger = logutil.getLogger(name)
        self.settings = None
        self.projroot = None
        self.outputdir = None
        self.cachedir = None
        self.taskoutdir = None
        self.multiManager = Manager()
        self._executedTasks = self.multiManager.dict()
        self._extraOutfiles = self.multiManager.list()
        self._shareLock = Lock()

    def setSettings(self, settings):
        self.settings = settings
    def setupDirectories(self, projroot, outputdir, cachedir, taskoutdir):
        self.projroot = projroot
        self.outputdir = outputdir
        self.cachedir = cachedir
        self.taskoutdir = taskoutdir if taskoutdir!=None else outputdir
    def absInputPaths(self, inputs):
        rootdir = self.projroot
        if isinstance(inputs, list):
            return [os.path.join(rootdir, x) for x in inputs]
        else:
            return [os.path.join(rootdir, inputs)]
    def absOutputPaths(self, outputs):
        rootdir = self.taskoutdir
        if isinstance(outputs, list):
            return [os.path.join(rootdir, x) for x in outputs]
        else:
            return [os.path.join(rootdir, outputs)]
    def dependentFiles(self, inputs, taskItem):
        return inputs
    def targetFiles(self, outputs, taskItem):
        return outputs
    def runCommand(self, cmd, options):
        # 工具函数，执行给定的shell命令
        pass

    def runTaskItem(self, taskItem, inputs, outputs):
        result = self.execAction(taskItem, inputs, outputs)
        if type(result)==tuple:
            outfiles = result[1]
            result = result[0]
        else:
            outfiles = outputs
        if result==None:
            result = True
        with self._shareLock:
            itemName = taskItem["fullname"]
            execResult = {
                "name": itemName,
                "status": "success" if result else "failed",
                "outputs": outfiles if result else None,
                # "taskItem": taskItem,
            }
            self._executedTasks[itemName] = execResult
        return result

    def registerExtraOutputFiles(self, outfiles):
        with self._shareLock:
            if isinstance(outfiles, (list, tuple)):
                self._extraOutfiles.extend(outfiles)
            else:
                self._extraOutfiles.append(outfiles)

    def getExtraOutfiles(self):
        result = []
        result.extend(self._extraOutfiles)
        return result

    def runPreTask(self, taskItems):
        return self.preAction(taskItems)

    def runPostTask(self, taskItems):
        with self._shareLock:
            executedTasks = self._executedTasks
            for item in taskItems:
                itemName = item["fullname"]
                if itemName in executedTasks:
                    item["$result"] = executedTasks[itemName]
                else:
                    item["$result"] = {
                        "name": itemName,
                        "status": "skipped",
                    }
        return self.postAction(taskItems)

    def execAction(self, taskItem, inputs, outputs):
        # 具体Action须重载该方法
        return True
    def preAction(self, taskItems):
        return True
    def postAction(self, taskItems):
        return True

# run all tasks
def runTasks(xtask, taskItems, xcfg, execOptions):
    tasktype = xtask.name
    total = len(taskItems)
    breakOnFailure = not execOptions["continue"]
    skipTaskItems = execOptions["skip_items"]
    executed, skipped = 0, 0
    successes, failures = 0, 0

    ok = xtask.runPreTask(taskItems)
    if ok!=None and not ok:
        logger.error("%s: Failed in pre-action" % (tasktype))
        if breakOnFailure:
            return

    idx = 0
    for task in taskItems:
        idx += 1
        # options = task["options"]
        logger.info("%s:%s (%d/%d)" % (tasktype, task["fullname"], idx, total))
        if skipTaskItems:
            skipped = skipped+1
            successes = successes+1
        else:
            ok = xtask.runTaskItem(task, task["abs_input"], task["abs_output"])
            executed = executed+1
            if ok or ok==None:
                successes = successes+1
            else:
                failures = failures+1
                if breakOnFailure:
                    break

    ok = xtask.runPostTask(taskItems)
    if ok!=None and not ok:
        logger.error("%s: Failed in post-action" % (tasktype))
        if breakOnFailure:
            return

    return {
        "total": total,
        "executed": executed,
        "skipped": skipped,
        "successes": successes,
        "failures": failures,
        "taskItems": taskItems,
    }

############################################################
import inspect
import types

__taskRegistries = {}
__taskSequences = {}

def registTask(name, taskInfo):
    stack = inspect.stack()
    caller = stack[1]

    if name in __taskRegistries:
        taskInfo = __taskRegistries[name]
        registrant = taskInfo["registrant"]
        logger.error(('Task named "%s" is already registered.\n' +
                      '  First registered from "%s:%d"\n' +
                      '  Registration from "%s:%d" is ignored.\n')
            % (name, registrant[1], registrant[2], caller[1], caller[2]))
        return False

    taskInfo["registrant"] = caller
    taskInfo["name"] = name
    if ("settings" not in taskInfo) or "settings" is None:
        taskInfo["settings"] = {}
    if ("cmd_name" not in taskInfo):
        taskInfo["cmd_name"] = name
    if ("cmd_help" not in taskInfo):
        taskInfo["cmd_help"] = "<No help message>"
    if ("mode" not in taskInfo):
        taskInfo["mode"] = "direct"

    requiredProperties = [
        ("task_creator", (types.FunctionType, type)),
    ]
    for prop in requiredProperties:
        if (prop[0] not in taskInfo) or (type(taskInfo[prop[0]]) not in prop[1]):
            logger.error(('"%s"(%s) required to regist task "%s". ' +
                'Registration from "%s:%d" failed.\n') %
                (prop[0], prop[1], name, caller[1], caller[2]))
            return False

    __taskRegistries[name] = taskInfo
    return True

def getTaskInfo(name):
    if name not in __taskRegistries:
        return None
    return __taskRegistries[name]

def registeredTasks():
    return list(__taskRegistries.items())

def registTaskSequence(name, seqInfo):
    stack = inspect.stack()
    caller = stack[1]

    if name in __taskSequences:
        seqInfo = __taskSequences[name]
        registrant = seqInfo["registrant"]
        logger.error(('Task sequence named "%s" is already registered.\n' +
                      '  First registered from "%s:%d"\n' +
                      '  Registration from "%s:%d" is ignored.\n')
            % (name, registrant[1], registrant[2], caller[1], caller[2]))
        return False

    subtasks = seqInfo["subtasks"]
    if not hasattr(subtasks, '__iter__'):
        logger.error(('Failed to add task sequence named "%s".\n' +
                      '  "subtasks" is not iterable. It should be a list or a tuple.\n')
            % (name))
        return False

    seqInfo["registrant"] = caller
    seqInfo["name"] = name
    if ("cmd_name" not in seqInfo):
        seqInfo["cmd_name"] = name
    if ("cmd_help" not in seqInfo):
        seqInfo["cmd_help"] = "<No help message>"

    __taskSequences[name] = seqInfo
    return True

def taskSequences():
    return list(__taskSequences.items())

from . import PackupTask

registTask("PackUIImage", {
    # "mode": "direct", # 无缓存
    "mode": "doit", # 有缓存
    "task_creator": PackupTask.PackupTask,
    "settings": {
        "outputdir": "asset/uiiii",
        "index_name": "index.json",
        "index_fmt": "json",
    },
    "cmd_name": "packuiimage",
    "cmd_help": 'UI资源合图任务',
})

registTaskSequence("UITaskSeq", {
    "cmd_name": "ui",
    "cmd_help": '处理UI资源(合并UI碎图)',
    "subtasks": ["PackUIImage"],
})
