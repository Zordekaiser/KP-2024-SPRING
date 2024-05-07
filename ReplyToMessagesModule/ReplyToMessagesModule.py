from sc_kpm import ScModule
from .ReplyToMessagesAgent import ReplyToMessagesAgent


class ReplyToMessagesModule(ScModule):
    def __init__(self):
        super().__init__(ReplyToMessagesAgent())
