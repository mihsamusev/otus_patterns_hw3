from typing import Callable, Deque, Protocol


class Command(Protocol):
    def execute(self):
        """
        Execute command
        """


class EnqueueFrontCommand:
    """
    Puts another command into the command queue
    """

    def __init__(self, command_queue: Deque[Command], command: Command):
        self._command = command
        self._command_queue = command_queue

    def execute(self):
        self._command_queue.appendleft(self._command)


class LogExceptionCommand:
    """
    Command that logs exception raised by execution of other command
    """

    def __init__(self, exception: Exception, logger_fn: Callable):
        self._exception = exception
        self._logger_fn = logger_fn

    def execute(self):
        self._logger_fn(self._exception)


class RepeatOnceCommand:
    """
    Command that repeats the command that has thrown an execution
    """

    def __init__(self, command: Command):
        self._command = command

    def execute(self):
        try:
            self._command.execute()
        except Exception as msg:
            raise RepeatError(msg)


class RepeatTwiceCommand(RepeatOnceCommand):
    def __init__(self, command: Command):
        super().__init__(command)


class RepeatError(Exception):
    """
    Thrown on unsuccessful command repeat
    """

    pass
