from os_manager import split_logo, stream_logo, loss_logo, loss_minor


class Message:
    '''
    输入报文和输出报文格式对。
    '''

    def __init__(self):
        # 输入报文的主要部分，具体表现为标识头、响应码等，默认为λ。
        self.give_major = chr(955)
        # 输入报文的其他参数，是有序列表。
        self.give_minors = []
        # 输出报文的主要部分，具体表现为标识头、响应码等，默认为λ。
        self.reap_major = chr(955)
        # 输出报文的其他参数，是有序列表。
        self.reap_minors = []

    def __str__(self):
        return f'{self.give_major}: {self.give_minors} --> \n\t\t{self.reap_major}: {self.reap_minors}\n'

    __repr__ = __str__

    def __eq__(self, other):
        return isinstance(other, Message) and (self.give_major, self.reap_major) == (other.give_major, other.reap_major)

    def __hash__(self):
        return hash((self.give_major, self.reap_major))

    @classmethod
    def build_mespair(cls, give_major = chr(955), give_minors = None, reap_major = chr(955), reap_minors = None):
        '''
        实现对输入/输出报文对缺失的补充，返回合法的类实例。
        :return: Message实例。
        '''
        if not give_minors or not isinstance(give_minors, list):
            give_minors = []
        if not reap_minors or not isinstance(reap_minors, list):
            reap_minors = []
        mespair = Message()
        mespair.give_major = give_major
        mespair.give_minors = give_minors
        mespair.reap_major = reap_major
        mespair.reap_minors = reap_minors
        return mespair

    def look_major(self):
        '''
        获取主要字段。
        一般一个转移仅需要一个主要字段，但是次要字段将以集合的形式存在。
        '''
        return self.give_major, self.reap_major

    def look_minors(self):
        '''
        获取次要字段。
        一般一个转移会存在多个次要字段，以集合的形式存在。
        '''
        return self.give_minors, self.reap_minors


def build_message_seqs(handle_text):
    '''
    读取处理文件，构建Message对列表。
    :param handle_text: 处理文件的完整路径。
    :rtype: list[list[Message]]。
    '''

    def handle_line(line: str):
        if line == loss_logo:
            return chr(955), [loss_minor]
        line_splits = line.split(':', 1)
        major, tempminors = line_splits[0], ''
        if len(line_splits) > 1:
            tempminors = line_splits[1]
        minors = [loss_minor] if not tempminors or tempminors == ' ' else tempminors.split(split_logo)
        return major, minors

    # 读取处理文件。
    with open(handle_text, 'r') as text:
        lines = text.readlines()
    results, resulti = [], []
    i, linel = 0, len(lines)
    # 一次处理两行。
    while i < linel:
        # 由于冗余的流分隔符导致的特例。
        if i + 1 >= linel:
            break
        # 去除行末的换行符。
        linei, linej = lines[i][:-1], lines[i + 1][:-1]
        # 流分隔符。
        if linei == stream_logo:
            # 将上一个流写入结果，并剔除空流。
            if resulti:
                results.append(resulti)
            # 重置此次分析的流。
            i, resulti = i + 1, []
            continue
        tempi, tempj = handle_line(linei), handle_line(linej)
        resulti.append(Message.build_mespair(tempi[0], tempi[1], tempj[0], tempj[1]))
        i += 2
    if resulti:
        results.append(resulti)
    return results
