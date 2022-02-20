"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: cvar.py
Description: Console Variables.
"""
from typing import Any, Callable, TypeVar, Union
from types import FunctionType
from inspect import signature

from override import override

class _CVarBase:
    def __init__(self, name: str, helpString: str, callback: FunctionType):
        self.name = name
        self.helpString = helpString
        self.callback = callback 

    def isConCommand(self) -> bool:
        return isinstance(self, ConCommand)

    def isConVar(self) -> bool:
        return isinstance(self, ConVar)

    def execute(self, *args) -> None:
        raise NotImplementedError

class ConVar(_CVarBase):
    def __init__(self, name: str, helpString: str, callback: FunctionType, value: Any):
        _CVarBase.__init__(self, name, helpString, callback)

        self.value = value
        self.defaultValue = value

    def revert(self):
        self.setValue(self.defaultValue)

    def setValue(self, value: Any) -> None:
        old = self.value
        self.value = value
        self.callback.__call__(self, old, self.value)

    def execute(self, *args) -> None:
        value = " ".join(args) 
        self.setValue(value)

    def getValue(self) -> Any:
        return self.value

    def getString(self) -> str:
        return str(self.value)

    def getInt(self) -> int:
        try:
            return int(self.value)
        except:
            try:
                return int(float(self.value))
            except:
                pass

        raise TypeError("cannot convert to int")

    def getFloat(self) -> float:
        return float(self.value)

class ConCommand(_CVarBase):
    def __init__(self, name: str, helpString: str, callback: FunctionType):
        _CVarBase.__init__(self, name, helpString, callback)

        self._paramcount = len(signature(self.callback).parameters)

    def execute(self, *args) -> None:
        paramcount = len(args)
        
        # Combine args.
        new_args = []

        for i, arg in enumerate(args):
            i += 1
            if i > self._paramcount:
                new_args.append(tuple([(new_args.pop())] + list(args[i-1:])))
            else:
                new_args.append(arg)

        args = tuple(new_args)
        del new_args, i, arg

        if len(args) != self._paramcount:
            raise TypeError("bad param count")

        self.callback.__call__(*args)
    


CVarType = Union[ConVar, ConCommand]

def NULL_CALLBACK(cvar, old, new): pass

@override
def _new_convar(name: str, helpString: str, callback: FunctionType):
    cvar = ConCommand(name, helpString, callback)
    return cvar

@override
def _new_convar(name: str, helpString: str, value: int):
    return _new_convar(name, helpString, value, NULL_CALLBACK)

@override
def _new_convar(name: str, helpString: str, value: int, callback: FunctionType):
    cvar = ConVar(name, helpString, callback, value)
    return cvar

class _ConVarManager:
    """
    Manages all convars.
    `cvar` references an instance
    of this object.

    Do not instantiate. Do not access directly.
    Use `cvar` instead.
    """
    def __init__(self):
        self._cvars: Dict[str, CVarType] = {}

    def __call__(self, name: str, helpString: str, *args: Any) -> CVarType:
        cvar = _new_convar(name, helpString, *args)
        self.register(cvar)
        return cvar

    def register(self, cvar: CVarType) -> None:
        """
        Registers a cvar into the manager.
        """
        self._cvars[cvar.name] = cvar

    def get(self, name: str, raiseIfNotFound: bool=False) -> CVarType:
        if name not in self._cvars:
            if raiseIfNotFound:
                raise TypeError("CVar %s not found" % name)
            return _dummycvar
        return self._cvars[name]

# Create a single instance of the convar manager.
cvar = _ConVarManager()

# Create the dummycvar Used by cvar.get()
# (not registered.)
_dummycvar = ConCommand("dummy", "", NULL_CALLBACK)

if __name__ == "__main__":
    def test(args, arg2):
        print(args, arg2)

    def onchange(cvar, old, new):
        print(cvar, old, new)

    cvar("test", "", test)
    cvar("testvalue", "", 1)
    cvar("testvalue2", "", 0, onchange)

    t = cvar.get("test")
    t.execute("test", "test2", "test3")
    t2 = cvar.get("testvalue")
    t2.execute("test2")
    t3 = cvar.get("testvalue2")
    t3.execute("test3")

    # Should recieve the dummy cvar
    t4 = cvar.get("testing123testing123")
    print(t4, t4.name)