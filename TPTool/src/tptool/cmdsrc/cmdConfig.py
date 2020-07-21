#!/usr/bin/env python
# coding=utf-8
# Filename: cmdConfig.py
# :   

import click

from . import logutil, ToolConfig
logger = logutil.getLogger()

@click.group()
@click.pass_context
def main(ctx, **arguments):
    '''查看或修改资源库设置选项'''
    pass

@click.command()
def _list(**args):
    '''显示设置选项'''

    xcfg = ToolConfig.getToolConfig()
    items = xcfg.listValues()
    lines = []
    for section, option, value in items:
        lines.append("%s.%s=%s" % (section, option, value))
    logutil.echo("\n".join(lines))

main.add_command(_list, "list")


@click.command()
@click.argument('key', nargs=1)
def _get(**args):
    '''输出指定选项的值'''

    xcfg = ToolConfig.getToolConfig()
    key = args["key"]
    nameparts = ToolConfig.parseKey(key)
    logutil.echo(xcfg.getValue(nameparts[0], nameparts[1], ""))

main.add_command(_get, "get")


@click.command()
@click.option('--keep-section', is_flag=True, help='当某section的值都被删除时，是否保留该section')
@click.argument('expr', nargs=1)
def _set(**args):
    '''设置或删除指定选项的值。\n
    expr格式为"<key>=[<value>]"，若value为空，则删除该选项。'''

    xcfg = ToolConfig.getToolConfig()
    expr = args["expr"]
    pos = expr.find("=")
    if pos<=0:
        logutil.echo("expr不是合法表达式: %s" % (expr))
        exit(-1)
    key = expr[:pos].strip()
    value = expr[pos+1:].strip()
    nameparts = ToolConfig.parseKey(key)
    if value=="":
        value = None
    ok = xcfg.setValue(nameparts[0], nameparts[1], value)
    if value==None and not args["keep_section"]:
        options = xcfg.listOptions(nameparts[0])
        if options==None or len(options)==0:
            xcfg.removeSection(nameparts[0])
    if ok:
        xcfg.saveConfigs()
        if value==None:
            logutil.echo('成功删除了选项"%s"' % (key))
        else:
            logutil.echo('%s.%s=%s' % (
                nameparts[0], nameparts[1],
                xcfg.getValue(nameparts[0], nameparts[1])))
    else:
        logutil.echo('操作失败')

main.add_command(_set, "set")


if __name__ == '__main__':
    main()
