"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: framework.py
Description: the core module of the framework.
All modules depend on this.
"""
import os
from typing import Any, Callable, Dict, List, Optional, Union
import importlib.util
import sys
from types import ModuleType

#### Struct ####
class Struct:
    """
    A structure can contain any data.
    Although with one exception:
    There can not be any duplicate values.
    e.g.
    >>> s = Struct()
    >>> s.key = someValue
    >>> s.key2 = someValue
    ValueError
    """
    def __init__(self, **kwargs):
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def __str__(self):
        s = "<Struct("
        for arg in self.__dict__:
            s += f"{arg}={getattr(self, arg)}, "
        s = s[:len(s)-2] + ")>"
        return s

    def __repr__(self):
        return str(self.__dict__)

    def __contains__(self, other):
        if not isinstance(other, str):
            raise TypeError("Struct cannot contain non-string")

        return other in self.__dict__

    def __getitem__(self, item):
        # Get item returns the key from a given value.
        vals = list(self.__dict__.values())
        index = vals.index(item)

        if item not in vals or index < 0:
            raise ValueError(item)
        else:
            keys = list(self.__dict__.keys())
            return keys[index]

    def __call__(self, item):
        # Calling returns the value from a given key.
        if item not in self.__dict__:
            raise KeyError(item)

        return self.__dict__[item]

    def __setattr__(self, attr, value):
        if value in self.__dict__.values():
            raise ValueError(f"Duplicate value '{value}' from key '{attr}'")

        self.__dict__[attr] = value

#### Enum ####
def enum(*args: Any) -> Struct:
    """
    Takes a list of string keys and returns a 
    enum-like Struct object which automatically creates
    integer values for the enum keys.
    """
    data = {}
    counter = 0

    # Give each arg an integer value and return a struct.
    for arg in args:
        data[arg] = counter
        counter += 1

    return Struct(**data)

#### Modules ####

# All framework modules are stored here.
modules: Dict[str, ModuleType] = {}

def getModule(name: str) -> Optional[ModuleType]:
    """
    Gets a framework module.
    If the specified module is not available then None is returned.
    """
    fname = f"rilowframework.{name}"
    if name in modules:
        return modules[name]
    elif fname in modules:
        return modules[fname]
    elif name == "framework":
        return sys.modules[__name__]
    else:
        return None

def moduleLoaded(name: str) -> bool:
    """
    Returns True if a given module is loaded.
    """
    return name in modules or f"rilowframework.{name}" in modules or name == "framework"

##### Event System #####

Events = enum(
    # FRAMEWORK_LOAD is called when the framework finishes loading.
    # Args:
    #   modules -> A dict of loaded framework modules (not finalized)
    # NOTE: This should only be triggered once (it is used internally)
    # This event is special in that it can trigger without a
    # on() call if a framework module has a onFrameworkLoad() function
    # inside of its global namespace. When this event is triggered
    # all framework modules then have access to the framework namespace. 
    # Do not attempt to access the framework namespace before this
    # event is triggered.
    "FRAMEWORK_LOAD",

    # FRAMEWORK_FINALIZE is called when the framework is finalizing.
    # NOTE: This is different from when python is finalizing. This event
    # isn't guarenteed to be run. It's more reliant to use __del__ for python
    # finalization in order to do finalizing.
    "FRAMEWORK_FINALIZE",

    # MODULE_LOAD is called when a framework module is loaded. 
    # Args: 
    #   module -> The module that was loaded.
    "MODULE_LOAD",

    # EVENT is called whenever an event is triggered.
    # Args:
    #   name -> The events name
    #   *args **kwargs -> The events arguments.
    "EVENT",
)

# For events that are used which are not a part of 
# the events enum we need to generate a new code for them given a string.
# In order to reduce the time it takes to get the code of an event they
# are cached here with {name: code}.
_eventCache: Dict[str, int] = {}

# Event registry.
# Each key is an event code and each value is 
# a list of callables registered to the event.
_registry: Dict[int, List[Callable]] = {}

def _getEventCode(event: Union[str, int]) -> int:
    """
    Returns a code for a given event.
    """
    if isinstance(event, int):
        return event
    elif not isinstance(event, str):
        raise TypeError("event must be string or int")

    if event in _eventCache:
        return _eventCache[event]
    elif event in Events:
        return Events(event)
    else:
        # Because we are generating a new code here, we want to make sure
        # that this code doesn't overlap with any existing codes (in Events)
        # and we want to cache the result inside _eventsCache
        code = 0
        for i, c in enumerate(event):
            n = ord(c)-97 # 97 = ord("a") => The lowest ord value. Subtract this to have smaller integers.
            if i % 2 == 0:
                code += n
            else:
                code -= n

        while code in Events.__dict__.values() or code in _eventCache.values():
            code += 1

        # Add to cache
        _eventCache[event] = code
        return code

def _getEventName(event: int) -> str:
    """
    Returns an events name from its code.
    """
    if event in Events.__dict__.values():
        return Events[event]
    
    elif event in _eventCache.values():
        # Get the key at the same index as the index of the event in the values list.
        return list(_eventCache.keys())[list(_eventCache.values()).index(event)]

    else:
        raise ValueError("Cannot find name for event '%s'" % event)

def on(event: Union[str, int], function: Callable) -> None:
    """
    Calls `function` when event `event` is triggered.
    """
    code = _getEventCode(event)
    
    # Add to events registry
    if code in _registry:
        _registry[code].append(function)
    else:
        _registry[code] = [function]

def onOnce(event: Union[str, int], function: Callable) -> None:
    """
    Calles `function` when event `event` is triggered. When the 
    function is called it is removed from the registry.
    """
    function.__FRAMEWORK_ON_ONCE__ = True
    return on(event, function)

def remove(event: Union[str, int], function: Callable) -> None:
    """
    Remove a callable from an events register.
    """
    code = _getEventCode(event)

    if code in _registry and function in _registry[code]:
        _registry[code].remove(function)
        if len(_registry[code]) == 0:
            del _registry[code]

def do(event: Union[str, int], *args, **kwargs) -> None:
    """
    Performs an event. Calling all registered functions.
    """
    code = _getEventCode(event)

    # Avoid recursion.
    if event != Events.EVENT:
        do(Events.EVENT, _getEventName(event), event, *args, **kwargs)

    # Do nothing if there is nothing registered
    if code not in _registry:
        return

    toRemove = []

    for function in _registry[code]:
        function.__call__(*args, **kwargs)

        if hasattr(function, "__FRAMEWORK_ON_ONCE__"):
            toRemove.append(function)

    for function in toRemove:
        remove(event, function)

##### Framework Loading #####

def _onFrameworkLoad(loaded_modules: Dict[str, ModuleType]) -> None:
    """
    Internal method called when the framework is done loading.
    This is actually registered to Events.FRAMEWORK_LOAD
    Do not call directly.
    """
    modules.update(loaded_modules)

    for name, module in loaded_modules.items():

        # inject framework into modules
        vars(module)["framework"] = sys.modules[__name__]

        # Events.FRAMEWORK_LOAD
        if hasattr(module, "onFrameworkLoad"):
            module.onFrameworkLoad()

    # We wait untill all modules are finalized before doing MODULE_LOAD events.
    for name in loaded_modules:
        do(Events.MODULE_LOAD, name)
    return



# os.path.dirname gets the directory the framework is in.
# next(os.walk()) gets the first iteration of os.walk
# [2] grabs the file list from the os.walk iteration.
files = next(os.walk(os.path.dirname(__file__)))[2]

# Unfinalized modules are loaded into this dict and then on Events.FRAMEWORK_LOAD
# (_onFrameworkLoad) they are then finalized and loaded into the `modules` dict.
_loaded_modules: Dict[str, ModuleType] = {}

for file in files:
    if not file.endswith(".py") or file == "framework.py":
        continue

    moduleName, _ = os.path.splitext(file)
    
    path = os.path.join(os.path.dirname(__file__), file)

    if not os.path.exists(path):
        raise FileNotFoundError(path)

    spec = importlib.util.spec_from_file_location(moduleName, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    _loaded_modules[moduleName] = module

# Cleanup namespace
del file, files, module, moduleName, path, spec, _

# After all of the modules have been loaded (framework is initialized)
# call the onFrameworkLoad function.
on(Events.FRAMEWORK_LOAD, _onFrameworkLoad)
do(Events.FRAMEWORK_LOAD, _loaded_modules)

# Clean up namespace
del _loaded_modules

#### Done loading framework ###
