import time
from sklearn.model_selection import KFold
from daikon.textpro import build_message_seqs
from automata.sptia import Esptia
from os_manager import sake_cata, svg_cata, check_cata, loss_minor, content_logo


class EsptiaTest:
    def __init__(self, text, protocol):
        self.check_holder = f'{check_cata}automata/sptia/'
        self.messages = build_message_seqs(f'{sake_cata}{text}.txt')
        self.handle_text = text
        self.protocol = protocol

    def build_esptia(self, check_text, level = 2, limit = 4):
        poll, messagel = 0, len(self.messages)
        if messagel < 5:
            print('测试数据集过小，无法进行测试。')
            return
        kfold = KFold(n_splits = min(10, messagel), shuffle = False)
        with open(f'{self.check_holder}{check_text}.txt', 'w') as checktext:
            checktext.write(f'Text: {self.handle_text}\nLevel: {level}\n\n')
            for learn_arrays, check_arrays in kfold.split(range(messagel)):
                learns, checks = [self.messages[i] for i in learn_arrays], [self.messages[i] for i in check_arrays]
                begin_time = time.time()
                transducer = Esptia(self.protocol)
                print(f'BeginTime: {begin_time}')
                transducer.build_esptia(learns, level, limit)
                transducer.depict_poll(f'{svg_cata}zoo-{self.handle_text}-build-esptiagl-{poll}-1.svg')
                print(f'BuildEsptia')
                for trani in transducer.transitions:
                    checktext.write(f'{trani.poll} => {len(trani.minors)}\n')
                transducer.finish_pretree()
                transducer.learn_probabilities()
                transducer.depict_poll(f'{svg_cata}zoo-{self.handle_text}-build-esptiagl-{poll}.svg')
                end_time = time.time()
                checktext.write(f'\n\tBegin: {begin_time}\n\tEnd: {end_time}\n\tSpend: {end_time - begin_time}\n')
                poll += 1

    def quality_evaluation_indicator(self, check_text, level=2, limit=4):
        poll, messagel = 0, len(self.messages)
        if messagel < 5:
            print('测试数据集过小，无法进行测试')
            return
        with open(f'{self.check_holder}{check_text}.txt', 'w') as checktext:
            kfold = KFold(n_splits = min(10, messagel), shuffle = False)
            checktext.write(f'Text: {self.handle_text}\nLevel: {level}\n\n')
            for learn_arrays, check_arrays in kfold.split(range(messagel)):
                learns, checks = [self.messages[i] for i in learn_arrays], [self.messages[i] for i in check_arrays]
                start_time = time.time()
                checktext.write(f'\tStart: {start_time}\n')
                transducer = Esptia(self.protocol)
                transducer.build_esptia(learns, level, limit)
                transducer.finish_pretree()
                transducer.learn_probabilities()
                finish_time = time.time()
                checktext.write(f'\tFinish: {finish_time}\n\tSpend: {finish_time - start_time}\n')
                loss_give, loss_reap = transducer.cross_entropy_loss(checks)
                checktext.write(f'loss_give: {loss_give}\nloss_reap: {loss_reap}\n')
                acc_give, acc_reap, rec_give, rec_reap = transducer.accuracy_recall(checks)
                checktext.write(f'acc_give: {acc_give}\nacc_reap: {acc_reap}\n\nrec_give: {rec_give}\nrec_reap: {rec_reap}\n')
                poll += 1

    def build_message_by_state(self, check_text, level = 2, limit = 4):
        poll, messagel = 0, len(self.messages)
        if messagel < 5:
            print('测试数据集过小，无法进行测试。')
            return
        kfold = KFold(n_splits = min(10, messagel), shuffle = False)
        with open(f'{self.check_holder}{check_text}.txt', 'w') as checktext:
            checktext.write(f'Text: {self.handle_text}\nLevel: {level}\n\n')
            for learn_arrays, check_arrays in kfold.split(range(messagel)):
                checktext.write(f'==========Poll: {poll}==========\n\n')
                # :type: list[list[Message]]。
                learns, checks = [self.messages[i] for i in learn_arrays], [self.messages[i] for i in check_arrays]
                begin_time = time.time()
                transducer = Esptia(self.protocol)
                transducer.build_esptia(learns, level, limit)
                transducer.finish_pretree()
                transducer.learn_probabilities()
                # transducer.depict(f'{svg_cata}{self.handle_text}-bms-{poll}.svg')
                end_time = time.time()
                checktext.write(f'\tBegin: {begin_time}\n\tEnd: {end_time}\n\tSpend: {end_time - begin_time}\n')
                # 下一状态预测的正确性集合。
                states_accuracy = []
                # 响应报文字段预测的正确性集合。
                majors_accuracy = []
                minors_accuracy = []
                # :type: list[Message]。
                for checki in checks:
                    now_state = transducer.q0
                    statei_accuracy, majori_accuracy, minori_accuracy = [], [], []
                    # :type: Message。
                    for checkj in checki:
                        checkb_major, checka_major = checkj.look_major()
                        checkb_minor, checka_minor = checkj.look_minors()
                        fresh_state, fresh_flag = transducer.after_state(now_state, checkj)
                        # 根据请求报文预测的下一状态、响应报文主要字段、响应报文次要字段。
                        guess_state, guess_major, guess_minor = transducer.build_message_by_state(
                            now_state, (checkb_major, checkb_minor)
                        )
                        statei_accuracy.append(fresh_state == guess_state)
                        majori_accuracy.append(guess_major == checka_major)
                        if not guess_minor or len(guess_minor) != len(checka_minor):
                            minori_accuracy.append(1)
                        else:
                            temp_minor_accuracy = [
                                checkai_minor == guessi_minor for checkai_minor, guessi_minor in zip(checka_minor, guess_minor)
                            ]
                            minori_accuracy.append(sum(temp_minor_accuracy) / len(temp_minor_accuracy))
                        if not fresh_state:
                            break
                        now_state = fresh_state
                    states_accuracy.append(sum(statei_accuracy) / len(statei_accuracy) if statei_accuracy else 1)
                    majors_accuracy.append(sum(majori_accuracy) / len(majori_accuracy) if majori_accuracy else 1)
                    minors_accuracy.append(sum(minori_accuracy) / len(minori_accuracy) if minori_accuracy else 1)
                checktext.write(f'State: {sum(states_accuracy) / len(states_accuracy) if states_accuracy else 1}\n')
                checktext.write(f'Major: {sum(majors_accuracy) / len(majors_accuracy) if majors_accuracy else 1}\n')
                checktext.write(f'Minor: {sum(minors_accuracy) / len(minors_accuracy) if minors_accuracy else 1}\n')
                poll += 1
                checktext.write(f'\n')

    def guess_req_transition(self, check_text, level = 2, limit = 4):
        poll, messagel = 0, len(self.messages)
        if messagel < 5:
            print('测试数据集过小，无法进行测试。')
            return
        kfold = KFold(n_splits = min(10, messagel), shuffle = False)
        with open(f'{self.check_holder}guessreq/{check_text}-{poll}-guess.txt', 'w') as checktext:
            with open(f'{self.check_holder}guessreq/{check_text}-{poll}.txt', 'w') as srctext:
                for learn_arrays, check_arrays in kfold.split(range(messagel)):
                    learns = [self.messages[i] for i in learn_arrays]
                    checks = [self.messages[i] for i in check_arrays]
                    transducer = Esptia(self.protocol)
                    transducer.build_esptia(learns, level, limit)
                    transducer.finish_pretree()
                    transducer.learn_probabilities()
                    for checki in checks:
                        now_state = transducer.q0
                        for checkj in checki:
                            checkb_major, checka_major = checkj.look_major()
                            checkb_minor, checka_minor = checkj.look_minors()
                            fresh_state, fresh_flag = transducer.after_state(now_state, checkj)
                            guess_state, guess_major, guess_minor = transducer.guess_req_by_res(
                                now_state, checkb_major, (checka_major, checka_minor)
                            )
                            if guess_major not in (content_logo, chr(955)):
                                if not guess_minor or len(guess_minor) != len(checka_minor):
                                    guess_minor = checkb_minor
                                guess_minor, checkb_minor = ' '.join(guess_minor), ' '.join(checkb_minor)
                                if guess_minor == loss_minor:
                                    guess_minor = ''
                                if checkb_minor == loss_minor:
                                    checkb_minor = ''
                                checktext.write(f'{guess_major} {guess_minor}\n')
                                srctext.write(f'{checkb_major} {checkb_minor}\n')
                            if not fresh_state:
                                break
                            now_state = fresh_state
                        checktext.write(f'\n##########\n')
                        srctext.write(f'\n##########\n')
                    poll += 1


def check_main(handletext, protocol, level = 2, limit = 4):
    transducer = EsptiaTest(handletext, protocol)
    # transducer.build_message_by_state(handletext, level, limit)
    # transducer.guess_req_transition(handletext, level, limit)
    transducer.build_esptia(handletext)


if __name__ == '__main__':
    check_main('smtp-126', 'smtp')
