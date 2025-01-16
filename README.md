# Daikon系统
配置见**Daikon文档**，使用其CSV文件分析功能需要额外的Perl库，修改`scripts/`中`.pl`文件中的路径配置。
> Daikon：`http://plse.cs.washington.edu/daikon/`。
- `convertcsv.pl`文件中新增`use lib '绝对路径/ESPT/daikon/wstdaikon/scripts';`，并把下载的`checkargs.pm`复制到`scripts/`目录。
  > 或者使用其他方式实现上述相同效果。
- Daikon系统放在`ESPT/daikon/wstdaikon/`目录下，具体怎么调用到daikon.jar包需要看个人的`os_manager.py`文件配置。

# 虚拟环境
新增`.pth`文件将ESPT根目录放置其中，否则编译器调用不到父目录同级文件。

# 项目内配置
- `os_manager.py`中记录了各特殊文件或文件夹的绝对路径、文件中的特殊字符。
- `info/pcap/`中存放训练数据`.pcap`和`.pcapng`文件。
- `info/picsvg/`中存放`svg`文件。
- `info/test/`中存放测试结果。
- `test/`中存放测试和使用文件，模型使用方法在这里面。