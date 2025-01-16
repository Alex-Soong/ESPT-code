from collections import deque
from automata.common import Transition, Transducer


class Esptia(Transducer):
    def build_esptia(self, messages, level, limit):
        poll = 0
        reds = {self.q0}
        for messagei in messages:
            now = self.q0
            now.poll += 1
            for messagej in messagei:
                fresh = Transition(messagej, now)
                temp, build = self.build_transition(fresh)
                now = temp
            poll += 1
            if poll < limit:
                continue
            self._slim_esptia(reds, level)
            poll = 0
        if poll != 0:
            self._slim_esptia(reds, level)
        self._replan_logo()

    def _slim_esptia(self, reds, level):
        blues = self._gather_blue(reds)
        while blues:
            bluei = blues.pop()
            flag = False
            for redi in reds:
                if {beforebi.begin for beforebi in bluei.before} & {beforeri.begin for beforeri in redi.before}:
                    break
                if self._compatible_test(redi, bluei, level) or self._compatible_test(bluei, redi, level):
                    self._mesh_esptia((redi, bluei))
                    flag = True
                    break
            if not flag:
                reds.add(bluei)
            blues = self._gather_blue(reds)

    def _mesh_esptia(self, pair):
        leaves = deque([pair])
        while leaves:
            redi, bluei = leaves.popleft()
            if redi == bluei:
                continue
            redi.poll += bluei.poll
            for beforeb in bluei.before:
                beforeb.end = redi
                redi.before.add(beforeb)
            for afterb in bluei.after:
                flag = False
                for afterr in redi.after:
                    if (afterr.give, afterr.reap) == (afterb.give, afterb.reap):
                        flag = True
                        afterr.poll += afterb.poll
                        afterr.minors.extend(afterb.minors)
                        afterb.end.before.discard(afterb)
                        self.transitions.discard(afterb)
                        if afterr.end != afterb.end:
                            leaves.append((afterr.end, afterb.end))
                        break
                if not flag:
                    afterb.begin = redi
                    redi.after.add(afterb)
            self.states.discard(bluei)
