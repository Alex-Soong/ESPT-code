import time
from sklearn.model_selection import KFold
from daikon.textpro import Message, build_message_seqs
from automata.common import Transducer


class TransducerTestWithoutMessage:
    @staticmethod
    def test_build_pretree():
        seqi1 = [
            Message.build_mespair('I1', ['name', 'player'], 'O1', ['OK++']),
            Message.build_mespair(chr(955), [], 'O2', ['Please Input']),
            Message.build_mespair('I3', ['name: Ll321'], chr(955), []),
            Message.build_mespair('I4', ['player: name'], '04', ['PWD']),
            Message.build_mespair('I5', ['asdfgh'], chr(955), [])
        ]
        seqi2 = [
            Message.build_mespair('I1', ['name', 'manager'], 'O1', ['ALLOW+']),
            Message.build_mespair(chr(955), [], 'O2', ['Please Input']),
            Message.build_mespair('I3', ['name: Ll321'], '04', ['PWD']),
            Message.build_mespair('I5', ['asdfgh'], '05', ['WRONG'])
        ]
        result = Transducer('login')
        result.build_pretree([seqi1, seqi2])
        # 直接输出判断，集合元素确定循环顺序不容易实现。
        for i in result.q0.after:
            print('q0的离开转移：', i)
            print('q0的离开转移的离开状态：', i.end)
            for j in i.end.after:
                print('q1的离开转移：', j)
                print('q1的离开转移的离开状态：', j.end)
                for k in j.end.after:
                    print('q2的离开转移：', k)
                    print('q2的离开转移的离开状态：', k.end)
                    for l1 in k.end.after:
                        print('q3的离开转移：', l1)
                        print('q3的离开转移的离开状态：', l1.end)
                        for m in l1.end.after:
                            print('q4的离开转移：', m)
                            print('q4的离开转移的离开状态：', m.end)

    @staticmethod
    def test_spt_il():
        seqi1 = [
            Message.build_mespair('I1', ['name', 'player'], 'O1', ['OK++']),
            Message.build_mespair(chr(955), [], 'O2', ['Please Input']),
            Message.build_mespair('I3', ['name: Ll321'], chr(955), []),
            Message.build_mespair('I4', ['player: wuhuwuhu'], '04', ['PWD']),
            Message.build_mespair('I5', ['asdfg'], '05', ['YES']),
            Message.build_mespair(chr(955), [], '06', ['Data']),
            Message.build_mespair('content', [], chr(955), []),
            Message.build_mespair('content', [], chr(955), []),
            Message.build_mespair('content', [], chr(955), []),
            Message.build_mespair('content', [], chr(955), []),
            Message.build_mespair('I7', ['FINISH'], 'O7', ['FREE'])
        ]
        seqi2 = [
            Message.build_mespair('I1', ['name', 'manager'], 'O1', ['OK+']),
            Message.build_mespair(chr(955), [], 'O2', ['Please Input']),
            Message.build_mespair('I3', ['name: Ll321'], chr(955), []),
            Message.build_mespair('I4', ['manager: alaala'], '04', ['PWD']),
            Message.build_mespair('I5', ['asdfg'], '05', ['NO'])
        ]
        seqi3 = [
            Message.build_mespair('I1', ['name', 'manager'], 'O1', ['OK+']),
            Message.build_mespair(chr(955), [], 'O2', ['Please Input']),
            Message.build_mespair('I3', ['name: Kk987'], chr(955), []),
            Message.build_mespair('I4', ['manager: weiwuweiwu'], '04', ['PWD']),
            Message.build_mespair('I5', ['poiuy'], '05', ['YES']),
            Message.build_mespair(chr(955), [], '06', ['Data']),
            Message.build_mespair('content', [], chr(955), []),
            Message.build_mespair('I7', ['FINISH'], 'O7', ['FREE'])
        ]
        result = Transducer('game')
        result.build_pretree([seqi1, seqi2, seqi3])
        result.slim_pretree(1)
        result.learn_probabilities()
        result.tell_transducer()


