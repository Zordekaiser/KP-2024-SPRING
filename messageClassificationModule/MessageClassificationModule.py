from sc_kpm import ScModule

from .MessageClassificationAgent import MessageClassificationAgent


class MessageClassificationModule(ScModule):
    def __init__(self):
        super().__init__(MessageClassificationAgent())
