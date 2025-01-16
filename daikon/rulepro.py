import subprocess
import pandas
from re import compile
from os_manager import csv_road, perl_road, jar_road, decls_road, dtrace_road, loss_minor
from automata.rules import Rule


def build_rules(minors, diyrule = False):
    '''
    调用规则监视器产生规则。
    :param minors: 规则监视器需要的字段集合。
    :param diyrule: 是否添加额外的自定义规则。
    :return: 格式化后的规则。
    '''
    # 请求次要字段长度、响应次要字段长度。
    minoral, minorbl = len(minors[0][0]), len(minors[0][1])
    # 列名。
    titles = [f'a{ai}' for ai in range(minoral)] + [f'b{bi}' for bi in range(minorbl)]
    # 需要被转译的CSV内容。
    # replace('\r', '').replace('\n', '').replace(',', '').replace('"', '\'')。
    csv_translate = str.maketrans('\r\n,"', '   \'')
    with (open(csv_road, 'w', encoding = 'utf-8') as csvtext):
        # 写入标题。
        csvtext.write(','.join(titles) + '\n')
        for minori in minors:
            givei, reapi = minori[0], minori[1]
            # 如果次要字段长度不同则直接不做判断。
            if (len(givei), len(reapi)) != (minoral, minorbl):
                print(f'#common.py: (72) Length Of Minors Not Equal\n')
                return []
            # 处理换行符、','等特殊字符。
            letters = ','.join([givej.translate(csv_translate) for givej in givei]) if givei else ''
            if reapi:
                if letters:
                    letters += ','
                letters += ','.join([reapj.translate(csv_translate) for reapj in reapi])
            csvtext.write(letters + '\n')
    result: list[Rule] = call_daikon()
    if diyrule:
        diy_rules(result)
    return result


def check_rules(gives, reaps, rules: list[Rule], minors, flag = False):
    '''
    通过规则验证字段的合法性。
    :param gives: 字段。
    :param reaps: 字段。
    :param rules: 规则。
    :param minors: 留存的标准字段。
    :param flag: 只检测请求报文。
    '''
    givel, reapl = len(gives), len(reaps)
    if not rules or (not flag and (givel, reapl) != (len(minors[0]), len(minors[1]))) or (
            flag and givel != len(minors[0])
    ):
        return True
    # replace('\r', '').replace('\n', '').replace(',', '').replace('"', '\'')。
    csv_translate = str.maketrans('\r\n,"', '   \'')
    pars = {f'a{i}': gives[i].translate(csv_translate) for i in range(givel)}
    if not flag:
        pars.update({f'b{i}': reaps[i].translate(csv_translate) for i in range(reapl)})
    # eval()函数极其危险，可以设计并调用自定义方法解决。
    # result = all([eval(rulei, None, pars) for rulei in self.rules])
    for rulei in rules:
        # temp = eval(rulei, None, pars)
        if not rulei.check(pars, flag):
            print(f'>> 规则检测错误: {pars}, {rulei}')
            return False
    return True


def call_daikon():
    '''
    调用Daikon分析生成规则。无法推断异或、大部分的模运算规则。
    :return: Daikon执行的结果。
    '''
    try:
        # 运行.perl脚本。
        # /home/ll/L/ZooForLessons/Senior/ESPT/daikon/wstdaikon/scripts/convertcsv.pl myfile.csv
        subprocess.run([perl_road, csv_road], capture_output = True, check = True, text = True)
        # 运行.jar包。
        # java -cp $DAIKONDIR/daikon.jar daikon.Daikon --nohierarchy myfile.decls myfile.dtrace
        letters = subprocess.run(
            ['java', '-cp', jar_road, 'daikon.Daikon', '--nohierarchy', decls_road, dtrace_road],
            capture_output = True, check = False, text = True
        ).stdout
        # Daikon version 5.8.18, released June 23, 2023; http://plse.cs.washington.edu/daikon.
        # Reading declaration files .
        # (read 1 decls file)
        # Processing trace data; reading 1 dtrace file:
        #
        # ===========================================================================
        # aprogram.point:::POINT
        # 内容
        # Exiting Daikon.
        if len(letters) < 298:
            return []
        if letters[:279].endswith('aprogram.point:::POINT\n'):
            letters = letters[279:-17]
        else:
            print('rulepro.call_daikon letters范围错误')
            i = letters.find('aprogram.point')
            if i != -1:
                letters = letters[i + 23:-17]
            else:
                return []
        if not letters:
            return []
        results = []
        for letteri in letters.split('\n'):
            if loss_minor not in letteri:
                results.append(letteri)
        # python_rules(results)
        return python_rules(results)
    except subprocess.CalledProcessError as suberr:
        print('#rulepro.py: (117) Daikon analysis failed: ')
        print(suberr)
        print('#rulepro.py: Error Finish!\n')
        return []


