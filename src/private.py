"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: private.py
Description: Private functions inside of classes.
"""
import inspect
import sys
from typing import Callable

class PrivateError(Exception):
    """
    Raised when trying to access a private method from outside of the allowed namespace.
    """
    pass

def private(func: Callable) -> Callable:
    """
    Makes a function/method private by blocking all
    external callers foreign to the Class/Module the
    function/method was defined in.
    """
    def wrapper(*args, **kwargs):
        if len(args) < 1:
            raise TypeError(f"{func.__qualname__} missing one required positional argument \"self\"")

        # Get self
        self = args[0]

        if not isinstance(self, object):
            # If self is not an object then raise a type error.
            raise TypeError(f"{func.__qualname__} param \"self\" must be an instance of object")

        # Get class
        cls = self.__class__

        # Get caller
        stack = inspect.stack()

        errstring = f"{func.__qualname__} is a private method and cannot be called externally"

        if len(stack) < 3:
            # There currently is less than 3 frames on the stack.
            # This usually means the call came from the module scope.
            raise PrivateError(errstring)

        # Search for callerClass
        frame = stack[2].frame

        if "self" in frame.f_locals:
            callerClass = frame.f_locals["self"].__class__
        elif "cls" in frame.f_locals:
            callerClass = frame.f_locals["cls"]
        else:
            # Most likely in module scope so compare __module__ attributes

            callerModule = frame.f_locals["__name__"]
            funcModule = func.__module__

            if callerModule != funcModule:
                raise PrivateError(errstring)

            else:
                # Can call the method
                return func.__call__(*args, **kwargs)

        # Compare class with calling class
        if cls != callerClass:
            raise PrivateError(errstring)

        else:
            return func.__call__(*args, **kwargs)

    # Copy func attributes + add some more
    wrapper.__name__ = func.__name__
    wrapper.__qualname__ = func.__qualname__
    wrapper.__doc__ = func.__doc__
    wrapper.__private__ = True # this isn't really checked by the module but is present incase others want to check.
    wrapper.__private_func__ = func # same as above, just in case
    return wrapper

if __name__ == "__main__":
    class MyPrivateClass:
        def __init__(self):
            print("inside init")

        def callPrivateMethod(self):
            print("inisde call private method")
            self.myPrivateMethod()

        @private
        def myPrivateMethod(self):
            print("inside private method")

    m = MyPrivateClass()
    print()

    m.callPrivateMethod()
    print()

    try:
        m.myPrivateMethod()
    except PrivateError as exc:
        print(f"{exc.__class__.__qualname__}: {exc}")
