#!/usr/bin/env python
# coding=utf-8
# Filename: AnimMainfestTask.py
# :   

import os
import shutil
import types
import json
from xtool.core import XConfig, XTaskCollector
from multiprocessing import Process, Manager, Lock
import yaml
from Cheetah.Template import Template

class AnimMainfestTask(XTool.BaseTask):
    def __init__(self, name, ctx):
        super(AnimMainfestTask, self).__init__(name, ctx)
        self.lock = Lock()

    def execAction(self, taskItem, inputs, outputs):
        return True, []
