import numpy
from collections import deque, defaultdict
from pygraphviz import AGraph
from z3 import Solver, Int, sat
from automata.rules import Rule
from daikon.textpro import Message
from daikon.rulepro import build_rules, check_rules


class State:
    '''
    状态机的状态。
    '''

    def __init__(self, logo, poll = 1):
        self.logo = logo
        # 进入该状态的转移。
        self.before: set[Transition] = set()
        # 离开该状态的转移。
        self.after: set[Transition] = set()
        # 到达该状态的协议的数量。
        self.poll = poll
        # 在该状态结束的概率。
        self.endingp = -1

    def __str__(self):
        # return f'<State{{{self.logo}}}({self.poll} -> {self.endingp:.3f})>'
        return f'<State{{{self.logo}}}({self.poll})>'

    __repr__ = __str__


class Transition:
    '''
    状态机的转移。
    '''

    def __init__(self, mespair, begin = None, end = None, poll = 1):
        # 输入报文的请求头、输出报文的响应码。
        self.give, self.reap = mespair.look_major()
        # 报文参数集合，可以存在重复元素，并不会影响Daikon系统的判断。
        # 推断完毕规则之后应该释放，其占用的内存极大。
        # :type: list[tuple[list[str]]]。
        self.minors = [mespair.look_minors()]
        # 进入状态。
        self.begin: State = begin
        # 离开状态。
        self.end: State = end
        # 经过该转移的报文计数。
        self.poll: int = poll
        # 转移的规则。
        # :type: list。
        self.rules: list[Rule] = []
        # 经过该转移的概率。
        self.passp = -1

    def __str__(self):
        # return (f'Transition: {self.begin} --> ({self.poll} -> {self.passp:.3f}) {self.give} / {self.reap} '
        #         f'%{self.minors}% --> {self.end}')
        return f'Transition: {self.begin} --> ({self.poll}) {self.give} / {self.reap}  -> {self.end}'

    __repr__ = __str__

    def build_rules(self, diyrule = False):
        '''
        创建该转移的规则。
        '''
        self.rules = build_rules(self.minors, diyrule)

    def check_rules(self, gives, reaps, flag = False):
        '''
        验证是否符合规则。
        :param flag: 是否仅验证输入报文，是则为True；默认为False，即验证请求和响应报文。
        :type gives: list[str]。
        :type reaps: list[str]。
        :rtype: bool。
        '''
        if not self.minors:
            return True
        return True if not self.rules else check_rules(gives, reaps, self.rules, self.minors[0], flag)

    def tell_rules(self):
        '''
        提供rules的字符串格式。
        '''
        result = []
        for rulei in self.rules:
            temp = rulei.tell()
            if temp:
                result.append(temp)
        return '\n'.join(result)

    def build_message_rule(self, gives):
        '''
        根据输入报文和当前转移的规则，推断输出报文。
        :param gives: 输入报文的次要字段。
        :type gives: list[str]。
        :return: 下一个状态，响应报文的主要、次要字段。
        '''

        def mesh_rule_type31(arrays):
            '''
            利用并查集合并形如x == y的等式的元素。
            :type arrays: list[list[str]]。
            :return: 每个元素对应并查集中的父节点、最终的并查集。
            :rtype: dict[str, str], dict[str, list[str]]。
            '''
            seniors = {}
            for arrayi, arrayj in arrays:
                seniors[mesh_rule_type31_ufseek(arrayi, seniors)] = mesh_rule_type31_ufseek(arrayj, seniors)
            catalogs = defaultdict(list)
            for seniori in seniors:
                catalogs[mesh_rule_type31_ufseek(seniors[seniori], seniors)].append(seniori)
            return seniors, catalogs

        def mesh_rule_type31_ufseek(now, seniors):
            '''
            并查集查找算法。
            '''
            if now != seniors.setdefault(now, now):
                seniors[now] = mesh_rule_type31_ufseek(seniors[now], seniors)
            return seniors[now]

        if not self.rules:
            return self.end, self.reap, []
        minorbl, minoral = len(self.minors[0][0]), len(self.minors[0][1])
        if len(gives) != minorbl:
            print('common.Transition.build_message_rule: 输入报文参数数量与最小报文参数数量不符')
            return self.end, self.reap, []
        # 该次请求报文字段，作为参数。
        minorbs = {f'a{bi}': gives[bi] for bi in range(minorbl)}
        # 生成的内容信息。
        minoras: dict[str, None | str | int] = {f'b{ai}': None for ai in range(minoral)}

        # 验证请求报文的字段。
        if not self.check_rules(gives, [], True):
            print('common.Transition.build_message_rule: 请求报文验证不通过')
            return None, None, []

        rules31, rules32 = [], []
        rules5 = []
        # 变量是否确定了值。
        sure = {}
        for rulei in self.rules:
            match rulei.kind:
                case 1:
                    # 数字等式交给方程组来解。
                    # 将其添加到方程组中，防止方程组中不含一些原值，导致Z3随即生成。例如: a0 = 1，而kind3中只有a1 - a0 = 2。
                    rules32.append(rulei.info)
                case 2:
                    # 字符串等式直接解。
                    if rulei.info[0] in minoras:
                        # 初始化全部为未确定。
                        sure[rulei.info[0]] = False
                        minoras[rulei.info[0]] = rulei.info[1]
                case 3:
                    (rules31 if rulei.info[0] else rules32).append([rulei.info[1], rulei.info[2]])
                case 5:
                    if (isinstance(rulei.info[2], int) or isinstance(rulei.info[2], numpy.int64)) and rulei.info[1].startswith('b'):
                        rules5.append(rulei.info)
        # 利用并查集确定所有可确定的字符串的值。
        rules31_senior, rules31_cata = mesh_rule_type31(rules31)
        for rulei31_senior in rules31_senior:
            if rulei31_senior in sure and not sure[rulei31_senior]:
                data = minoras[rulei31_senior]
                sure_senior = mesh_rule_type31_ufseek(rulei31_senior, rules31_senior)
                for rulei31_cata in rules31_cata[sure_senior]:
                    sure[rulei31_cata] = True
                    minoras[rulei31_cata] = data
        # 至此可以由规则推导出的字符串的值已经被确定。

        # 推断根据等式可以直接确定的数字的值，要求一方至少是请求报文的参数。
        for rulei31, rulej31 in rules31:
            try:
                if rulei31.startswith('a') and rulej31.startswith('b') and not minoras[rulej31]:
                    minoras[rulej31] = int(minorbs[rulei31])
                elif rulei31.startswith('b') and rulej31.startswith('a') and not minoras[rulei31]:
                    minoras[rulei31] = int(minorbs[rulej31])
            except ValueError:
                pass

        # 计算数字表达式。
        # 将目前无值的变量全部设定为数字类型，即使其包含了无法由规则推断出来的字符串值。
        numbers = {minorai: Int(minorai) for minorai in minoras if not minoras[minorai]}
        # 已经确定的数字值。
        sure_numbers = {minorai: minoras[minorai] for minorai in minoras if
                        minoras[minorai] and isinstance(minoras[minorai], int)}
        solve = Solver()
        # 将变量添加进去。
        give_pars = {f'{minorbi}': int(minorbj) for minorbi, minorbj in minorbs.items() if minorbj.isdigit()}
        for minorbi, minorbj in minorbs.items():
            if minorbj.isdigit():
                solve.add(eval(f'{minorbi} == {minorbj}', None, give_pars))
        for rulei32 in rules32:
            solve.add(eval(f'{rulei32[0]} == {rulei32[1]}', None, numbers | give_pars | sure_numbers))
        # 将类型5的数字比较规则添加到约束中去。
        for rulei5 in rules5:
            solve.add(eval(f'{rulei5[1]} {rulei5[0]} {rulei5[2]}', None, numbers | sure_numbers))
        if solve.check() == sat:
            model = solve.model()
            for numberi, numberj in numbers.items():
                minoras[numberi] = model[numberj]
        else:
            raise Exception('common.Transition.build_message_rule: Cannot solve the equation.')

        # 根据留存的信息验证类型。
        for normi, normj in {f'b{bi}': bj for bi, bj in enumerate(self.minors[0][1])}.items():
            if normi not in minoras:
                raise Exception('common.Transition.build_message_rule: Cannot find the norm.')
            if minoras[normi] is None or (
                    (isinstance(minoras[normi], int) and isinstance(normj, str)) and not normj.isdigit()
            ):
                minoras[normi] = normj

        return self.end, self.reap, list(minoras.values())

    def check_rules_only_res(self, reaps):
        '''
        仅仅验证响应报文的字段。
        '''
        if not self.minors:
            return True
        reapl = len(reaps)
        if reapl != len(self.minors[0][1]):
            return True
        csv_translate = str.maketrans('\r\n,"', '   \'')
        feeds = {f'b{i}': reaps[i].translate(csv_translate) for i in range(reapl)}
        for rulei in self.rules:
            match rulei.kind:
                case 1 | 2:
                    if rulei.info[0] not in feeds:
                        return True
                    return feeds[rulei.info[0]] == str(rulei.info[1])
                case 3:
                    try:
                        result = eval(f'{rulei.info[1]} == {rulei.info[2]}', None, feeds)
                    except NameError:
                        return True
                    except TypeError:
                        try:
                            result = eval(f'{rulei.info[1]} == {rulei.info[2]}', None, {
                                feedi: int(feedj) for feedi, feedj in feeds.items() if feedj.isdigit()
                            })
                        except TypeError:
                            return True
                    return result
                case 4:
                    if rulei.info[0] not in feeds:
                        return True
                    return feeds[rulei.info[0]] in rulei.info[1]
                case 5:
                    if rulei.info[1] not in feeds:
                        return True
                    feedi = feeds[rulei.info[1]]
                    if isinstance(rulei.info[2], numpy.int64) or isinstance(rulei.info[2], int):
                        return feedi.isdigit() and eval(f'{feedi} {rulei.info[0]} {rulei.info[2]}')
                    return eval(f'\'{feedi}\' {rulei.info[0]} \'{rulei.info[2]}\'')
                case 6:
                    return True
        return True

    def guess_request_by_rule(self, reaps):
        '''
        根据响应报文和当前转移的规则，推断请求报文。
        '''

        def mesh_rule_type31(arrays):
            seniors, catalogs = {}, defaultdict(list)
            for arrayi, arrayj in arrays:
                seniors[mesh_rule_type31_ufseek(arrayi, seniors)] = mesh_rule_type31_ufseek(arrayj, seniors)
            for seniori in seniors:
                catalogs[mesh_rule_type31_ufseek(seniors[seniori], seniors)].append(seniori)
            return seniors, catalogs

        def mesh_rule_type31_ufseek(now, seniors):
            if now != seniors.setdefault(now, now):
                seniors[now] = mesh_rule_type31_ufseek(seniors[now], seniors)
            tempresult = seniors[now]
            return tempresult

        if not self.rules:
            return self.end, self.give, []
        minorbl, minoral = len(self.minors[0][0]), len(self.minors[0][1])
        if len(reaps) != minoral:
            return self.end, self.give, []
        minoras = {f'b{ai}': reaps[ai] for ai in range(minoral)}
        minorbs: dict[str, None | str | int] = {f'a{bi}': None for bi in range(minorbl)}
        # 验证响应报文字段。
        if not self.check_rules_only_res(reaps):
            return None, None, []

        rules31, rules32 = [], []
        rules5 = []
        # 变量是否确定了值。
        sure = {}
        for rulei in self.rules:
            match rulei.kind:
                case 1:
                    rules32.append(rulei.info)
                case 2:
                    if rulei.info[0] in minorbs:
                        sure[rulei.info[0]] = False
                        minorbs[rulei.info[0]] = rulei.info[1]
                case 3:
                    (rules31 if rulei.info[0] else rules32).append([rulei.info[1], rulei.info[2]])
                case 5:
                    if (isinstance(rulei.info[2], int) or isinstance(rulei.info[2], numpy.int64)) and rulei.info[1].startswith('a'):
                        rules5.append(rulei.info)

        rules31_senior, rules31_cata = mesh_rule_type31(rules31)
        for rulei31_senior in rules31_senior:
            if rulei31_senior in sure and not sure[rulei31_senior]:
                data = minorbs[rulei31_senior]
                sure_senior = mesh_rule_type31_ufseek(rulei31_senior, rules31_senior)
                for rulei31_cata in rules31_cata[sure_senior]:
                    sure[rulei31_cata], minorbs[rulei31_cata] = True, data

        for rulei31, rulej31 in rules31:
            try:
                if rulei31.startswith('b') and rulej31.startswith('a') and not minorbs[rulej31]:
                    minorbs[rulej31] = int(minoras[rulei31])
                elif rulei31.startswith('a') and rulej31.startswith('b') and not minorbs[rulei31]:
                    minorbs[rulei31] = int(minoras[rulej31])
            except ValueError:
                pass

        numbers, solve = {minorbi: Int(minorbi) for minorbi in minorbs if not minorbs[minorbi]}, Solver()
        sure_numbers = {minorbi: minorbs[minorbi] for minorbi in minorbs if
                        minorbs[minorbi] and isinstance(minorbs[minorbi], int)}
        give_pars = {f'{minorbi}': int(minorbj) for minorbi, minorbj in minoras.items() if minorbj.isdigit()}
        for minorbi, minorbj in minoras.items():
            if minorbj.isdigit():
                solve.add(eval(f'{minorbi} == {minorbj}', None, give_pars))
        for rulei32 in rules32:
            solve.add(eval(f'{rulei32[0]} == {rulei32[1]}', None, numbers | give_pars | sure_numbers))
        for rulei5 in rules5:
            solve.add(eval(f'{rulei5[1]} {rulei5[0]} {rulei5[2]}', None, numbers | sure_numbers))
        if solve.check() == sat:
            model = solve.model()
            for numberi, numberj in numbers.items():
                minorbs[numberi] = model[numberj]
        else:
            return self.end, self.give, []

        # 根据留存的信息验证类型。
        for normi, normj in {f'a{ai}': aj for ai, aj in enumerate(self.minors[0][0])}.items():
            if normi not in minorbs:
                raise Exception('test.automata.sptia.guess_request_by_rule: Cannot find the norm.')
            if minorbs[normi] is None or (
                    (isinstance(minorbs[normi], int) and isinstance(normj, str)) and not normj.isdigit()
            ):
                minorbs[normi] = normj

        return self.end, self.give, list(minorbs.values())


