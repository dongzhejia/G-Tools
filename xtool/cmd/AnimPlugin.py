#!/usr/bin/env python
# coding=utf-8
# Filename: AnimPlugin.py
# :   
from . import MovieClipTask
from . import PackupTask
from . import SpineTask
from . import AnimMainfestTask

XTool.registTask("PackAnimImage", {
    "mode": "doit",
    "task_creator": PackupTask.PackupTask,
    "settings": {
        "outputdir": "asset/anim",
        "index_name": "index.json",
    },
    "cmd_name": "packanimimage",
    # "cmd_disabled": True,
    "cmd_help": '动画图片资源合图任务',
    "cmd_options": [
        (("--skip-index",), {"is_flag":True, "help":'是否跳过生成index文件的步骤'}),
    ],
})

XTool.registTask("ExportSpine", {
    "mode": "doit",
    "settings": {
    },
    "task_creator": SpineTask.SpineTask,
    "cmd_name": "sp",
    "cmd_help": '导出Spine动画',
    # "cmd_disabled": True,
    "cmd_options": [
    ],
})

XTool.registTask("AnimMainfestTask", {
    "task_creator": AnimMainfestTask.AnimMainfestTask,
    "settings": {
    },
    "cmd_name": "animmainfest",
    # "cmd_disabled": True,
    "cmd_help": '动画概要信息任务',
    "cmd_options": [
    ],
})

################################################################################

XTool.registTaskSequence("MCTaskSeq", {
    "cmd_name": "flash",
    "cmd_help": '处理MovieClip资源(合并动画碎图、生成flash动画文件)',
    "subtasks": ["PackAnimImage", "ExportMCLib"],
})

XTool.registTaskSequence("SpineTaskSeq", {
     "cmd_name": "spine",
     "cmd_help": '处理spine动画资源(合并动画碎图、生成spine动画文件)',
     "subtasks": ["PackAnimImage", "ExportSpine"],
})

XTool.registTaskSequence("AnimTaskSeq", {
     "cmd_name": "anim",
     "cmd_help": '处理动画资源(合并动画碎图、生成flash动画和spine动画文件)',
     "subtasks": ["PackAnimImage", "ExportSpine", "AnimMainfestTask"],
})
