# gtool 用户手册

gtool为前端开发的工具集。

本文档将介绍用户对gtool的安装、gtool命令的使用。

## gtool 安装


安装的详细步骤请参照以下Git库中`README.md`的详细介绍

Gitlab地址：// todo

*注：在使用gtool命令处理资源前，请先安装TexturePacker以及命令行工具*

## gtool 命令的使用

在终端键入gtool，将得到gtool命令的Usage：

```
clean    清空图片输出目录
  config   查看或修改资源库设置选项
  dataset  导出json命令
  dotask   执行特定任务
  init     创建或重置资源库
  target   Target管理$ gtool

Usage: gtool [OPTIONS] COMMAND [ARGS]...

Options:
  -h, --help     显示帮助信息并退出
  -v, --version  显示版本信息并退出

Commands:
  clean    清空图片输出目录
  config   查看或修改资源库设置选项
  dataset  导出json命令
  dotask   执行特定任务
  init     创建或重置资源库
  target   Target管理
```

### 资源库的创建、查看及修改

* `gtool init`：创建或重置资源库。

  ```
  ~ $ gtool init --help
  
  Usage: gtool init [OPTIONS]
  
    创建或重置资源库
  
  Options:
    --outputdir TEXT      图片默认输出目录
    --projroot TEXT       图片默认项目目录
    --jsonoutputdir TEXT  表默认输出目录
    --jsonprojroot TEXT   表默认项目目录
    --help            Show this message and exit.
  ```

  我们通常使用下面这种更自动化的方式为项目创建资源库。

  ```
  ~ $ gtool init.py 
  选择图片资源默认输出目录: /data/assets/resources/uiatlas 
  选择图片资源默认输入目录: /data/targetDir 
  选择配置默认输出目录: /data/assets/resources/config/data 
  选择配置默认输入目录: /data/design 
  已重置资源库(/data/tool/GTool/.gtool)
  ```

* `gtool config`：查看或修改资源库设置选项

  ```
  ~ $ gtool config --help

  Usage: gtool config [OPTIONS] COMMAND [ARGS]...

    查看或修改资源库设置选项

  Options:
    --help  Show this message and exit.

  Commands:
    get   输出指定选项的值
    list  显示设置选项
    set   设置或删除指定选项的值。 expr格式为"<key>=[<value>]"，若value为空，则删除该选项。
  ```
  
资源库创建成功后，会在GTool项目的根目录下生成`.gtool`工程文件，`.gtool/xconfig.cfg`为相关的配置文件，我们可以通过该命令对配置文件中的相关字段进行查看和修改，例如：
  
设置指定选项的值：
  
```
  ~ $ gtool config set projroot=/data/work/~
  
gtool.projroot=/data/work/~
  ```
  
查看指定选项的值：
  
```
  ~ $ gtool config get outputdir
  
/data/work/~
  ```

*注：成功完成资源库的创建后，就可以使用资源处理的相关命令了。*


### 资源处理的相关命令

在使用gtool资源处理的相关命令前，我们要先了解gtool有关资源的一些基本定义及相关配置。

#### 资源处理的基本定义：

* `target`：目标平台。通过目标平台的配置及命令的参数化，对资源处理任务进行平台化区分。
  * 任务类型：gtool定义了资源处理的任务类型
    1. `PackUIImage`：处理UI资源的TP任务类型

#### 资源处理的相关配置：

*   `gtool.settings`文件：

    ```
    TaskSettings:
        PackUIImage:
            outputdir: asset/ui
            index_name: index.json
            index_fmt: json
    ...

    
    ```

    * `TaskSettings`：为某一类型的任务指定输出目录以及生成index文件的名字和格式等
    
    * `cleanup`：配置了指定的清空任务，与`gtool clean` 命令的`-t`参数配合使用。

      `gtool clean`会清空输出目录，如果只想清空输出目录下的某个子目录，则可以参照以下操作：
    
  首先在`gtool.settings`中添加配置
    
      ```
      cleanup:
          ui: [asset/ui]
  ```
    
  然后执行以下命令，清空输出目录下asset/ui子目录
    
  ```
      $ gtool clean -t ui
  ```
    
