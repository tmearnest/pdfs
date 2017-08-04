from abc import ABCMeta, abstractmethod

class Command(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def set_args(self, subparser):
        pass

    @abstractmethod
    def run(self, args):
        pass

    def args(self, subparsers):
        self.sp = subparsers.add_parser(self.command, help=self.help)
        self.set_args(self.sp)
        self.sp.set_defaults(func=self.run)
