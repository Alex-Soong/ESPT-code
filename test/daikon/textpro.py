from unittest import TestCase
from daikon.textpro import Message, build_message_seqs


class MessageTest(TestCase):
    def setUp(self):
        self.data = [
            Message.build_mespair('A', ['a1', 'a2'], 'B', []),
            Message.build_mespair('A', ['a1', 'a2'], 'B', ['b1', 'b2']),
            Message.build_mespair('A', ['a1'], 'C', []),
            Message.build_mespair('B', ['a1', 'a2'], 'B', []),
            Message.build_mespair('B', ['b1', 'b2'], 'A', ['a1', 'a2']),
            'A'
        ]

    def test_eq(self):
        self.assertTrue(self.data[0] == self.data[1])
        self.assertFalse(self.data[0] == self.data[2])
        self.assertFalse(self.data[0] == self.data[3])
        self.assertFalse(self.data[1] == self.data[4])
        self.assertFalse(self.data[1] == self.data[5])
        self.assertTrue(self.data[0] in [self.data[1], self.data[2]])
        self.assertFalse(self.data[3] in [self.data[1], self.data[2]])
        self.assertFalse(self.data[4] in [self.data[1], self.data[2]])


def test_build_message_seqs():
    pass


if __name__ == '__main__':
    test_build_message_seqs()
    # testmain()