def python_rules(rules) -> list[Rule]:
    samples = [
        # 类型1，数字相等。
        (compile(r'^([ab]\d+) == ([+-]?\d+)$'), 1),
        # 类型2，字符串相等。
        (compile(r'^([ab]\d+) == "([^"]*)"$'), 2),
        # 类型3，运算相等。
        (compile(
            r'^([ab]?\d+(?: [+\-*/%] [ab]?\d+|\*\*[ab]?\d+)*) == ([ab]?\d+(?: [+\-*/%] [ab]?\d+|\*\*[ab]?\d+)*)$'
        ), 3),
        # 类型4，集合属于。
        (compile(r'^([ab]\d+) one of \{(.*)}$'), 4),
        # 类型5，范围运算。
        (compile(r'^([ab]\d+) ([><]=?|!=) (\d+)$'), 5),
    ]
    result = []
    for rulei, rulej in enumerate(rules):
        for samplei, samplej in samples:
            temp = samplei.fullmatch(rulej)
            if not temp:
                result.append(Rule(False, 0, rulej))
                continue
            batchs = temp.groups()
            match samplej:
                case 1:
                    try:
                        result.append(Rule(True, samplej, (batchs[0], int(batchs[1]))))
                    except ValueError:
                        result.append(Rule(True, 2, batchs))
                case 2:
                    result.append(Rule(True, samplej, batchs))
                case 3:
                    flag = False
                    for batchi in batchs:
                        if not batchi.startswith('a') and not batchi.startswith('b'):
                            flag = False
                            break
                        flag = batchi[1:].isdigit()
                        if not flag:
                            break
                    result.append(Rule(True, samplej, (flag, batchs[0], batchs[1])))
                case 4:
                    gathers = set()
                    for batchi in batchs[1].split(','):
                        gatheri = batchi.strip(' "')
                        try:
                            gatheri = float(gatheri)
                            gatheri = int(gatheri)
                        except ValueError:
                            pass
                        gathers.add(str(gatheri))
                    result.append(Rule(False, samplej, (batchs[0], gathers)))
                case 5:
                    if len(batchs) >= 3 and (batchs[3].startswith('a') or batchs[3].startswith('b')):
                        break
                    result.append(Rule(False, samplej, (batchs[1], batchs[0], batchs[2])))
    return result


def diy_rules(result: list[Rule], mapping = False, maplimit = 5):
    '''
    自定义规则。默认实现数值列上下界。
    :param mapping: 是否实现映射退则约束推断。
    '''
    csvdf = pandas.read_csv(csv_road)
    csvtles = csvdf.columns
    # 归纳类型为1、4中的元素，其不需要判断上下界。
    rules1, rules4 = set(), set()
    for rulei in result:
        if rulei.kind == 1:
            rules1.add(rulei.info[0])
        elif rulei.kind == 4:
            rules4.add(rulei.info[0])
    for csvtlei in csvtles:
        if csvtlei in rules1 or csvtlei in rules4 or csvdf[csvtlei].dtype not in ('float64', 'int64'):
            continue
        erect_high, erect_low = csvdf[csvtlei].max(), csvdf[csvtlei].min()
        if erect_high == erect_low:
            result.append(Rule(True, 1, (csvtlei, erect_high)))
            continue
        result.append(Rule(False, 5, ('>=', csvtlei, erect_low)))
        result.append(Rule(False, 5, ('<=', csvtlei, erect_high)))
    if mapping:
        diyrule_mapping(result, maplimit)


def diyrule_mapping(result: list[Rule], maplimit: int):
    '''
    自定义规则：一对一映射。
    :param maplimit: 一对一映射数量的上限，防止无重复元素的组合被误认为映射。
    '''
    df = pandas.read_csv(csv_road)
    # 获取列名，其按照从左到右的顺序返回列名。
    erects = df.columns
    # 每列与每列之间按照笛卡尔乘积的关系构建一个矩阵。
    for erecti in erects:
        for erectj in erects:
            # 只考虑矩阵的左下部分。
            if erecti == erectj:
                break
            grpbys1, grpbys2 = df.groupby(erecti)[erectj], df.groupby(erectj)[erecti]
            # 只考虑一对一的映射关系。
            if not (grpbys1.transform('nunique').eq(1).all() and grpbys2.transform('nunique').eq(1).all()):
                continue
            # 分组映射的数量应该有所限制。
            if grpbys1.ngroups > maplimit:
                continue
            catalogs = {}
            if erecti < erectj:
                for grpbyi, grpbyj in grpbys1:
                    # 获取每个分组的值。
                    catalogs[grpbyi] = list(grpbyj)[0]
                result.append(Rule(False, 6, (erecti, erectj, catalogs)))
            else:
                for grpbyi, grpbyj in grpbys2:
                    # 获取每个分组的值。
                    catalogs[grpbyi] = list(grpbyj)[0]
                result.append(Rule(False, 6, (erectj, erecti, catalogs)))
