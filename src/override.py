"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: override.py
Description: Function overrides in python
"""
import functools
import inspect
from typing import Any, Callable, Dict, List, Union, Optional
import sys

# Placeholder for framework
def _getClassNameFromFunction(func: Callable) -> str:
    if hasattr(func, "__func__"):
        return _getClassNameFromFunction(func.__func__)
    elif hasattr(func, "func"):
        return _getClassNameFromFunction(func.func)

    if hasattr(func, "__self__"):
        return func.__self__.__class__.__qualname__

    moduleName = func.__module__
    module = sys.modules[moduleName]
    qualname = func.__qualname__
    name = func.__name__
    splits = qualname.split(".")

    if len(splits) == 1:
        # If there is only one split then
        # the function is in the module scope.
        return func.__module__ + "." + func.__name__

    obj = module
    objects = {}

    # Skip the last split (its the function itself)
    for split in splits[:-1]:
        if not hasattr(obj, split):
            continue

        obj = getattr(obj, split)
        objects[split] = obj

    cls = None
    for obj in reversed(list(objects.values())):
        if inspect.isclass(obj) and getattr(obj, name) == func:
            cls = obj
            break

    if cls is None:
        return None
    else:
        return cls.__qualname___

def _getManagerId(func: Callable) -> str:
    """
    Returns the manager id of a given function.
    """
    cls = _getClassNameFromFunction(func)
    if cls:
        return cls
    else:
        return func.__qualname__

def _getHash(types: List[type]) -> int:
    """
    Returns the hash to be used for a given list of types.
    """
    # NOTE: Alternating between adding and subtracting allows
    # for different outputs based on the ORDER of types not just
    # on the types that are included. This allows for (int, str)
    # to be different from (str, int).
    # return sum([id(t) for t in types])
    ids = [id(t) for t in types]
    acc = 0
    for i, id_ in enumerate(ids):
        if i % 2 == 0:
            acc += id_
        else:
            acc -= id_
    return acc

class _OverrideManager:
    def __init__(self, id: str):
        self.id = id
        self._overrides: Dict[str, Dict[int, Callable]] = {}

    def _addOverride(self, func: Callable) -> None:
        """
        Adds an override to the manager.
        """
        name = func.__name__
        types = list(func.__annotations__.values())
        # TODO: Remove Return annotation. 
        # TODO: Fix `self` annotation.
        #print(types)
        hash = _getHash(types)
        if name in self._overrides:
            self._overrides[name][hash] = func
        else:
            self._overrides[name] = {hash: func}

    def _callOverride(self, func: Callable, args: Any, kwargs: Any) -> Any:
        name = func.__name__
        types = [type(arg) for arg in args]
        hash = _getHash(types)
        override = self._overrides[name].get(hash, None)
        if override is None:
            typenames = [t.__qualname__ for t in types]
            raise TypeError("no override available for: %s" % (typenames))
        return override.__call__(*args, **kwargs)

    def getWrapper(self, func: Callable) -> Callable:
        """
        Get an override wrapper for a given func.
        """
        self._addOverride(func)

        def wrapper(*args, **kwargs):
            return self._callOverride(func, args, kwargs)

        wrapper.__doc__ = func.__doc__
        wrapper.__name__ = func.__name__
        wrapper.__qualname__ = func.__qualname__
        wrapper.__override__ = func
        wrapper.__manager__ = self
        return wrapper

class _OverrideManagerFactory:
    _managers: Dict[str, _OverrideManager] = {}

    @classmethod
    def getManager(cls, func: Callable) -> _OverrideManager:
        id = _getManagerId(func)

        if id in cls._managers:
            return cls._managers[id]

        else:
            manager = _OverrideManager(id)
            cls._managers[id] = manager
            return manager

def override(func: Callable) -> Callable:
    """
    Override decorator.
    """
    return _OverrideManagerFactory.getManager(func).getWrapper(func)

if __name__ == '__main__':
    @override
    def test(x: int):
        print("int!", x)

    @override
    def test(x: str):
        print("string!", x)

    @override
    def test(x: int, y: str):
        print("int str")

    @override
    def test(x: str, y: int):
        print("str int")

    k = list(_OverrideManagerFactory._managers.keys())[0]
    manager = _OverrideManagerFactory._managers[k]
    overrides = manager._overrides
    print(_OverrideManagerFactory._managers)
    print(overrides)

    test(2)
    test("testing")
    print()

    test(2, "hello")
    test("hello", 2)

