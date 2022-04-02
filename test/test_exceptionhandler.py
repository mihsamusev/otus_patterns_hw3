import unittest
from collections import deque
from typing import Callable
from unittest.mock import Mock

from src.app import execute_commands
from src.command import (
    Command,
    LogExceptionCommand,
    RepeatError,
    RepeatOnceCommand,
    RepeatTwiceCommand,
)
from src.exceptionhandler import (
    ExceptionHandler,
    ExceptionPair,
    LogStrategy,
    RepeatOnceStrategy,
    RepeatTwiceStrategy,
)


class FakeCommand:
    def execute(self):
        """
        I do nothing
        """
        pass


class TestExceptionHandler(unittest.TestCase):
    def test_log_exception_command_calls_logger_function(self):
        exc = ValueError()
        logger_fn = Mock()
        command = LogExceptionCommand(exc, logger_fn)
        command.execute()

        logger_fn.assert_called_once_with(exc)

    def test_log_handler_puts_log_exception_command_into_command_queue(self):
        pair = ExceptionPair(Mock(spec_set=Command), ValueError())

        command_queue = deque()
        logger_fn = Mock()
        handling_strategy = LogStrategy(command_queue, logger_fn)

        handling_strategy.handle(pair)

        self.assertTrue(len(command_queue) == 1)
        self.assertIsInstance(command_queue.popleft(), LogExceptionCommand)

    def test_exception_handler_executes_log_exception_command_from_command_queue(self):
        faulty_command = Mock(spec_set=Command)
        command_exception = IndexError("I fail")
        faulty_command.execute.side_effect = command_exception
        command_queue = deque()
        command_queue.append(faulty_command)

        logger_fn = Mock(spec_set=Callable)
        exception_handler = ExceptionHandler()
        pair = (Command, IndexError)
        exception_handler.register(*pair, LogStrategy(command_queue, logger_fn))

        execute_commands(command_queue, exception_handler)
        faulty_command.execute.assert_called_once()
        logger_fn.assert_called_once_with(command_exception)

    def test_repeat_handler_puts_same_command_into_command_queue(self):
        pair = ExceptionPair(Mock(spec_set=Command), ValueError())
        command_queue = deque()

        handling_strategy = RepeatOnceStrategy(command_queue)
        handling_strategy.handle(pair)

        self.assertTrue(len(command_queue) == 1)
        self.assertIsInstance(command_queue.popleft(), RepeatOnceCommand)

    def test_exception_handler_executes_repeat_command_from_command_queue(self):
        faulty_command = Mock(spec_set=Command)
        faulty_command.execute.side_effect = ValueError("I fail")
        command_queue = deque()
        command_queue.append(faulty_command)

        exception_handler = ExceptionHandler()
        pair = (Command, ValueError)
        exception_handler.register(*pair, RepeatOnceStrategy(command_queue))

        execute_commands(command_queue, exception_handler)
        self.assertEqual(faulty_command.execute.call_count, 2)

    def test_exception_handler_executes_repeat_then_log(self):

        faulty_command = Mock(spec_set=Command)
        faulty_command.execute.side_effect = [
            IndexError("I fail first time"),
            IndexError("I fail secood time"),
        ]
        command_queue = deque()
        command_queue.append(faulty_command)

        logger_fn = Mock(spec_set=Callable)
        exception_handler = ExceptionHandler()
        pair_1 = (Command, IndexError)
        pair_2 = (RepeatOnceCommand, RepeatError)
        exception_handler.register(*pair_1, RepeatOnceStrategy(command_queue))
        exception_handler.register(*pair_2, LogStrategy(command_queue, logger_fn))

        execute_commands(command_queue, exception_handler)
        self.assertEqual(faulty_command.execute.call_count, 2)
        logger_fn.assert_called_once()

    def test_exception_handler_executes_repeat_twice_then_log(self):

        faulty_command = Mock(spec_set=Command)
        faulty_command.execute.side_effect = [
            IndexError("I fail first time"),
            ValueError("I fail secood time"),
            IOError("I fail last time"),
        ]
        command_queue = deque()
        command_queue.append(faulty_command)

        logger_fn = Mock(spec_set=Callable)
        exception_handler = ExceptionHandler()
        pair_1 = (Command, IndexError)
        pair_2 = (RepeatTwiceCommand, RepeatError)
        pair_3 = (RepeatOnceCommand, RepeatError)
        exception_handler.register(*pair_1, RepeatTwiceStrategy(command_queue))
        exception_handler.register(*pair_2, RepeatOnceStrategy(command_queue))
        exception_handler.register(*pair_3, LogStrategy(command_queue, logger_fn))

        execute_commands(command_queue, exception_handler)
        self.assertEqual(faulty_command.execute.call_count, 3)
        logger_fn.assert_called_once()
