# G-Tools

=========
前端开发工具集。

Gitlab地址：待添加  // TODO


安装 python
-----------------------
python3=3.7.0

搭建开发环境
-----------------------

1. 从Gitlab上clone项目代码。

        $ git clone ...

2. 根据模板生成`.gitignore`文件。

        $ cd xtool
        xtool $ cp gitignore-template .gitignore

3. 执行`setup.py`，构建开发环境。

        xtool $ sudo python setup.py develop

  *注：执行setup.py时，所有需要的依赖库会被自动安装（使用EasyInstall）。*

第3步的setup.py脚本会自动安装依赖库。如果安装依赖库失败，且已经安装了pip，可用pip进行查看或安装。pip使用方式如下：

        pip show -V <package> # 查看是否安装了package，以及其版本
        pip install <package> # 安装package
        pip install <package>==<version> # 安装指定版本的package

如果pip也不能安装，则只能尝试直接搜索下载依赖库，进行手动安装。

本项目依赖的库有：

* PyYAML(==3.11)
* click(>=5.1)
* dataTools>=1.0.1
* doit(==0.32.0)


更新数值导表工具代码
-----------------------
1. 当 dataTools 导数值表工具有代码更新时，需要重新安装或者升级下扩展库
2. 打开终端，在任意目录下执行下列命令
        
        json数值表lua更新 
        sudo -H pip3 install --upgrade -i http://10.0.4.168:8135/packages/ dataTools --trusted-host 10.0.4.168
        
3. 查看json版本是否已经为最新版本(通常更新人员会提示大家最新版本号，与之对比)

        json数值表更新
        pip3 show -V dataTools

4. 提示没有 pip 命令时，先百度下安装 pip 命令, 可参考 [pip安装](https://blog.csdn.net/lyj_viviani/article/details/70568434)

5. 如果pip提示升级错误，首先升级一下 pip 命令即可, 最新版本为 19.0.3

        sudo pip3 install --upgrade pip

安装常见错误
-----------------------
1. 如果某些依赖的package下载比较慢，或者报错`ImportError: No module named <package>`，可以考虑通过pip手动安装：

        sudo pip3 intall <package> 