class TransducerTest:
    def __init__(self, text, protocol):
        project_path = '/home/song/codess/ESPT-code/'
        self.text_road = project_path + 'info/handle/'
        self.svg_road = project_path + 'info/picsvg/'
        self.test_road = project_path + 'info/test/automata/common/'
        self.messages = build_message_seqs(f'{self.text_road}{text}.txt')
        self.handletext = text
        self.protocol = protocol

    def seek_state(self):
        transducer = Transducer(self.protocol)
        transducer.build_pretree(self.messages)
        print(transducer.seek_state())
        print(transducer.seek_state(3))
        print(transducer.seek_state(transducer.state_number - 1))
        print(transducer.seek_state(300))

    def draw_svg(self):
        transducer = Transducer(self.protocol)
        transducer.build_pretree(self.messages)
        transducer.depict_poll(f'{self.svg_road}{self.handletext}-draw-svg-1.svg')
        transducer.slim_pretree(2)
        transducer.depict_poll(f'{self.svg_road}{self.handletext}-draw-svg-2.svg')
        transducer.finish_pretree()
        transducer.depict_poll(f'{self.svg_road}{self.handletext}-draw-svg-3.svg')
        transducer.learn_probabilities()
        transducer.depict(f'{self.svg_road}{self.handletext}-draw-svg-4.svg')

    def build_esptiail(self, check_text, level):
        poll, messagel = 0, len(self.messages)
        if messagel < 5:
            print('测试数据集过小，无法进行测试。')
            return
        kfold = KFold(n_splits = min(10, messagel), shuffle = False)
        with open(f'{self.test_road}{check_text}.txt', 'w') as checktext:
            checktext.write(f'Text: {self.handletext}\n\n')
            for learn_arrays, check_arrays in kfold.split(range(messagel)):
                learns, checks = [self.messages[i] for i in learn_arrays], [self.messages[i] for i in check_arrays]
                begin_time = time.time()
                transducer = Transducer(self.protocol)
                transducer.build_pretree(learns)
                transducer.slim_pretree(level)
                transducer.depict_poll(f'{self.svg_road}zoo-{self.handletext}-build-esptiail-{poll}-1.svg')
                for trani in transducer.transitions:
                    checktext.write(f'{trani.poll} => {len(trani.minors)}\n')
                transducer.finish_pretree()
                transducer.learn_probabilities()
                transducer.depict_poll(f'{self.svg_road}zoo-{self.handletext}-build-esptiail-{poll}.svg')
                end_time = time.time()
                checktext.write(f'{poll}轮: \n\tBegin: {begin_time}\n\tEnd: {end_time}\n\tSpend: {end_time - begin_time}\n')
                poll += 1

    def build_rules(self, level = 2):
        learns, checks = self.messages[0:80], self.messages[80:100]
        transducer = Transducer(self.protocol)
        transducer.build_pretree(learns)
        transducer.slim_pretree(level)
        transducer.finish_pretree()
        transducer.depict(f'{self.svg_road}{self.handletext}-build-rules.svg')

    def quality_evaluation_indicator(self, level = 2, testtext = None):
        '''
        质量评价标准测试。
        '''
        poll, messagel = 0, len(self.messages)
        if messagel < 5:
            print('测试数据集过小，无法进行测试。')
            return
        if not testtext:
            testtext = f'{self.handletext}-qei'
        with open(f'{self.test_road}{testtext}.txt', 'w') as checktext:
            checktext.write(f'Text: {self.handletext}\nLevel: {level}\n\n')
            kfold = KFold(n_splits = min(10, messagel), shuffle = False)
            for learn_arrays, check_arrays in kfold.split(range(messagel)):
                learns = [self.messages[i] for i in learn_arrays]
                checks = [self.messages[i] for i in check_arrays]
                start_time = time.time()
                transducer = Transducer(self.protocol)
                transducer.build_pretree(learns)
                transducer.slim_pretree(level)
                transducer.finish_pretree(True)
                transducer.learn_probabilities()
                transducer.depict(f'{self.svg_road}{self.handletext}-qei-{poll}.svg')
                finish_time = time.time()
                checktext.write(f'Start: {start_time}\nFinish: {finish_time}\nSpend: {finish_time - start_time}\n')
                loss_give, loss_reap = transducer.cross_entropy_loss(checks)
                checktext.write(f'loss_give: {loss_give}\nloss_reap: {loss_reap}\n')
                acc_give, acc_reap, rec_give, rec_reap = transducer.accuracy_recall(checks)
                checktext.write(f'acc_give: {acc_give}\nacc_reap: {acc_reap}\n\nrec_give: {rec_give}\nrec_reap: {rec_reap}\n')
                poll += 1
                checktext.write('##########\n')

    def build_message_by_state(self, level = 2):
        poll, messagel = 0, len(self.messages)
        kfold = KFold(n_splits = min(10, messagel), shuffle = False)
        i = 0
        for learn_arrays, check_arrays in kfold.split(range(messagel)):
            learns = [self.messages[i] for i in learn_arrays]
            checks: list[list[Message]] = [self.messages[i] for i in check_arrays]
            transducer = Transducer(self.protocol)
            transducer.build_pretree(learns)
            transducer.slim_pretree(level)
            transducer.finish_pretree()
            transducer.depict(f'{self.svg_road}{self.handletext}-bmbstate-{poll}.svg')
            for checki in checks:
                now_state = transducer.q0
                for checkj in checki:
                    givecru_check, reapcru_check = checkj.look_major()
                    giveanc_check, reapanc_check = checkj.look_minors()
                    statea = transducer.after_state(now_state, checkj)
                    after, crucial, ancillary = transducer.build_message_by_state(
                        now_state, (givecru_check, giveanc_check)
                    )
                    print(f'实际响应报文: {reapcru_check} #### {reapanc_check}')
                    if not statea or not after:
                        break
                    now_state = statea
            poll += 1


def check_main(text, protocol, level = 2, check_text = None):
    transducer = TransducerTest(text, protocol)
    transducer.seek_state()
    transducer.build_rules()
    transducer.quality_evaluation_indicator(level, check_text)
    transducer.build_message_by_state()
    transducer.build_esptiail(text, level)


if __name__ == '__main__':
    # check_main('smtp-126', 'smtp')
    check_main('live555-rtsp', 'live555')
