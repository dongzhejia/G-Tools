#!/usr/bin/env python
# coding=utf-8
# Filename: cmdDotask.py
# :   

import os
import sys
import click
import json


from . import common as common
from . import ToolConfig, ToolTask, ToolTaskCollector, ToolDoit, logutil
logger = logutil.getLogger()

@click.group(chain=True, subcommand_metavar="TASK1 [ARGS]... [TASK2 [ARGS]...]...")
@click.option("--target", default=None, help='目标平台')
@click.option("--outputdir", default=None, help='输出目录') 
@click.option("--cachedir", default=None, help='缓存目录')
@click.option("--ignore-file", "-i", default=None, help='忽略列表文件')
@click.option("--continue", "-c", is_flag=True, help='子任务失败时不中断执行')
@click.option("--skip-items", "-s", is_flag=True, help='跳过所有任务项')
@click.option("--mode", "-m", default=None, type=click.Choice(["doit", "direct"]), help='指定任务运行模式')
# @click.option("--check-file-uptodate", default=None, type=click.Choice(["md5","timestamp"]), help=u'[doit] 检查文件过时的算法')
@click.option("--always-execute", "-a", is_flag=True, help='[doit] 总是执行所有任务')
@click.option("--verbosity", "-v", type=click.Choice(["0","1","2"]), default="1", help='[doit] 任务输出显示模式：0-静默|1-屏蔽stdout|2-全部显示')
@click.option("--process", "-n", type=int, default=1, help='[doit] 最大并行任务数')
@click.option("--parallel-type", "-P", type=click.Choice(["process", "thread"]), default="process", help='[doit] 并行执行方式')
@click.pass_context
def main(ctx, **arguments):
    '''执行特定任务'''

    xcfg = ToolConfig.getToolConfig()
    arguments["verbosity"] = int(arguments["verbosity"])

    target = common.ensure_target(xcfg, arguments)
    outputdir = common.ensure_outputdir(xcfg, arguments)
    cachedir = common.ensure_cachedir(xcfg, arguments)

    ignorefile = common.ensure_ignorefile(xcfg, arguments)
    ctx.obj = arguments

    print("==========================")
    print("target = "+target)
    print("outputdir = "+outputdir)
    print("cachedir = "+cachedir)
    print("projroot = "+xcfg.getProjectRoot())
    print("==========================")

############################################################
def createTaskContext(xcfg, doargs, args):
    taskContext = ToolTask.TaskContext(logger, xcfg)
    taskContext.setOptions(args)
    return taskContext

def createTaskCollector(xcfg, ignoreFile=None):
    # projroot = xcfg.getProjectRoot()
    collector = ToolTaskCollector.ToolTaskCollector(xcfg, ignoreFile)
    collector.collectAllTasks()
    return collector

def _mergeFilterFunction(f1, f2):
    if f1!=None and f2!=None:
        return lambda x: f1(x) and f2(x)
    if f1!=None:
        return f1
    return f2

def collectTaskItems(taskCollector, target, tasktype, args):
    fsencoding = sys.getfilesystemencoding()
    nameFilter = None
    if args["name"]:
        names = [x.encode(fsencoding) for x in args["name"]]
        nameFilter = taskCollector.filterPatternForNames(names)
    subdirFilter = None
    if args["subdir"]:
        subdirs = [os.path.abspath(x.encode(fsencoding)) for x in args["subdir"]]
        subdirFilter = taskCollector.filterPatternForSubdirs(subdirs)
    extensionFilter = None
    if "extensions" in args and args["extensions"] is not None:
        extensionFilter = taskCollector.filterForExtensionOptions(int(args["extensions"]))
    exclude_extensionFilter = None
    if "exclude_extensions" in args and args["exclude_extensions"] is not None:
        exclude_extensionFilter = taskCollector.filterForExcludeExtensionOptions(int(args["exclude_extensions"]))
    filterFunction = _mergeFilterFunction(nameFilter, subdirFilter)
    filterFunction = _mergeFilterFunction(filterFunction, _mergeFilterFunction(extensionFilter, exclude_extensionFilter))
    return taskCollector.getTaskItemsForTargetType(target, tasktype, filterFunction)

def prepareTaskSettings(xcfg, taskInfo):
    taskSettings = {}
    if taskInfo["settings"]:
        taskSettings = dict(taskSettings, **taskInfo["settings"])
    tasktype = taskInfo["name"]
    userSettings = xcfg.getProjectSettings("TaskSettings", tasktype)
    if userSettings:
        taskSettings = dict(taskSettings, **userSettings)
    return taskSettings

