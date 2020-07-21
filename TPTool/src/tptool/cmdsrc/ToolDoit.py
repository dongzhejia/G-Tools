#!/usr/bin/env python
# coding=utf-8
# Filename: ToolDoit.py
# :   

import os
import re
import threading

from . import logutil
logger = logutil.getLogger()

from doit.cmd_base import ModuleTaskLoader
from doit.doit_cmd import DoitMain
from doit.tools import config_changed
from doit.reporter import ConsoleReporter

class MyReporter(ConsoleReporter):
    def __init__(self, statistics, *argv, **objects):
        super(MyReporter, self).__init__(*argv, **objects)
        self._taskNamePattern = re.compile(r'^[a-zA-Z0-9-_]+:.*$')
        self._statistics = statistics if (type(statistics) is dict) else {}
        if ("executed" not in self._statistics):
            self._statistics["executed"] = 0
        if ("uptodates" not in self._statistics):
            self._statistics["uptodates"] = 0
        if ("ignored" not in self._statistics):
            self._statistics["ignored"] = 0
        if ("total" not in self._statistics):
            self.total = "-"
        else:
            self.total = self._statistics["total"]
        self.processed = 0

    def execute_task(self, task):
        if task.name[0] != '_' and self._taskNamePattern.match(task.name)!=None:
            self.processed += 1
            # self.write('[...] %s\n' % task.title())
            logger.info('[...] %s (%d/%s)' % (task.title(), self.processed, self.total))
            self._statistics["executed"] = self._statistics["executed"]+1

    def skip_uptodate(self, task):
        if task.name[0] != '_' and self._taskNamePattern.match(task.name)!=None:
            self.processed += 1
            # self.write('[---] %s\n' % task.title())
            logger.info('[---] %s (%d/%s)' % (task.title(), self.processed, self.total))
            self._statistics["uptodates"] = self._statistics["uptodates"]+1

    def skip_ignore(self, task):
        if task.name[0] != '_' and self._taskNamePattern.match(task.name)!=None:
            self.processed += 1
            # self.write('[!!!] %s\n' % task.title())
            logger.info('[!!!] %s (%d/%s)' % (task.title(), self.processed, self.total))
            self._statistics["ignored"] = self._statistics["ignored"]+1

    def add_failure(self, task, exception):
        super(MyReporter, self).add_failure(task, exception)
        if task.name[0] != '_' and self._taskNamePattern.match(task.name)!=None:
            self._statistics["failures"] = self._statistics["failures"]+1

    def add_success(self, task):
        super(MyReporter, self).add_success(task)
        if task.name[0] != '_' and self._taskNamePattern.match(task.name)!=None:
            self._statistics["successes"] = self._statistics["successes"]+1

def makeReporter(clazz, arg1, skipTaskItems):
    class subclazz(clazz):
        def __init__(self, *argv, **objects):
            super(subclazz, self).__init__(arg1, *argv, **objects)
            if skipTaskItems:
                self.execute_task = self.skip_uptodate
    return subclazz

# run tasks
def runTasks(tptask, taskItems, xcfg, execOptions):
    taskcachedir = execOptions["taskcache"]
    if not os.path.isdir(taskcachedir):
        os.makedirs(taskcachedir)

    total = len(taskItems)

    # continueOnFailure = execOptions["continue"]
    skipTaskItems = execOptions["skip_items"]
    statistics = {
        "total": total,
        "successes": 0,
        "failures": 0,
        "executed": 0,
        "uptodates": 0,
        "ignored": 0,
    }

    DOIT_CONFIG = {
        'reporter': makeReporter(MyReporter, statistics, skipTaskItems),
        'verbosity': execOptions["verbosity"],
        'continue': execOptions["continue"],
        'dep_file': os.path.join(taskcachedir, 'doit'),
        'check_file_uptodate': 'timestamp', # XXX 'md5' won't work when input path is a directory.
    }

    taskName = tptask.name

    def runtask(tptask, taskItem, inputs, outputs):
        if skipTaskItems:
            return True
        return tptask.runTaskItem(taskItem, inputs, outputs)

    def taskGenerator():
        for item in taskItems:
            name = item["fullname"]

            options = item["options"]
            inputs = [x.encode().decode('utf-8') for x in item["abs_input"]]
            outputs = item["abs_output"]
            yield {
                "name": name,
                "actions": [(runtask, (tptask, item, inputs, outputs))],
                "file_dep": tptask.dependentFiles(inputs, item),
                "targets": tptask.targetFiles(outputs, item),
                'uptodate': [config_changed(options)],
                # 'setup': [setupTaskName],
            }

    dodo = {
        "DOIT_CONFIG": DOIT_CONFIG,
        # "task_"+setupTaskName: setupTaskGenerator,
        "task_"+taskName: taskGenerator,
    }

    # generate argv
    dodoargv = [
        "-n", str(execOptions["process"]),
        "-P", execOptions["parallel_type"],
    ]

    breakOnFailure = not execOptions["continue"]
    ok = tptask.runPreTask(taskItems)
    if (ok!=None and not ok) and breakOnFailure:
        return
    DoitMain(ModuleTaskLoader(dodo)).run(dodoargv)
    tptask.runPostTask(taskItems)

    skipped = statistics["uptodates"] + statistics["ignored"]
    return {
        "total": total,
        "executed": statistics["executed"],
        "skipped": skipped,
        "successes": skipped + statistics["successes"],
        "failures": statistics["failures"],
        "taskItems": taskItems,
    }
