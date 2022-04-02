from typing import Deque

from src.command import Command
from src.exceptionhandler import ExceptionHandler, ExceptionPair


def execute_commands(commands: Deque[Command], exception_handler: ExceptionHandler):
    while len(commands) > 0:
        command = commands.popleft()
        try:
            command.execute()
        except Exception as exc:
            pair = ExceptionPair(source=command, exception=exc)
            exception_handler.handle(pair)