def executeTaskItems(doargs, args, taskItems, taskInfo, taskSettings, taskContext):
    xcfg = ToolConfig.getToolConfig()
    projroot = xcfg.getProjectRoot()
    target = doargs["target"]
    cachedir = doargs["cachedir"]

    tasktype = taskInfo["name"]
    taskcache = os.path.join(cachedir, target, tasktype)
    doargs["taskcache"] = taskcache

    # # collect task items
    # names = args["name"]
    # subdirs = args["subdir"]
    # fsencoding = sys.getfilesystemencoding()
    # if names:
    #     names = map(lambda x: x.encode(fsencoding), names)
    # if subdirs:
    #     subdirs = map(lambda x: os.path.abspath(x.encode(fsencoding)), subdirs)
    # taskItems = collectTaskItems(taskCollector, target, tasktype, names=names, subdirs=subdirs)
    # print(json.dumps(taskItems))
    # if not taskItems:
    #     logger.info("No tasks (target='%s', type='%s')." % (target, tasktype))
    #     return None

    outputdir = doargs["outputdir"]
    taskoutdir = outputdir
    if "outputdir" in taskSettings and taskSettings["outputdir"]:
        taskoutdir = os.path.join(taskoutdir, taskSettings["outputdir"])
    if not os.path.isdir(taskoutdir):
        os.makedirs(taskoutdir)

    # create task object
    result = None
    taskCreator = taskInfo["task_creator"]
    taskObj = taskCreator(taskInfo["name"], taskContext)
    taskObj.setSettings(taskSettings)
    taskObj.setupDirectories(
        projroot = os.path.abspath(projroot),
        outputdir = os.path.abspath(outputdir),
        cachedir = os.path.abspath(taskcache),
        taskoutdir = os.path.abspath(taskoutdir),
    )

    for item in taskItems:
        item["abs_input"] = taskObj.absInputPaths(item["input"])
        item["abs_output"] = taskObj.absOutputPaths(item["output"])

    # execute tasks
    mode = doargs["mode"] or taskInfo["mode"]
    if mode=="direct":
        result = ToolTask.runTasks(taskObj, taskItems, xcfg, doargs)
    elif mode=="doit":
        result = ToolDoit.runTasks(taskObj, taskItems, xcfg, doargs)
    else:
        logger.error("Unkown task mode: '%s'" % (mode))

    extraOutfiles = taskObj.getExtraOutfiles()
    if extraOutfiles:
        result["$task"] = {
            "name": taskObj.name,
            "status": "success",
            "outputs": extraOutfiles,
        }

    return result

def hasErrorsInResult(result):
    return result!=None and result["failures"]>0

def displayTaskResult(result, taskName, silentIfSucceed=False, isBriefMode=False):
    if result!=None and hasErrorsInResult(result):
        messages = []
        messages.append("##### ERRORS occur in task \"%s\" #####" % taskName)
        if isBriefMode:
            logger.error("\n".join(messages))
        else:
            nw = -12
            messages.append("\t%*s : %d" % (nw, "total", result["total"]))
            messages.append("\t%*s : %d" % (nw, "executed", result["executed"]))
            messages.append("\t%*s : %d" % (nw, "skipped", result["skipped"]))
            messages.append("\t%*s : %d" % (nw, "successes", result["successes"]))
            messages.append("\t%*s : %d" % (nw, "failures", result["failures"]))
            logger.warning("\n".join(messages))

    elif not silentIfSucceed:
        logger.info("Task \"%s\" is done successfully." % taskName)

def onStartTask(doargs, args, taskInfo, taskSettings, isInSeq=False):
    tasktype = taskInfo["name"]
    outputdir = doargs["outputdir"]
    if "outputdir" in taskSettings and taskSettings["outputdir"]:
        outputdir = os.path.join(outputdir, taskSettings["outputdir"])
    outputdir = os.path.abspath(outputdir)
    logger.info("-"*60)
    logger.info("Running task '%s' ..." % (tasktype))
    nw = -12
    if not isInSeq:
        logger.info("\t%*s : %s" % (nw, "target", doargs["target"]))
        logger.info("\t%*s : %s" % (nw, "ignore file", doargs["ignore_file"]))
    logger.info("\t%*s : %s" % (nw, "output root", outputdir))
    # logger.info("."*60)

