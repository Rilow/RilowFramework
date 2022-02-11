"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: config.py
Description: Allows easy loading/saving of configuration files.
All modules depend on this.
"""
from abc import ABC
from typing import Any, Dict
import os
import inspect

class ConfigError(Exception): pass
class KeyNotFound(ConfigError): pass
class ParserError(ConfigError):
    def __init__(self, parser, message): 
        super().__init__(f"[{parser.__qualname__}] {message}")
class ParserLoadError(ParserError): pass
class ParserSaveError(ParserError): pass

class ConfigParser(ABC):
    """
    Abstract base class for config parsers.
    """
    def parse(config: "ConfigBase", filepath: str) -> Dict[str, Any]:
        raise NotImplementedError

    def save(config: "ConfigBase", filepath: str, data: Dict[str, Any]) -> None:
        raise NotImplementedError

class ConfigBase:
    """
    The base class for all config classes.
    """
    def __init__(self, filepath: str=None, *, parser: ConfigParser=ConfigParser, doSaving: bool=False, doLoading: bool=True, ignoreParserErrors: bool=False):
        # If parser is set to the ConfigParser ABC then use the default parser (this is used because None is reserved for NullParser)
        if parser is None:
            parser = NullParser
        elif parser == ConfigParser:
            parser = DefaultParser

        if not issubclass(parser, ConfigParser):
            raise TypeError(f"parser must be a subclass of `ConfigParser` {parser=}")

        if filepath is not None:
            if not os.path.exists(filepath):
                raise FileNotFoundError(filepath)

        # Set attributes
        set("doSaving", doSaving)
        set("parser", parser)
        set("filepath", filepath)
        set("ignoreParserErrors", ignoreParserErrors)
        set("data", {})

        if doLoading:
            get("load").__call__()

    def __str__(self):
        return str(get("data"))

    def __getattribute__(self, attr):
        # Attributes are obtained from the config data
        # note that object.__getattribute__ is used here
        # because accessing self.data directly will
        # cause recursion
        data = get("data")

        if attr not in data:
            raise KeyNotFound(attr)
        return data[attr]
    
    def __setattr__(self, attr, value):
        get("data")[attr] = value
        return

    def __getitem__(self, item):
        # Items are obtained from the classes
        # attributes but cannot be accessed directly
        # as this will call __getattribute__
        # To prevent this we use object.__getattribute__
        return get(item)

    def __setitem__(self, item, value):
        set(item, value)

    def load(self) -> None:
        """
        Load the config using the parser.
        """
        data = {}
        err = False

        try:
            data = get("parser").parse(self, get("filepath"))
        except:
            err = True

            if not get("ignoreParserErrors"):
                raise ParserLoadError(parser, f"failed to load {filepath}")

        if not err:
            set("data", data)

    def save(self) -> None:
        """
        Save the config using the parser.
        """
        if not get("doSaving"):
            return

        data = get("data")
        parser = get("parser")
        filepath = get("parser")

        try:
            parser.save(self, filepath, data)
        except:
            if not get("ignoreParserErrors"):
                raise ParserSaveError(parser, f"failed to save {filepath}, {data=}")


def _getCallerInstance() -> object:
    """
    Returns the instance who called this function.

    Used by set() and get().
    """
    # Go back two frames (once for the function that called this one and 
    # once more to go back to the instances call to get/set)
    return inspect.currentframe().f_back.f_back.f_locals["self"]


def set(attr: str, value: Any) -> None:
    """
    Helper function for `ConfigBase` do not use.

    Set an attribute of the instance.
    """
    try:
        self = _getCallerInstance()
        return object.__setattr__(self, attr, value)
    except:
        pass

    raise ConfigError(f"Could not set '{attr}' to '{value}'")

def get(attr: str) -> Any:
    """
    Helper function for `ConfigBase` do not use.

    Return an attribute of the instance.
    """
    try:
        self = _getCallerInstance()
        return object.__getattribute__(self, attr)
    except:
        pass

    raise ConfigError(f"Could not get '{attr}'")
    
        
class NullParser(ConfigParser):
    """
    The null parser does nothing.
    """
    def parse(config: ConfigBase, filepath: str) -> Dict[str, Any]:
        return {}

    def save(config: ConfigBase, filepath: str, data: Dict[str, Any]) -> None:
        return

class DefaultParser(ConfigParser):
    """
    Default parser.
    """
    def parse(config: ConfigBase, filepath: str) -> Dict[str, Any]:
        if filepath is None:
            return {}

        with open(filepath) as f:
            content = f.read()

        rawLines = content.splitlines()
        lines = []

        # remove comments / blank lines
        for line in rawLines:
            if len(line.strip()) == 0:
                continue
            elif line.startswith("//"):
                continue
            elif "//" in line:
                line = line[:line.find("//")]

            lines.append(line)

        # parse lines
        data = {}

        for line in lines:
            split = line.split("=")
            if len(split) < 2:
                continue

            key = split[0].strip()
            val = "=".join(split[1:]).strip()
            data[key] = val

        return data

    def save(config: ConfigBase, filepath: str, data: Dict[str, Any]) -> None:
        if filepath is None:
            return

        lines = []
        for key, val in data.items():
            lines.append(f"{key}={val}")

        content = "\n".join(lines)

        with open(filepath, 'w') as f:
            f.write(content)

        return

class JsonParser(ConfigParser):
    """
    Parse using json.
    """
    def parse(config: ConfigBase, filepath: str) -> Dict[str, Any]:
        if filepath is None:
            return {}

        addEmptyData = False

        with open(filepath) as f:
            content = f.read()
            if len(content.strip()) == 0:
                data = {}
                addEmptyData = True
            else:
                data = json.loads(content)

        if addEmptyData and config["doSaving"]:
            # we only want to do file writing if it is
            # explicitly enabled via doSaving
            with open(filepath, "w") as f:
                f.write("{}")

        return data

    def save(config: ConfigBase, filepath: str, data: Dict[str, Any]) -> None:
        if filepath is None:
            return

        with open(filepath) as f:
            json.dump(f, data)
        return


class Config(ConfigBase):
    pass

class MemoryConfig(ConfigBase):
    def __init__(self):
        # An in-memory config has no disk i/o so loading and saving should be disabled.
        # Doing that should be good enough but for good measure we can also use the nullparser.
        ConfigBase.__init__(self, None, parser=NullParser, doLoading=False, doSaving=False)


if __name__ == '__main__':
    t = "test.cfg"
    c = Config(t)
    j = Config(t, parser=JsonParser, ignoreParserErrors=True)
    d = Config(t, parser=None)

    print(d)
    d.test = 2
    print(d)