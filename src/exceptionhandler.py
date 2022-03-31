from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Deque, Optional, Protocol, Type

from src.command import (
    Command,
    LogExceptionCommand,
    RepeatOnceCommand,
    RepeatTwiceCommand,
)


@dataclass(frozen=True)
class ExceptionPair:
    """
    Object that is used as a key for mapping exception handlers
    """

    source: Command
    exception: Exception

    def types(self):
        """
        Create a unique key corresponding to source and exception type combo
        """
        return (self.source.__class__, self.exception.__class__)


class ExceptionHandler:
    """
    Maps command + exception pairs to exception handlers to resolve errors
    """

    def __init__(self, default_strategy: Optional[ExceptionStrategy] = None):
        self._handler_map = {}
        self._default_strategy = default_strategy

    def register(
        self,
        command_type: Type,
        exception_type: Type,
        handling_strategy: ExceptionStrategy,
    ):
        hashable = (command_type, exception_type)
        key = hash(hashable)
        self._handler_map[key] = handling_strategy

    def handle(self, pair: ExceptionPair):
        """
        Handles exception by invoking stored handlers,
        If handler is not found, try applying defauly handling strategy if it exists
        """
        key = hash(pair.types())
        handling_strategy = self._handler_map.get(key)

        if handling_strategy:
            handling_strategy.handle(pair)
        else:
            if self._default_strategy:
                self._default_strategy.handle(pair)


class ExceptionStrategy(Protocol):
    """
    Interface for concrete exception handling strategy
    """

    def handle(self, pair: ExceptionPair):
        ...


class LogStrategy:
    """
    Handles exception by queuing a logging command with the exception
    """

    def __init__(self, command_queue: Deque, logger_fn: Callable):
        self._command_queue = command_queue
        self._logger_fn = logger_fn

    def handle(self, pair: ExceptionPair):
        command = LogExceptionCommand(
            exception=pair.exception, logger_fn=self._logger_fn
        )
        self._command_queue.appendleft(command)


class RepeatOnceStrategy:
    """
    Handles exception by putting a repeater command into the queue
    """

    def __init__(self, command_queue: Deque):
        self._command_queue = command_queue

    def handle(self, pair: ExceptionPair):
        command = RepeatOnceCommand(command=pair.source)
        self._command_queue.appendleft(command)


class RepeatTwiceStrategy:
    """
    Handles exception by putting a repeater command into the queue
    """

    def __init__(self, command_queue: Deque):
        self._command_queue = command_queue

    def handle(self, pair: ExceptionPair):
        command = RepeatTwiceCommand(command=pair.source)
        self._command_queue.appendleft(command)