def onFinishTask(doargs, args, taskInfo, result, isInSeq=False):
    tasktype = taskInfo["name"]
    # logger.info("."*60)
    logger.info("Finished task '%s'!" % (tasktype))
    if result!=None:
        displayTaskResult(result, tasktype, isBriefMode=isInSeq)
    logger.info("-"*60)

def onStartTaskSeq(doargs, args, seqInfo):
    name = seqInfo["name"]
    logger.info("="*60)
    logger.info("Running task sequence '%s' ..." % (name)) # todo
    outputdir = doargs["outputdir"]
    outputdir = os.path.abspath(outputdir)
    nw = -12
    logger.info("\t%*s : %s" % (nw, "target", doargs["target"]))
    logger.info("\t%*s : %s" % (nw, "ignore file", doargs["ignore_file"]))
    logger.info("\t%*s : %s" % (nw, "output root", outputdir))
    # logger.info("="*60)

def onFinishTaskSeq(doargs, args, seqInfo, results):
    name = seqInfo["name"]
    # logger.info("="*60)
    logger.info("Finished task sequence '%s'!" % (name))
    if results:
        for taskName, status, result in results:
            if status=="Done":
                displayTaskResult(result, taskName, silentIfSucceed=True)
            elif status=="Skipped":
                logger.info("Sub task \"%s\" is skipped." % (taskName))
    logger.info("="*60)

def dumpTaskItems(taskItems, filepath):
    if filepath == None:
        return
    with open(filepath, 'w') as f:
        f.write(json.dumps(
            taskItems,
            indent = 4,
            separators = (',', ': '),
            ensure_ascii=False).encode('utf8'))

def collectOutputList(outlist, result):
    if result == None or outlist==None:
        outlist = []
    taskItems = result["taskItems"]
    for item in taskItems:
        if "$result" in item:
            itemResult = item["$result"]
            outlist.append(itemResult)
    if "$task" in result:
        outlist.append(result["$task"])
    return outlist

def writeOutputList(statusCode, outlist, filepath):
    if filepath == None:
        return
    data = {"statusCode":statusCode, "outList":outlist}
    with open(filepath, 'w') as f:
        f.write(json.dumps(
            data,
            indent = 4,
            separators = (',', ': '),
            ensure_ascii=False).encode('utf8'))

# Create command entry for single task
def createTaskCmdEntry(taskInfo):

    @click.pass_context
    @click.option('--subdir', '-d', multiple=True, required=False, help='任务子目录')
    @click.option('--name', '-n', multiple=True, required=False, help='任务子名')
    @click.option("--task-dump-file", default=None, help='任务项输出文件')
    @click.option("--no-execute", is_flag=True, help='禁止执行任务')
    @click.option("--outlist-file", "-l", default=None, help='输出文件列表文件')
    @click.option("--extensions", '-ext', default=None, help='只包含哪些扩展')
    @click.option("--exclude-extensions", '-exext', default=None, help='排除哪些扩展')
    # @click.argument('subdir', required=False)
    def cmdEntry(ctx, **args):
        doargs = ctx.obj
        xcfg = ToolConfig.getToolConfig()
        target = doargs["target"]
        ignoreFile = doargs["ignore_file"]
        taskDumpFile = args["task_dump_file"]
        outlistFile = args["outlist_file"]
        outlist = [] if outlistFile!=None else None
        noExecute = args["no_execute"]

        taskContext = createTaskContext(xcfg, doargs, args)
        taskCollector = createTaskCollector(xcfg, ignoreFile)
        taskSettings = prepareTaskSettings(xcfg, taskInfo)
        tasktype = taskInfo["name"]
        taskItems = collectTaskItems(taskCollector, target, tasktype, args)
        # if not taskItems:
        #     logger.info("No tasks (target='%s', type='%s')." % (target, tasktype))

        result = None
        if not noExecute:
            onStartTask(doargs, args, taskInfo, taskSettings)
            result = executeTaskItems(doargs, args, taskItems, taskInfo, taskSettings, taskContext)
            onFinishTask(doargs, args, taskInfo, result)
            if outlist!=None:
                collectOutputList(outlist, result)

        if taskDumpFile!=None:
            dumpTaskItems(taskItems, taskDumpFile)

        statusCode = 0
        if result!=None and hasErrorsInResult(result):
            statusCode = -1
        if not noExecute and outlist!=None:
            writeOutputList(statusCode, outlist, outlistFile)
        if statusCode!=0:
            sys.exit(statusCode)

    cmdEntry.__doc__ = taskInfo["cmd_help"]
    return click.command()(cmdEntry)

