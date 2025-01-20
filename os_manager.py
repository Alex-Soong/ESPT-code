# 处理.pcap文件的结果文件的标志符。
# 报文参数分隔符。
split_logo = '###'
# 报文流之间的分隔符。
stream_logo = '##########'
# TODO: 读文件的时候最后的\n怎么处理？
# 缺失报文的补充。
loss_logo = '$LOSS$LOGO'
# 文本内容。
content_logo = 'content'
# 处理结果文件的目录。
project_path = '/home/song/codess/ESPT-code/'
sake_cata = project_path + 'info/handle/'
# pcap文件目录。
pcap_cata = project_path + 'info/pcap/'
# svg文件目录。
svg_cata = project_path +'info/picsvg/'
# 测试文件生成目录。
check_cata = project_path +'info/test/'

# WS Daikon库的相关配置。
# 在.perl文件中新增：
'''
# 提供checkargs.pm包的位置。
use lib '/home/ll/L/ZooForLessons/Senior/ESPT/daikon/wstdaikon/scripts';
'''
# 创立.csv文件的位置。
csv_road = project_path +'info/wstdaikon.csv'
# .perl文件绝对路径。
perl_road = project_path + 'daikon/wstdaikon/scripts/convertcsv.pl'
# .jar包文件绝对路径。
jar_road = project_path + 'daikon/wstdaikon/daikon.jar'
# .decls文件绝对路径。
decls_road = project_path + 'info/wstdaikon.decls'
# .dtrace文件绝对路径。
dtrace_road = project_path + 'info/wstdaikon.dtrace'

# 次要字段的处理。
# 缺失的次要字段。
loss_minor = 'LOSS_MINOR'