class Transducer:
    '''
    状态机。
    '''

    def __init__(self, protocol):
        # 状态机描述的协议。
        self.protocol: str = protocol
        # 起始状态。
        self.q0: State = State(0, 0)
        # 该状态机的所有状态。
        self.states: set[State] = {self.q0}
        # 该状态机的所有转移。
        self.transitions: set[Transition] = set()
        # 状态机的所有输入报文标志。
        self.sigma = set()
        # 状态机的所有输出报文标志。
        self.gamma = set()
        # 当前状态节点计数。
        self.state_number = 1

    def __str__(self):
        return f'Transducer of protocol: {self.protocol}'

    __repr__ = __str__

    def tell_transducer(self):
        '''
        输出状态机详情，不在__str__中实现。
        '''
        for transitioni in self.transitions:
            print(transitioni)
            print('\t', transitioni.minors, '\n')
        # haves = {havei.logo: False for havei in self.states}
        # for afteri in now_state.after:
        #     haves[now_state.logo] = True
        #     print(afteri)
        #     if afteri.end and not haves[afteri.end.logo]:
        #         self.print_transducer(afteri.end)
        #     elif not afteri.end:
        #         raise Exception('automata/common/print_transducer 离开状态为None!')

    def build_transition(self, fresh):
        '''
        在状态机中添加一个转移。
        :param fresh: 新增的转移。
        :type fresh: Transition。
        :return: 新增转移的离开状态。
        :rtype: State，是否创建了新的转移。
        '''
        # 状态机已经存在相同的转移 -> 查找进入状态的离开转移。
        for trani in fresh.begin.after:
            if (trani.give, trani.reap) == (fresh.give, fresh.reap):
                trani.poll += 1
                trani.end.poll += 1
                # 将次要字段添加到列表中。
                trani.minors.extend(fresh.minors)
                return trani.end, False
        # 状态机不存在相同的转移。
        fresh.begin.after.add(fresh)
        if fresh.end:
            fresh.end.before.add(fresh)
        else:
            statei = State(self.state_number)
            self.state_number += 1
            statei.before.add(fresh)
            fresh.end = statei
            self.states.add(statei)
        self.transitions.add(fresh)
        # 处理输入和输出报文标志。
        self.sigma.add(fresh.give)
        self.gamma.add(fresh.reap)
        if not fresh.give or not fresh.reap:
            raise Exception('automata/common/build_transition 参数携带的报文存在None!')
        return fresh.end, True

    def off_transition(self, old):
        '''
        TODO: 存在的意义？
        从状态机中删除转移。
        :param old: 待删除的转移。
        :type old: Transition。
        '''
        old.begin.after.discard(old)
        old.end.before.discard(old)
        self.transitions.discard(old)
        del old

    def build_pretree(self, arrays):
        '''
        根据报文序列构建前缀树状态机。
        :param arrays: 报文序列。
        :type arrays: list[list[Message]]。
        '''
        # arrayi是包含Message的列表。
        for arrayi in arrays:
            now = self.q0
            now.poll += 1
            # arrayj是Message。
            for arrayj in arrayi:
                fresh = Transition(arrayj, now)
                now, temp = self.build_transition(fresh)

    def _compatible_test(self, red, blue, level):
        '''
        判断两个节点是否兼容。
        ∀b'满足τ(b, i) = (o, b')，如果∃r'满足τ(r, i) = (o, r')，那么r和b是包容的。
        :type red, blue: State。
        :return: 是否兼容。
        '''
        if not level:
            return True
        result = False
        for afterb in blue.after:
            result = False
            for aftera in red.after:
                if (aftera.give, aftera.reap) == (afterb.give, afterb.reap):
                    result = self._compatible_test(aftera.end, afterb.end, level - 1)
                    break
            if not result:
                return False
        return result

    def _mesh_states(self, pair: tuple[State, State]):
        '''
        合并状态pair[1]到pair[0]中。
        :param pair: 两个状态构成的元组，约定为(red, blue)。将blue合并到red中，仅保留red状态，
        :type pair: tuple[State, State]。
        :return: 合并后的red状态。
        '''
        # 使用双向列表，便于双向弹出。
        leaves = deque([pair])
        red, blue = leaves[0]
        while leaves:
            red, blue = leaves.popleft()
            # 更新red的报文计数。
            red.poll += blue.poll
            # 处理blue的进入转移，将这些转移的输出状态设置为red。
            for beforeb in blue.before:
                beforeb.end = red
                red.before.add(beforeb)
            # 需要分类处理，因为可能状态b包容状态a，而非默认的状态a包容状态b。
            for afterb in blue.after:
                # 标志位：afterb是否被afterr包含。
                flag = False
                for afterr in red.after:
                    if (afterr.give, afterr.reap) == (afterb.give, afterb.reap):
                        flag = True
                        afterr.poll += afterb.poll
                        # 合并应该选用.extend()方法。
                        afterr.minors.extend(afterb.minors)
                        afterb.end.before.discard(afterb)
                        self.transitions.discard(afterb)
                        leaves.append((afterr.end, afterb.end))
                        break
                # 如果状态b包容状态a，那么可能出现剩余的b的离开转移，将这些转移的起点全部设置成red状态。
                if not flag:
                    afterb.begin = red
                    red.after.add(afterb)
            self.states.discard(blue)
        return red

    def slim_pretree(self, level):
        '''
        化简前缀树。
        :param level: 化简的维度。
        '''
        reds: set[State] = {self.q0}
        blues = self._gather_blue(reds)
        while blues:
            blue: State = blues.pop()
            flag = False
            for red in reds:
                # 如果存在red，满足red和blue是兄弟节点，则说明red和blue不应该合并。
                if {beforebi.begin for beforebi in blue.before} & {beforeri.begin for beforeri in red.before}:
                    break
                if self._compatible_test(red, blue, level) or self._compatible_test(blue, red, level):
                    self._mesh_states((red, blue))
                    flag = True
                    break
            if not flag:
                reds.add(blue)
            # 此处可能更新了reds += blue，导致兄弟节点之间的合并。
            blues = self._gather_blue(reds)
        self._replan_logo()

    def finish_pretree(self, diyrule = False):
        '''
        完全化前缀树。
        '''
        for transitioni in self.transitions:
            transitioni.build_rules(diyrule)
            # 推断完rules之后应该释放minors，但是为了验证次要字段的长度以及作为转移的记忆元素，保留0号元素。
            del transitioni.minors[1:]

    @staticmethod
    def _gather_blue(reds, reds_aft = None):
        '''
        设置blue节点集合。
        '''
        if not reds_aft:
            reds_aft = reds
        blues = set()
        for redi_aft in reds_aft:
            for trani in redi_aft.after:
                if trani.end not in reds:
                    blues.add(trani.end)
        return blues

    def _replan_logo(self):
        '''
        重新规划状态机状态节点的标志。
        '''
        poll, lines = 0, [self.q0]
        while poll < len(lines):
            for afteri in lines[poll].after:
                if afteri.end not in lines:
                    lines.append(afteri.end)
            poll += 1
        self.state_number = poll
        for statei, statej in enumerate(lines):
            statej.logo = statei

    def learn_probabilities(self):
        '''
        行为概率计算。
        '''
        for statei in self.states:
            pass_poll = 0
            for trani in statei.after:
                pass_poll += trani.poll
                trani.passp = round(float(trani.poll) / statei.poll, 3)
            statei.endingp = round(float(statei.poll - pass_poll) / statei.poll, 3)

    def cross_entropy_loss(self, arrays: list[list[Message]]):
        '''
        关于输入报文主要标志和输出报文主要标志的交叉损失函数。
        :param arrays: 测试报文列表。
        :type arrays: list[list[Message]]。
        '''

        def message_major_loss(major, give = None):
            if not give:
                fore_temp = self.give_poll(now)
                container = sigmas
            else:
                fore_temp = self.reap_poll(now, give)
                container = gammas
            foreps = [0] * len(container)
            for tempi in fore_temp:
                foreps[container.index(tempi)] = fore_temp[tempi]
            if sum(foreps):
                foreps = [forepi / sum(foreps) for forepi in foreps]
            facts = [0] * len(container)
            if major in container:
                facts[container.index(major)] = 1
            return sum([(foreps[i] - facts[i]) ** 2 for i in range(len(foreps))])

        sigmas, gammas = list(self.sigma), list(self.gamma)
        sigmas.sort()
        gammas.sort()
        loss_sigmas, loss_gammas = [], []
        for arrayi in arrays:
            now = self.q0
            loss_sigmai, loss_gammai = [], []
            for messi in arrayi:
                # Message类的主要字段。
                givei, reapi = messi.look_major()
                loss_sigmai.append(message_major_loss(givei))
                loss_gammai.append(message_major_loss(reapi, give = givei))
                now, flag = self.after_state(now, messi)
                if not now:
                    break
            loss_sigmas.append(sum(loss_sigmai) / len(loss_sigmai) if loss_sigmai else 0)
            loss_gammas.append(sum(loss_gammai) / len(loss_gammai) if loss_gammai else 0)
        if not loss_sigmas or not loss_gammas:
            return -1, -1
        return round(sum(loss_sigmas) / len(loss_sigmas), 4), round(sum(loss_gammas) / len(loss_gammas), 4)

    def accuracy_recall(self, arrays):
        '''
        计算准确率和召回率（覆盖率）。
        准确率Accuracy：在所有样本中，结果预测正确（实际正确认为正确 + 实际错误认为错误）的概率。
        召回率Recall：即覆盖率。在真正正确（实际正确认为正确 + 实际正确认为错误）的样本中，实际正确认为正确的样本所占比例。
        在此处，实现为：
            准确率：在各TCP流中，通过Daikon预测并以最大概率转移的样本和未通过Daikon预测的样本占总样本的比例。
            覆盖率：样本实际运行的反应是否包含于ESPT预测的反应区间中。
        :param arrays: 测试报文列表。
        :type arrays: list[list[Message]]。
        '''

        def message_accuracy_recall(major, give = None):
            result_acc, result_rec = 0, 0
            if not give:
                # 针对now的离开转移tran构成的集合{tran.give}，统计{tran.give}对应的{tran.poll}之和。
                fore_temp = self.give_poll(now)
            else:
                # 针对now的输入标志为give的离开转移tran构成的集合{tran.reap}，统计{tran.reap}对应的{tran.poll}之和。
                fore_temp = self.reap_poll(now, give)
            if major in fore_temp:
                result_rec = 1
                # accuracy找概率最大值。
                # 考虑到Daikon次要字段的验证，如果不是概率最大值对应的转移，则判断是否被该转移的Daikon refuse。
                if major == list(fore_temp.keys())[0]:
                    result_acc = 1
                    return result_acc, result_rec
            return result_acc, result_rec

        acc_gives, acc_reaps, rec_gives, rec_reaps = [], [], [], []
        for arrayi in arrays:
            now = self.q0
            flag = True
            acc_givei, acc_reapi, rec_givei, rec_reapi = [], [], [], []
            for messi in arrayi:
                # Message类的主要字段。
                givei, reapi = messi.look_major()
                acc_givei_temp, rec_givei_temp = message_accuracy_recall(givei)
                acc_reapi_temp, rec_reapi_temp = message_accuracy_recall(reapi, give = givei)
                acc_givei.append(acc_givei_temp if flag else 0)
                rec_givei.append(rec_givei_temp)
                acc_reapi.append(acc_reapi_temp if flag else 0)
                rec_reapi.append(rec_reapi_temp)
                now, flag = self.after_state(now, messi)
                if not now:
                    break
            acc_gives.append(round(sum(acc_givei) / len(acc_givei), 4) if acc_givei else 0)
            acc_reaps.append(round(sum(acc_reapi) / len(acc_reapi), 4) if acc_reapi else 0)
            rec_gives.append(round(sum(rec_givei) / len(rec_givei), 4) if rec_givei else 0)
            rec_reaps.append(round(sum(rec_reapi) / len(rec_reapi), 4) if rec_reapi else 0)
        return (
            round(sum(acc_gives) / len(acc_gives), 4) if acc_gives else 0,
            round(sum(acc_reaps) / len(acc_reaps), 4) if acc_reaps else 0,
            round(sum(rec_gives) / len(rec_gives), 4) if rec_gives else 0,
            round(sum(rec_reaps) / len(rec_reaps), 4) if rec_reaps else 0
        )

    @staticmethod
    def give_poll(now):
        '''
        在当前状态，针对每个输入报文对应的离开转移，统计经过的报文的数量。即对每个give，统计poll的和。
        :param now: 当前状态。
        :return: 每个输入报文主要字段对应的转移的总数，由其构成字典。
        :rtype: dict[str, int]。
        '''
        results = defaultdict(int)
        if not now:
            return results
        for trani in now.after:
            results[trani.give] += trani.poll
        results = sorted(results.items(), key = lambda resulti: (resulti[1], resulti[0]), reverse = True)
        return dict(results)

    @staticmethod
    def reap_poll(now, give):
        '''
        根据当前状态的输入报文，统计输出报文标志对应的离开转移的数量。
        :param now: 当前状态。
        :param give: 输入报文主要标志。
        :rtype: dict[str, int]。
        '''
        results = {}
        if not now:
            return results
        for trani in now.after:
            # 不可能输入报文与输出报文同时相等。
            if trani.give == give:
                results[trani.reap] = trani.poll
        results = sorted(results.items(), key = lambda resulti: (resulti[1], resulti[0]), reverse = True)
        return dict(results)

    @staticmethod
    def after_state(now: State, mess):
        if not now:
            return None, False
        majorb, majora = mess.look_major()
        minorsb, minorsa = mess.look_minors()
        for trani in now.after:
            if (trani.give, trani.reap) == (majorb, majora):
                return trani.end, trani.check_rules(minorsb, minorsa)
        return None, False

    def depict(self, pic_text):
        '''
        画此状态机的SVG。
        :param pic_text: SVG路径，包含.svg后缀。
        '''
        picture = AGraph(rankdir = 'LR', directed = True)
        for trani in self.transitions:
            begin, end = trani.begin, trani.end
            picture.add_edge(
                f'q{begin.logo}:{begin.endingp}', f'q{end.logo}:{end.endingp}',
                label = f'{trani.give}/{trani.reap}:{trani.passp}\n{trani.tell_rules()}'
            )
        for statei in self.states:
            if not statei.logo:
                picture.add_node(f'q{statei.logo}:{statei.endingp}', shape = 'doublecircle', penwidth = 2)
            else:
                picture.add_node(f'q{statei.logo}:{statei.endingp}', penwidth = 2)
        picture.layout(prog = 'dot')
        picture.draw(pic_text)

    def seek_state(self, logo = 0):
        '''
        获取状态q_logo。
        :param logo: 状态的编号。
        '''
        if logo >= self.state_number:
            return None
        for statei in self.states:
            if statei.logo == logo:
                return statei
        return None

    def build_message_by_transition(self, norm_tran: Transition, gives: tuple):
        '''
        按照转移来构建响应报文。
        :param norm_tran: 依据的转移。
        :param gives: 请求报文，包含主要字段和次要字段。
        :return: 下一个状态，响应报文的主要次要字段。
        '''
        if norm_tran not in self.transitions:
            return None, None, []
        crucial, ancillary = gives[0], gives[1]
        if norm_tran.give != crucial:
            return None, None, []
        # 此处不验证请求报文的格式是否正确，由Transition类处理。
        return norm_tran.build_message_rule(ancillary)

    def build_message_by_state(self, norm_state: State | int, gives: tuple):
        '''
        按照状态来构建响应报文。
        :param norm_state: 依据的状态。
        :param gives: 请求报文，包含主要字段和次要字段。
        :return: 下一个状态，响应报文的主要次要字段。
        '''
        if isinstance(norm_state, int):
            norm_state = self.seek_state(norm_state)
        if norm_state not in self.states:
            return None, None, []
        crucial, ancillary = gives[0], gives[1]
        nominee: None | Transition = None
        for transi in norm_state.after:
            if transi.give == crucial:
                # 对于存在多个离开转移含有相同的请求报文主要字段时，选取概率最大的一个。
                if not nominee or (nominee and transi.poll > nominee.poll):
                    nominee = transi
                # 此处不验证请求报文的格式是否正确，由Transition类处理。
        if nominee:
            return nominee.build_message_rule(ancillary)
        return None, None, []

    def depict_poll(self, pic_text):
        '''
        画此状态机的SVG。
        :param pic_text: SVG路径，包含.svg后缀。
        '''
        picture = AGraph(rankdir = 'LR', directed = True)
        for trani in self.transitions:
            begin, end = trani.begin, trani.end
            picture.add_edge(
                f'q{begin.logo}:{begin.poll}', f'q{end.logo}:{end.poll}',
                label = f'{trani.give}/{trani.reap}:{trani.poll}\n{trani.tell_rules()}'
            )
        for statei in self.states:
            if not statei.logo:
                picture.add_node(f'q{statei.logo}:{statei.poll}', shape = 'doublecircle', penwidth = 2)
            else:
                picture.add_node(f'q{statei.logo}:{statei.poll}', penwidth = 2)
        picture.layout(prog = 'dot')
        picture.draw(pic_text)

    def guess_req_by_res(self, norm_state: State | int, give, reaps: tuple):
        if norm_state not in self.states:
            return None, None, []
        crucial, ancillary = reaps[0], reaps[1]
        for transi in norm_state.after:
            if (transi.give, transi.reap) == (give, reaps[0]):
                return transi.guess_request_by_rule(ancillary)
        return None, None, []