* `.gtask`文件：

    各ui或anim子目录的配置文件，描述了该目录下资源处理的各项具体任务。

    ```
    target: __ANY__
    items:
        # PackUIImage tasks
        TP_battleRes:
            type: PackUIImage
            options: {}
            output: [battle_battleRes.plist, battle_battleRes.png]
            input: [battleRes]
            ignore: [battleRes/progressbar]
            
        # PackAnimImage tasks
        TP_gyzyimage:
            type: PackAnimImage
            options: {}
            output: [gyzyimage.plist, gyzyimage.png]
            input: [gyzyimage]

    ```
    
    任务配置的参数：
    
    * `type`：任务类型
    * `options`：任务的选项参数
    * `output`：输出文件
    * `input`：输入目录或文件
    * `ignore`：任务处理忽略的目录或文件

#### 资源处理的命令：

-   `gtool target`：查看以及切换当前目标平台

    ```
    ~ $ gtool target

    Usage: gtool target [OPTIONS] COMMAND [ARGS]...

      Target管理

    Options:
      --help  Show this message and exit.

    Commands:
      status  查看当前Target信息
      switch  切换Target
      list    查看当前可选target
    ```

*   `gtool dotask/gdo`：执行特定任务

    ```
    ~ $ gdo

    Usage: xdo [OPTIONS] TASK1 [ARGS]... [TASK2 [ARGS]...]...

      执行特定任务

    Options:
      --target TEXT                   目标平台
      --outputdir TEXT                输出目录
      --cachedir TEXT                 缓存目录
      -i, --ignore-file TEXT          忽略列表文件
      -c, --continue                  子任务失败时不中断执行
      -s, --skip-items                跳过所有任务项
      -m, --mode [doit|direct]        指定任务运行模式
      -a, --always-execute            [doit] 总是执行所有任务
      -v, --verbosity [0|1|2]         [doit] 任务输出显示模式：0-静默|1-屏蔽stdout|2-全部显示
      -n, --process INTEGER           [doit] 最大并行任务数
      -P, --parallel-type [process|thread]
                                  [doit] 并行执行方式
      --help                          Show this message and exit.
    
    Commands:
      ui  处理UI资源(合并UI碎图)
    ```
    
* `gtool run/xrun`：执行自定义命令

    ```
    ~ $ xrun

    Usage: xrun [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

      执行自定义命令

    Options:
      --target TEXT     目标平台
      --outputdir TEXT  输出目录
      --cachedir TEXT   缓存目录
      --help            Show this message and exit.

    Commands:
      dataset    excel导出命令
      luaalt     分析Lua源码中的标记，生成用于Lua自动加载的配置文件
      sync       同步Raw资源（无需额外处理的资源）
      uitaskgen  为UI子目录生成.xtask文件
    ```

* `gtool clean`：清空输出目录

    ```
    ~ $ gtool clean --help

    Usage: gtool clean [OPTIONS]

      清空输出目录

    Options:
      --all             清空整个输出目录
      --outputdir TEXT  重定义输出目录
      --rm-dir          删除目录而非清空目录
      -p, --path TEXT   清理指定路径
      --help            Show this message and exit.
    ```

#### 数值表相关

1. 分表命名规则:
分表通过 ***表内的分页签*** 的方式区分
2. gdataset: 导出 json 配置
  在终端cd到gtool/src/exceltools/目录，执行 python cmdExcelTools.py --help 可查看详细的参数配置

  ```
  ~ $ gdataset --help                  
  Usage: gdataset [OPTIONS]
  
    导出json命令
  
  Options:
    -s, --source TEXT     数据表分支
    -r, --revision TEXT   更新数据表到指定版本
    --cache / --no-cache  是否使用缓存
    --help                Show this message and exit.
  ```


