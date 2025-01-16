import numpy


class Rule:

    def __init__(self, buildable = False, kind = 0, info = None):
        '''
        转移的规则。
        :param buildable: 是否具有构建数据包的能力，默认无。
        :param kind: 规则的类型，包含：
                        0: 未知类型。
                        1: 数字相等。具有构建数据包的能力。直接转化为整数int。
                        2: 字符串相等。具有构建数据包的能力。
                        3: 数值运算相等。具有构建数据包的能力，但需要结合其他的规则一起推断，交给Transition类实现。
                            包含变量相等: a - b == 0不同于a == b，前者表示a,b是数字，后者无此作用。
                            设立True、False标记位，表示表达式是否形如a0 == b0，字符串的推断仅可能于此相关。
                        4: 集合属于。
                        5: 字符串或数值比较。没有直接构建数据包的能力，但是可以约束其他规则。
                        6: 一对一映射。默认不使用。
        :param info: 规则内容，形如：
                        0: ('<UNKNOWN>')。
                        1: ('a0', 1)。
                        2: ('a0', '1')。
                        3: (True | False, '<EXPRESSION_left>', '<EXPRESSION_right>')。
                        4: ('a0', {'1', '2'}) # 集合中应该都是字符串。
                        5: ('> | < | >= | <= | !=', 'a0', 1 | '1')。
                        6: ('a0', 'b0', {'a0_1': 'b0_1', ...})。
        '''
        self.buildable = buildable
        self.kind = kind
        self.info = () if not info else info

    def __str__(self):
        return f'{self.kind}:{self.info} {self.buildable}'

    __repr__ = __str__

    def check(self, catalogs: dict, flag = False):
        '''
        检测规则。
        :param flag: 是否仅验证了输入报文。
        '''
        match self.kind:
            case 0:
                # print(f'存在未知类型规则{self}')
                return True
            case 1 | 2:
                if len(self.info) != 2:
                    print(f'存在不正确的数字或字符串相等规则{self}')
                    return True
                # 仅验证输入报文。
                if self.info[0] not in catalogs:
                    return flag
                return catalogs[self.info[0]] == str(self.info[1])
            case 3:
                if len(self.info) != 3:
                    print(f'存在不正确的运算相等规则{self}')
                    return True
                result = False
                try:
                    result = eval(f'{self.info[1]} == {self.info[2]}', None, catalogs)
                except NameError:
                    if flag:
                        return flag
                    else:
                        print(f'存在不正确的运算相等规则{self}，其运算符或变量有误')
                except TypeError:
                    try:
                        number_catalogs = {
                            catalogi: int(catalogj) for catalogi, catalogj in catalogs.items() if catalogj.isdigit()
                        }
                        result = eval(f'{self.info[1]} == {self.info[2]}', None, number_catalogs)
                    except TypeError:
                        print(f'存在不正确的运算相等规则{self}，其运算符或变量有误')
                return result
            case 4:
                if len(self.info) != 2 or not isinstance(self.info[1], set):
                    print(f'存在不正确的集合属于规则{self}')
                    return True
                # 仅验证输入报文。
                if self.info[0] not in catalogs:
                    return flag
                return catalogs[self.info[0]] in self.info[1]
            case 5:
                if len(self.info) != 3 or self.info[0] not in ['>', '<', '>=', '<=', '!=']:
                    print(f'存在不正确的比较规则{self}')
                    return True
                # 仅验证输入报文。
                if self.info[1] not in catalogs:
                    return flag
                # 数字不可以直接作为字符串比较。
                feed = catalogs[self.info[1]]
                if isinstance(self.info[2], numpy.int64) or isinstance(self.info[2], int):
                    if not feed.isdigit():
                        return False
                    return eval(f'{feed} {self.info[0]} {self.info[2]}')
                return eval(f'\'{feed}\' {self.info[0]} \'{self.info[2]}\'')
            case 6:
                if len(self.info) != 3 or not isinstance(self.info[2], dict):
                    print(f'存在不正确的一对一映射规则{self}')
                    return True
                # 仅验证输入报文。
                if self.info[0] not in catalogs or self.info[1] not in catalogs:
                    return flag
                if catalogs[self.info[0]] not in self.info[2]:
                    return False
                return self.info[2][catalogs[self.info[0]]] == catalogs[self.info[1]]

    def tell(self):
        match self.kind:
            case 0:
                return ''
            case 1 | 2:
                return f'{self.info[0]} = {self.info[1]}'
            case 3:
                return f'{self.info[1]} = {self.info[2]}'
            case 4:
                return f'{self.info[0]} in {self.info[1]}'
            case 5:
                return f'{self.info[1]} {self.info[0]} {self.info[2]}'
            case 6:
                return f'{self.info[0]}-{self.info[1]}=>{len(self.info[2])}'