# Create command entry for task sequence
def createTaskSequenceCmdEntry(seqInfo):

    @click.pass_context
    @click.option('--subdir', '-d', multiple=True, required=False, help='任务子目录')
    @click.option('--name', '-n', multiple=True, required=False, help='任务子名')
    @click.option("--task-dump-file", default=None, help='任务项输出文件')
    @click.option("--no-execute", is_flag=True, help='禁止执行任务')
    @click.option("--outlist-file", "-l", default=None, help='输出文件列表文件')
    @click.option("--extensions", '-ext', default=None, help='只包含哪些扩展')
    @click.option("--exclude-extensions", '-exext', default=None, help='排除哪些扩展')
    # @click.argument('subdir', required=False)
    def cmdEntry(ctx, **args):
        doargs = ctx.obj
        xcfg = ToolConfig.getToolConfig()
        target = doargs["target"]
        ignoreFile = doargs["ignore_file"]
        taskDumpFile = args["task_dump_file"]
        taskItemsToDump = [] if taskDumpFile!=None else None
        outlistFile = args["outlist_file"]
        outlist = [] if outlistFile!=None else None
        taskContext = createTaskContext(xcfg, doargs, args)
        taskCollector = createTaskCollector(xcfg, ignoreFile)
        noBreak = doargs["continue"]
        noExecute = False #args["no_execute"]

        if not noExecute:
            onStartTaskSeq(doargs, args, seqInfo)

        subtasks = seqInfo["subtasks"]
        results = []
        failedCount = 0
        for taskName in subtasks:
            taskInfo = ToolTask.getTaskInfo(taskName)
            if taskInfo==None:
                continue
            if not noBreak and failedCount>0:
                results.append((taskName, "Skipped", None))
            else:
                taskSettings = prepareTaskSettings(xcfg, taskInfo)
                tasktype = taskInfo["name"]
                taskItems = collectTaskItems(taskCollector, target, tasktype, args)
                # if not taskItems:
                #     logger.info("No tasks (target='%s', type='%s')." % (target, tasktype))
                if taskItemsToDump!=None and taskItems:
                    taskItemsToDump = taskItemsToDump + taskItems
                if not noExecute:
                    onStartTask(doargs, args, taskInfo, taskSettings, isInSeq=True)
                    result = executeTaskItems(doargs, args, taskItems, taskInfo, taskSettings, taskContext)
                    if result!=None and hasErrorsInResult(result):
                        failedCount += 1
                    results.append((taskName, "Done", result))
                    onFinishTask(doargs, args, taskInfo, result, isInSeq=True)
                    if outlist!=None:
                        collectOutputList(outlist, result)

        if not noExecute:
            onFinishTaskSeq(doargs, args, seqInfo, results)

        if taskDumpFile!=None:
            dumpTaskItems(taskItemsToDump, taskDumpFile)

        statusCode = 0
        if failedCount>0:
            statusCode = -1
        if not noExecute and outlist!=None:
            writeOutputList(statusCode, outlist, outlistFile)
        if statusCode!=0:
            sys.exit(statusCode)

    cmdEntry.__doc__ = seqInfo["cmd_help"]
    return click.command()(cmdEntry)

def setupTaskCommands():
    for taskName, taskInfo in ToolTask.registeredTasks():
        # print taskName, taskInfo
        cmdName = taskInfo["cmd_name"]
        if not cmdName:
            cmdName = taskName
        cmdEntry = createTaskCmdEntry(taskInfo)
        if not cmdEntry:
            continue

        # 屏蔽：暂时不需要该命令，直接用 ui 即可
        # if not main.get_command(None, cmdName):
        #     main.add_command(cmdEntry, cmdName)
        # else:
        #     main.add_command(cmdEntry, taskName+":"+cmdName)

    for seqName, seqInfo in ToolTask.taskSequences():
        cmdName = seqInfo["cmd_name"]
        if not cmdName:
            cmdName = taskName
        if not main.get_command(None, cmdName):
            cmdEntry = createTaskSequenceCmdEntry(seqInfo)
            if cmdEntry:
                main.add_command(cmdEntry, cmdName)
        else:
            logger.warning('Command name "%s" for task sequence "%s" is already used.'
                % (cmdName, seqName))

############################################################
if __name__ == '__main__':
    main()
