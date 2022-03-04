"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: cli.py
Description: Command line interface.
"""
from typing import Dict, Callable, Tuple

from interface import Interface

class CommandNotFound(KeyError):
    pass

class _CommandManager:
    _commands: Dict[str, Callable] = {}

    @classmethod
    def _resolve_command(cls, name):
        if name in cls._commands:
            return cls._commands[name]
        elif name in BUILTIN_COMMANDS:
            return BUILTIN_COMMANDS[name]
        else:
            raise CommandNotFound(name)

    @classmethod
    def _get_command(cls, name):
        try:
            command = cls._resolve_command(name)
        except CommandNotFound:
            command = None
        finally:
            return command 

    @classmethod
    def get(cls, name):
        """
        Get a command.
        """
        return cls._get_command(name)

    @classmethod
    def add(cls, name, callback):
        cls._commands[name] = callback

class _CommandLineInterfaceBase:
    def __init__(self):
        self._aliases: Dict[str, str] = {}
        self._commands: Dict[str, Callable] = {}

    def addAlias(self, name, value):
        if self._resolve_command(name):
            raise ValueError(f"alias cannot overwrite '{name}'")

        self._aliases[name] = value

    def remAlias(self, name):
        del self._aliases[name]
        
    def addCommand(self, name, callback):
        self._commands[name] = callback

    def remCommand(self, name):
        del self._commands[name]

    def _resolve_name(self, name):
        imax = 500
        i = 0
        while name in self._aliases and name != self._aliases[name] and i < imax:
            i += 1
            name = self._aliases[name]
        return name

    def _resolve_command(self, name):
        return _CommandManager.get(name)

    def process(self, line: str) -> None: 
        split = line.split(" ")

        if len(split) == 0:
            return

        name = split[0]

        if len(split) > 1:
            args = tuple(split[1:])
        else:
            args = tuple()

        name = self._resolve_name(name)
        command = self._resolve_command(name)

        if command is None:
            return self.onUnknownCommand(name)

        self.runCommand(name, command, args)

    def runCommand(self, name, command, args):
        try:
            command.__call__(self, args)
        except Exception as exc:
            return self.onException(exc.__class__, exc, exc.__traceback__, name, command, args)

    def onUnknownCommand(self, name: str) -> None:
        return self.output(f"unknown command '{name}'")

    def onException(self, type_, exc, tb, name, command, args):
        return self.output(f"{type_.__qualname__}: {exc}")

class ICommandLineInterface(Interface, _CommandLineInterfaceBase):
    def output(self, message: str) -> None: ...

class CommandLineInterface(ICommandLineInterface):
    """
    The default command line interface.
    """
    def output(self, message: str):
        print(message)

def _alias(cli: ICommandLineInterface, args: Tuple):
    if len(args) != 2:
        return cli.output("Usage: alias <name> <value>")

    name = args[0]
    value = args[1]

    try:
        cli.addAlias(name, value)
    except ValueError:
        # Name already exists.
        return cli.output(f"name '{name}' already exists")

def _echo(cli: ICommandLineInterface, args: Tuple):
    return cli.output(" ".join(args))

BUILTIN_COMMANDS = {
    "alias": _alias,
    "echo": _echo
}

if __name__ == "__main__":
    CLI = CommandLineInterface()
    CLI.process("alias test echo")
    CLI.process("test hello world")