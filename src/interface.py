"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: interface.py
Description: Interfaces in python.
"""
from typing import Any

class ImplementationError(Exception):
    """
    A class implementing an interface did not implement
    one of the methods of the interface.
    """
    pass

# Get the code value for ellipsis.
# NOTE: This is not constant and may change depending on
# implementation/version and is best to obtain
# directly from this function.
def _ellipsisFunctionCode(): ...
ELLIPSIS_CO_CODE = _ellipsisFunctionCode.__code__.co_code
del _ellipsisFunctionCode

_IGNORED_INTERFACE_ATTRS_ = ("__module__", "__qualname__", "__annotations__")

class _InterfaceMeta(type):
    def __new__(cls, name, bases, attrs):
        obj = type.__new__(cls, name, bases, attrs)

        if attrs.get("__qualname__", None) == "Interface":
            # Base `Interface` object
            return obj

        if bases[0] == Interface:
            # Define an interface
            _Interface_methods = [] # Methods that the interface defines to be implemented.
            _Interface_attrs = attrs.get("__annotations__", {}).copy() # Attributes that the interface defines and their types.

            for attr in attrs:
                if attr in _IGNORED_INTERFACE_ATTRS_: continue
                val = attrs[attr]

                if callable(val):
                    co_code = val.__code__.co_code
                    if co_code == ELLIPSIS_CO_CODE:
                        _Interface_methods.append(attr)

            # Interface identifier
            obj.__interface__ = True

            # Interface methods/attrs that must be implemented.
            setattr(obj, "_Interface_methods", _Interface_methods)
            setattr(obj, "_Interface_attrs", _Interface_attrs)
            return obj

        else:
            # Define an implementation
            interface = bases[0]

            if not isinterface(interface):
                raise TypeError(f"invalid interface type '{interface.__qualname__}'")

            methods = interface._Interface_methods
            implemented = [] # Implemented methods.
            interface_attrs = interface._Interface_attrs

            for attr in attrs:
                if attr in _IGNORED_INTERFACE_ATTRS_: continue

                val = attrs[attr]

                if attr in methods:
                    # Check ellipsis
                    co_code = val.__code__.co_code
                    if co_code == ELLIPSIS_CO_CODE:
                        raise ImplementationError(f"unimplemented method '{attr}'")
                    implemented.append(attr)
                    continue

                elif attr in interface_attrs:
                    if not isinstance(val, interface_attrs[attr]):
                        raise ImplementationError(f"wrong type '{type(val).__qualname__}' for attr '{attr}'")
                    continue


            if implemented != methods:
                # Not all methods have been implemented.
                missing = [attr for attr in methods if attr not in implemented]
                raise ImplementationError(f"no implementation for methods: '{missing}'")

            # Implementation
            obj.__interface__ = False
            return obj

class Interface(metaclass=_InterfaceMeta):
    def __init__(self):
        if isinterface(self):
            raise TypeError("cannot instatiate interface")

# Used by isinterface() and isimplementation()
InterfaceTypes = (Interface, _InterfaceMeta)

def isinterface(x: Any) -> bool:
    """
    Return True if `x` is an interface.
    """
    return isinstance(x, InterfaceTypes) and hasattr(x, "__interface__") and x.__interface__ is True

def isimplementation(x: Any) -> bool:
    """
    Return True if `x` is an interface implementation.
    """
    return isinstance(x, InterfaceTypes) and hasattr(x, "__interface__") and x.__interface__ is False

def _test():

    class _MyInterface(Interface):
        x: int

        def testMethod(x: int, y: int) -> int: ...

        def methodThatHasImplementation(x: int):
            return x ** 2

    try:
        m = _MyInterface()

        raise RuntimeError("no type error raised")
    except TypeError:
        pass

    class _MyImplementation(_MyInterface):
        x = 1
        def testMethod(x: int, y: int) -> int:
            return x + y

    try:
        class _MyImplementationError(_MyInterface):
            pass

        raise RuntimeError("no implementation error raised")
    except ImplementationError:
        pass

    try:
        class _MyImplementationErrorPt2(_MyInterface):
            x = "string"
            def testMethod(x: int, y: int) -> int:
                return x + y

        raise RuntimeError("no implementation error raised")
    except ImplementationError:
        pass

if __name__ == "__main__": 
    _test()