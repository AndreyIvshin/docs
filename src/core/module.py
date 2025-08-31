class Module:
    def __init__(self, mhtml_manipulator, logger_factory):
        self.mhtml_manipulator = mhtml_manipulator
        self.logger = logger_factory(type(self).__name__)

    def fix_mhtml(self, path):
        raise Exception("Not implemented!")
