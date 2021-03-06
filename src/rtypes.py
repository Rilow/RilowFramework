"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: rilowtypes.py
Description: Helpful classes/functions for types.
"""
import operator
import math
import sys
from typing import Dict, Set, Callable, Optional, Type, Tuple, Any, T

COMPARISONS: Dict[str, str] = {
    # Comparison operators
    "__lt__": "<", # x<y
    "__le__": "<=", # x<=y
    "__gt__": ">", # x>y
    "__ge__": ">=", # x>=y
    "__eq__": "==", # x==y
    "__ne__": "!=", # x!=y
}

OPERATIONS: Dict[str, str] = {
    # Operation operators
    "__add__": "+", # x+y
    "__sub__": "-", # x-y
    "__mul__": "*", # x*y
    "__pow__": "**", # x**y
    "__div__": "/", # x/y
    "__truediv__": "/", # x/y
    "__floordiv__": "//", # x//y
    "__mod__": "%", # x%y
    "__matmul__": "@", # x@y
    "__lshift__": "<<", # x<<y
    "__rshift__": ">>", # x>>y
    "__and__": "&", # x&y
    "__xor__": "^", # x^y
    "__or__": "|", # x|y

    "__divmod__": "divmod()",
}

# Right Operation Operators (__radd__)
RIGHT_OPERATIONS: Dict[str, str] = {}

# Augmented Operation Operators (__iadd__)
AUGMENTED_OPERATIONS: Dict[str, str] = {}

# All operation operators can be made into right and augmented operators
for method, operand in OPERATIONS.items():
    augment = "__i" + method[2:]
    augmentoperand = operand + "="
    right = "__r" + method[2:]
    RIGHT_OPERATIONS[right] = operand
    AUGMENTED_OPERATIONS[augment] = augmentoperand

UNARY_OPERATIONS: Dict[str, str] = {
    "__pos__": "+", # +x
    "__neg__": "-", # -x
    "__invert__": "~", #~x
}

MAGIC_METHODS: Set[str] = {
    "__call__", # x()
    "__getitem__", # x[slice]
    "__setitem__", # x[slice] = y
    "__delitem__", # del x[slice]
    "__missing__", # x[slice] -> KeyError -> x.__missing__(slice)
    "__iter__", # for y in x
    "__reversed__", # reversed(x)
    "__contains__", # y in x
    "__enter__", # with x
    "__exit__", # with x: ... -> x.__exit__(exc_type, exc_value, traceback)
}

# These are magic methods that should not be re-wrapped by the class
# and should not type check.
TYPE_CONVERSION_METHODS: Set[str] = {
    "__str__", # str(x)
    "__repr__", # repr(x)
    "__int__", # int(x)
    "__float__", # float(x)
    "__complex__", # complex(x)
    "__oct__", # oct(x)
    "__hex__", # hex(x)
    "__index__", # for index/slicing
    "__bool__", # bool(x) Python3.x
    "__nonzero__", # bool(x) Python2.x
    "__dir__", # dir(x)
    "__format__", # str.format(x) -> x.__format__(str)
    "__hash__", # hash(x)
    "__sizeof__", # sys.getsizeof(x)
    "__abs__", # abs(x)
    "__round__", # round(x, n)
    "__floor__", # math.floor(x)
    "__ceil__", # math.ceil(x)
    "__trunc__", # math.trunc(x)
    "__len__", #  len(x)
    "__bytes__", # bytes(x)
}

ATTRIBUTE_METHODS: Set[str] = {
    "__getattr__", # getattr(x, y) || missing x.y
    "__setattr__", # setattr(x, y, z) || x.y = z
    "__delattr__", # delattr(x, y) || del x.y
    "__getattribute__", # x.y
    "__get__", # x
    "__set__", # x = y
    "__delete__" # del x
}

MAGIC_METHOD_TO_FUNCTION: Set[Callable] = {
    "__getattr__": getattr,
    "__setattr__": setattr,
    "__delattr__": delattr,
    "__bytes__": bytes,
    "__len__": len,
    "__trunc__": math.trunc,
    "__ceil__": math.ceil,
    "__floor__": math.floor,
    "__round__": round,
    "__abs__": abs,
    "__sizeof__": sys.getsizeof,
    "__hash__": hash,
    "__dir__": dir,
    "__nonzero__": bool,
    "__bool__": bool,
    "__hex__": hex,
    "__oct__": oct,
    "__float__": float,
    "__int__": int,
    "__complex__": complex,
    "__str__": str,
    "__repr__": repr,
    "__reversed__": reversed,

    # These require lambdas because they are not simple function calls like func(x)
    "__call__": lambda x, *args, **kwargs: x.value.__call__(*args, **kwargs),
    "__getitem__": lambda x, item: x.value.__getitem__(item),
    "__setitem__": lambda x, item, value: x.value.__setitem__(item, value),
    "__delitem__": lambda x, item: x.value.__delitem__(item),
    "__iter__": lambda x: tuple(y for y in x.value.__iter__())
}

TYPEWRAPPER_IGNORED_ATTRIBUTES: Set[str] = {
    "__getattr__",
    "__setattr__",
    "__delattr__",
    "__getattribute__",
    "__get__",
    "__set__",
    "__delete__",
    "__str__",
    "__repr__",
}

# Clean namespace
del method, operand, augment, augmentoperand, right

# Merge collections
OPERATIONS.update(COMPARISONS)
OPERATIONS.update(RIGHT_OPERATIONS)
OPERATIONS.update(AUGMENTED_OPERATIONS)
OPERATIONS.update(UNARY_OPERATIONS)

MAGIC_METHODS = MAGIC_METHODS.union(TYPE_CONVERSION_METHODS)
MAGIC_METHODS = MAGIC_METHODS.union(ATTRIBUTE_METHODS)

MAGIC_NAMES = set(OPERATIONS.keys()).union(MAGIC_METHODS)

# Wrapped Operations are those which re-wrap return values with
# the type wrapper class.
WRAPPED_OPERATIONS = set(AUGMENTED_OPERATIONS.keys())

WRAPPED_METHODS = set()

# ALL_OPERATIONS can be used on TypeWrapper.ALLOWED_OPERATIONS to signify that all operations are allowed.
ALL_OPERATIONS = MAGIC_NAMES.difference(TYPEWRAPPER_IGNORED_ATTRIBUTES)

# COPY_OPERATIONS_ONCE can be used and will copy all operations present in the value onto the classes
# ALLOWED_OPERATIONS.
COPY_OPERATIONS_ONCE = 0

# COPY_OPERATIONS can be used to copy operations present in the value onto the instance, thus the copy
# is done for every instance rather than once for the class in COPY_OPERATIONS_ONCE
COPY_OPERATIONS = 1

def doOperation(op: str, x: Any, y: Optional[Any]=None) -> Any:
    if y is None:
        if op == "+": return +x
        elif op == "-": return -x
        elif op == "~": return ~x
        else: raise TypeError(f"unknown operation {op}")

    if op == "+": return x + y
    elif op == "-": return x - y
    elif op == "*": return x * y
    elif op == "**": return x ** y
    elif op == "/": return x / y
    elif op == "//": return x // y
    elif op == "%": return x % y
    elif op == "@": return x @ y
    elif op == "<<": return x << y
    elif op == ">>": return x >> y
    elif op == "&": return x & y
    elif op == "^": return x ^ y
    elif op == "|": return x | y
    elif op == "<": return x < y
    elif op == ">": return x > y
    elif op == "<=": return x <= y
    elif op == ">=": return x >= y
    elif op == "==": return x == y
    elif op == "!=": return x != y
    else: raise TypeError(f"unknown operation {op}")

class _TypeWrapperMeta(type):
    """
    Do not use this meta class directly you WILL run into errors.
    Used internally by TypeWrapper. And should only be used by TypeWrapper.
    """
    @classmethod
    def _getAllowedOperations(cls, self):
        klass = self.__class__
        if klass.ALLOWED_OPERATIONS != COPY_OPERATIONS and klass.ALLOWED_OPERATIONS != COPY_OPERATIONS_ONCE:
            return

        valuetype = self.value.__class__

        # Replace the instances or the classes ALLOWED_OPERATIONS depending on the mode.
        if klass.ALLOWED_OPERATIONS == COPY_OPERATIONS:
            obj = self
        else: # COPY_OPERATIONS_ONCE
            obj = klass

        obj.ALLOWED_OPERATIONS = []

        for attr in dir(valuetype):
            if attr in MAGIC_NAMES and attr not in TYPEWRAPPER_IGNORED_ATTRIBUTES:
                obj.ALLOWED_OPERATIONS.append(attr)

    @classmethod
    def _getOperationWrapper(cls, attr: str, func: Optional[Callable], _default: bool=False) -> Callable:
        """
        Returns an operation wrapper function for a class subclassing TypeWrapper as defined in OPERATIONS.
        Used internally. Do not call.
        """
        def operationwrapper(self, other: Optional[Any]=None) -> Any:
            """
            Internal operation wrapper.
            """
            if self.ALLOWED_OPERATIONS == COPY_OPERATIONS or self.ALLOWED_OPERATIONS == COPY_OPERATIONS_ONCE:
                cls._getAllowedOperations(self)

            operation = OPERATIONS.get(attr, None)

            # If other is None then a unary operation was attempted.
            args = tuple() if not other else (other,)

            if attr not in self.ALLOWED_OPERATIONS and (operation and operation not in self.ALLOWED_OPERATIONS):
                right = attr in RIGHT_OPERATIONS
                return self._handle_restricted_operation(OPERATIONS[attr], *args)

            if isinstance(other, TypeWrapper):
                othervalue = other.value
            else:
                othervalue = other


            # Check if the function is defined.
            if func is None:
                if hasattr(operator, attr):
                    result = getattr(operator, attr).__call__(self.value, othervalue)
                else:
                    operand = OPERATIONS[attr]
                    if attr in RIGHT_OPERATIONS:
                        result = doOperation(operand, othervalue, self.value)
                    else:
                        result = doOperation(operand, self.value, othervalue)
            else:
                result = func.__call__(self, other)

            if attr in WRAPPED_OPERATIONS:
                return self.__class__(result)
            else:
                return result

        operationwrapper.__qualname__ = attr
        if func is not None:
            operationwrapper.__doc__ = func.__doc__
        operationwrapper.__func__ = func
        return operationwrapper

    @classmethod
    def _getMagicMethodWrapper(cls, attr: str, func: Optional[Callable], _default: bool=False) -> Callable:
        """
        Returns a magic method wrapper function for a class subclassing TypeWrapper as defined in MAGIC_METHODS.
        Used internally. Do not call.
        """
        def magicmethodwrapper(self, *args: Any, **kwargs: Any) -> Any:
            """
            Internal magic method wrapper function.
            """
            if self.ALLOWED_OPERATIONS == COPY_OPERATIONS:
                cls._getAllowedOperations(self)

            if attr not in self.ALLOWED_OPERATIONS and (attr in MAGIC_METHOD_TO_FUNCTION and MAGIC_METHOD_TO_FUNCTION[attr] not in self.ALLOWED_OPERATIONS):
                return self._handle_restricted_magic_method(attr, _default)

            if func is None and attr in MAGIC_METHOD_TO_FUNCTION:
                builtinFunc = MAGIC_METHOD_TO_FUNCTION[attr]
                result = builtinFunc(self, *args, **kwargs)
            elif func is None:
                return self._handle_restricted_magic_method(attr, False) # set default to false for "not defined" message.
            else:
                result = func.__call__(self, *args, **kwargs)

            if attr in WRAPPED_METHODS:
                return self.__class__(result)
            else:
                return result


        magicmethodwrapper.__qualname__ = attr
        if func is not None:
            magicmethodwrapper.__doc__ = func.__doc__
        magicmethodwrapper.__func__ = func
        return magicmethodwrapper

    def __new__(cls: Type, name: str, bases: Tuple, attrs: Dict[str, Any]) -> Type:
        """
        Create a new TypeWrapper subclass.
        """
        klass = type.__new__(cls, name, bases, attrs)

        typewrapper = klass if "TypeWrapper" not in globals() else TypeWrapper

        for name in MAGIC_NAMES:
            if name in OPERATIONS and name not in TYPEWRAPPER_IGNORED_ATTRIBUTES:
                _default = name in attrs
                wrapper = cls._getOperationWrapper(name, getattr(klass, name, None), _default)
                setattr(klass, name, wrapper)
            elif name in MAGIC_METHODS and name not in TYPEWRAPPER_IGNORED_ATTRIBUTES:
                _default = name in MAGIC_METHODS
                wrapper = cls._getMagicMethodWrapper(name, getattr(klass, name, None), _default)
                setattr(klass, name, wrapper)

        # For every attribute we create wrappers on operations and magic methods.
        for attr in attrs:
            func = attrs[attr]

            # If the attribute is a magic name and there is a NEWLY DEFINED function eg. overriding TypeWrapper method,
            # and that said method is not in ALLOWED_OPERATIONS then add it.
            if klass.ALLOWED_OPERATIONS != COPY_OPERATIONS and attr in MAGIC_NAMES and getattr(typewrapper, attr, None) != func and attr not in klass.ALLOWED_OPERATIONS:
                # Add operand if available otherwise add the attribute.
                klass.ALLOWED_OPERATIONS.append(OPERATIONS.get(attr, attr))

            if attr in OPERATIONS:
                attrs[attr] = cls._getOperationWrapper(attr, func)
                continue
            elif attr in MAGIC_METHODS:
                attrs[attr] = cls._getMagicMethodWrapper(attr, func)
                continue


        return klass

class TypeWrapper(metaclass=_TypeWrapperMeta):
    ALLOWED_OPERATIONS = []

    def __init__(self, value: T=None, type: Type[T]=None):
        # If type is none then do not type restrict the value.
        self.type: Type[T] = type
        self.value: T = value

    def _handle_restricted_operation(self, operand: str, other: Optional[Any]=None, right: bool=False) -> None:
        """
        This is called internally by _TypeWrapperMeta when a operation is attempted that
        is not allowed.
        """
        qualname = self.__class__.__qualname__
        otherqualname = other.__class__.__qualname__
        if other is None:
            s = f"'{qualname}'"
        elif right:
            s = f"'{otherqualname}' and '{qualname}'"
        else:
            s = f"'{qualname}' and '{otherqualname}'"

        if other is None:
            t = "unary type"
        else:
            t = "operand type(s) for"

        raise TypeError(f"unsupported {t} {operand}: {s}")

    def _handle_restricted_magic_method(self, name: str, default: bool=False) -> None:
        """
        This is called internally by _TypeWrapperMeta when a magic method is attempted to be 
        called which is not allowed to be.
        """
        if default:
            raise TypeError(f"could not call magic method '{name}'")
        else:
            raise TypeError(f"type '{self.__class__.__qualname__}' doesn't define {name}")

    # Because __str__ is defined by `object` we need to overwrite it.
    def __str__(self):
        return str(self.value)

    def __getattr__(self, attr):
        # Called on missing attributes. Will attempt to return the attribute of the value.
        r = getattr(self.value, attr, None)

        if not r:
            raise AttributeError(f"'{self.value.__class__.__qualname__}' object has no attribute '{attr}'")
        return r

if __name__ == "__main__":
    class MyTypeWrapper(TypeWrapper):
        ALLOWED_OPERATIONS = ["__add__", "__setitem__", "__getitem__", "__delitem__", "__sizeof__", "__iadd__"]

        def __init__(self, value):
            super().__init__(value)

        def __imul__(self, other):
            return -1

    class MyOtherTypeWrapper(TypeWrapper):
        ALLOWED_OPERATIONS = COPY_OPERATIONS_ONCE

    class MyOtherOtherTypeWrapper(TypeWrapper):
        ALLOWED_OPERATIONS = COPY_OPERATIONS

    x = MyTypeWrapper(4)
    print(x)
    print(x+2)
    x *= 2
    print(x)

    x = MyTypeWrapper([])
    x.append(2)
    print(x)

    x = MyTypeWrapper({})
    print(x)
    x["hello"] = "world"
    print(x)
    print(x["hello"])
    del x["hello"]
    print(x)
    x["hello"] = "world"
    print(x)
    x.clear()
    print(x)
    print(sys.getsizeof(x))

    x = MyTypeWrapper(2)
    print(x)

    try:
        print(+x)
        print("This should have raised an error!")
    except TypeError as exc:
        print(f"{exc.__class__.__qualname__}: {exc}")


    f = MyOtherTypeWrapper(4)
    print(f+2)
    print(MyOtherTypeWrapper.ALLOWED_OPERATIONS)

    f2 = MyOtherOtherTypeWrapper(4)
    print(f2+2)

    # Notice its still set to `1`  the value of COPY_OPERATIONS because
    # the operations are copied per instance. not per class as COPY_OPERATIONS_ONCE is (above)
    print(MyOtherOtherTypeWrapper.ALLOWED_OPERATIONS)

    f3 = MyTypeWrapper(2)
    f3 += 2
    print(f3, f3.__class__)