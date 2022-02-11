"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: typed.py
Description: strict typed functions in python
"""
from functools import partial as _partial
from typing import \
        _SpecialGenericAlias, _CallableGenericAlias, Any, Callable, Dict, \
        List, Tuple, Type, TypeVar, NoReturn, Optional, Union, get_origin
from types import CodeType, FunctionType, MethodType, WrapperDescriptorType
import sys

# Set this True for debug messages
__DEBUG__ = False

def _getArgNames(co: CodeType) -> List[str]:
    """
    Retruns a list of all argument names
    for a given code object.
    e.g.
    >>> def test(x: int): ...
    >>> _getArgNames(test.__code__)
    ["x"]
    """
    names = co.co_varnames
    nargs = co.co_argcount
    nkwargs = co.co_kwonlyargcount
    args = list(names[:nargs])
    kwonlyargs = list(names[nargs:nargs+nkwargs])
    return args + kwonlyargs

def _getArgs(x: Any) -> Tuple:
    """
    Returns a typing objects args value.
    This returns an empty tuple if no args are
    present.
    """
    # HACKHACK: Accessing private attribute!
    try:
        return x.__args__
    except:
        return tuple()

def _getBound(x: Any) -> Type:
    """
    Returns a typing objects bound type.
    This is used internally specifically for
    Type and TypeVar objects and will return None
    if a bound type cannot be found.
    """
    # HACKHACK: Accessing private attribute!
    try:
        return x.__bound__
    except:
        return None

def _getTypeName(x: Any) -> str:
    """
    Returns a representable string from a given type.
    """
    # typing.Any
    if x == Any:
        return "Any"

    # typing.NoReturn
    elif x == NoReturn:
        return "NoReturn"

    # typing.Union -> Always has args, any amount
    elif _isUnion(x):
        return str(tuple([_getTypeName(arg) for arg in x.__args__]))

    # typing.List -> Optional args, any amount
    elif _isList(x):
        args = _getArgs(x)
        s = "List["
        if args:
            s += f"{args[0]}]"
        else:
            s += "]"
        return s

    # typing.Tuple -> Optional args, any amount
    elif _isTuple(x):
        args = _getArgs(x)
        s = "Tuple["
        for arg in args:
            s += f"{_getTypeName(arg)}, "
        s = s[:len(s)-2] # remove comma and trailing whitespace
        return s + "]"

    # typing.Dict -> Optional args, always has 2 if present
    elif _isDict(x):
        s = "Dict["
        args = _getArgs(x)
        if args:
            # args[0] = keytype, args[1] = valuetype
            s += f"{_getTypeName(args[0])}: {_getTypeName(args[1])}"
        return s + "]"

    # typing.TypeVar -> Can be bound to a type
    elif _isTypeVar(x):
        bound = _getBound(x)

        if bound:
            # __name__ is the name of the typevar
            s = _getTypeName(bound) + f" (TypeVar(\"{x.__name__}\"))"
        else:
            s = str(x)
        return s

    # typing.Type -> Optional args, references a type if present
    elif _isType(x):
        args = _getArgs(x)
        if not args:
            type_ = type
        else:
            type_ = args[0]
        return _getTypeName(type_)

    # Fallback to __name__ and __qualname__
    else:
        name = getattr(x, '__name__', None)
        if not name:
            name = getattr(x, '__qualname__', None)
            if not name:
                name = str(x)
        return name

def _isUnion(x: Any) -> bool:
    """
    Returns True if x is a Union.
    """
    # Check the origin
    return get_origin(x) is Union

def _isList(x: Any) -> bool:
    """
    Returns True if x is a List.
    """
    # Check the origin
    return get_origin(x) == list

def _isTuple(x: Any) -> bool:
    """
    Returns True if x is a Tuple.
    """
    # Check the origin
    return get_origin(x) == tuple

def _isDict(x: Any) -> bool:
    """
    Returns True if x is a Dict.
    """
    # Check the origin
    return get_origin(x) == dict

def _isTypeVar(x: Any) -> bool:
    """
    Returns True if x is a TypeVar.
    """
    # NOTE: TypeVars are all instances so
    # we can use an instance check but other
    # typing objects (specifically ones that
    # are subscripted) raise errors on
    # instance checks.
    try:
        return isinstance(x, TypeVar)
    except:
        return False

def _isType(x: Any) -> bool:
    """
    Returns True if x is Type.
    """
    # HACKHACK: Accessing private class of the typing module
    return x == Type and x.__class__ == _SpecialGenericAlias

def _isBuiltinType(x: Any) -> bool:
    """
    Returns True if x is generic builtin type.
    """
    return x == type

def _isCallable(x: Any) -> bool:
    """
    Returns True if x is a Callable.
    """
    # HACKHACK: Accessing private class of the typing module
    return x.__class__ == _CallableGenericAlias

def _isString(x: Any) -> bool:
    """
    Returns True if x is a string.
    """
    try:
        return isinstance(x, str) or x == str
    except:
        return False

def _typecheck(v: Any, t: Type) -> bool:
    """
    Checks if the value `v` matches the type `t`.
    Returns False if the types do not match otherwise True.
    """
    # Use a check flag here for each case with a value of None.
    # If the flag isn't set before the return then
    # a final instance check occurs. Note that any typing
    # objects (subscriptable ones) will cause an exception
    # on the instance check.
    check = None

    # typing.Any -> matches everything
    if t == Any:
        check = True

    # typing.NoReturn -> This should never be triggered (NoReturn should exit before a typecheck on a return)
    elif t == NoReturn:
        raise RuntimeError("NoReturn should not be accessed by the typed wrapper")

    # types.NoneType -> Ensure the value is None
    elif t is None or t == type(None):
        check = v is None

    # typing.Type -> Only care about type checking if there is a type associated with it.
    elif _isType(t):
        args = _getArgs(t)

        if len(args) == 0:
            check = True
        else:
            # Check the associated type
            check = _typecheck(v, args[0])

    # typing.TypeVar -> Only care about type checking if there is a bound type
    elif _isTypeVar(t):
        # e.g.
        # U = TypeVar("U", bound=User)
        # def sendVerificationEmail(user: U): ...
        # The bound type of U would be User because it was 
        # specifically bound, otherwise we only have the given name
        # and can't perform type checking.
        bound = _getBound(t)

        if bound:
            check = _typecheck(v, bound)
        else:
            check = True

    # type (builtins.type) -> Builtin type means any type could be parsed as this value so its always True
    elif _isBuiltinType(t):
        check = True

    # typing.Union -> Check the value is one of the types in the union
    # NOTE: Optional[...] == Union[..., None]
    elif _isUnion(t):
        check = False

        # Unions will always have args
        for type_ in t.__args__:
            x = _typecheck(v, type_)
            if x:
                check = True
                break

    # typing.List -> Check that all items match the type. (Lists have one arg (if present))
    elif _isList(t):
        args = _getArgs(t)

        if not isinstance(v, list):
            check = False

        elif not args:
            check = True

        else:
            check = all([_typecheck(x, args[0]) for x in v])

    # typing.Tuple -> Check length and type, order matters!
    elif _isTuple(t):
        args = _getArgs(t)

        if not isinstance(v, tuple):
            check = False

        elif not args:
            check = True

        elif len(args) != len(v):
            check = False

        else:
            check = True

            for i in range(len(args)):
                if not _typecheck(v[i], args[i]):
                    check = False

    # typing.Dict -> Check key type and value type
    elif _isDict(t):
        args = _getArgs(t)

        if not isinstance(v, dict):
            check = False
        else:
            keyType = args[0]
            valType = args[1]
            keys = tuple(v.keys())
            vals = tuple(v.values())
            keysCheck = all([_typecheck(key, keyType) for key in keys])
            valsCheck = all([_typecheck(val, valType) for val in vals])
            check = keysCheck and valsCheck

    # typing.Callable
    # NOTE: Normally callables are wrapped into _TypedWrapper
    # on return (unless wrapping is off) callables that make
    # it into this if statement are only those which are subscripted
    # (not generic `Callable` or the wrapped ones.) Simply return True.
    elif _isCallable(t):
        return True

    elif _isString(t):
        # Strings (representive retruns like)
        # def getUser(someargs) -> "User": ...
        # are handled here. They are always true because
        # they are basically just a type var without an arg.
        check = True

    # If not value has been set for the check then perform an instance check
    if check is None:
        check = isinstance(v, t)

    if __DEBUG__:
        print("[CHCKD]:", v, _getTypeName(t), check)

    return check

class _TypedWrapper:
    @classmethod
    def from_class(cls, klass: type) -> '_TypedWrapper':
        """
        Create a wrapper for classes.
        This is called when the typed descriptor is used on a class
        as a whole.
        """
        # Get methods from klass
        methods = []

        attrs = dir(klass)
        for attr in attrs:
            x = getattr(klass, attr)
            if isinstance(x, (MethodType, FunctionType)) and not attr.startswith("__"):
                methods.append(x)

        # Mostly we don't wrap dunder methods but for __init__ we make an exception.
        if "__init__" in attrs:
            methods.append(getattr(klass, "__init__"))

        for method in methods:
            # Cannot wrap a descriptro wrapper
            if isinstance(method, WrapperDescriptorType):
                continue

            typedmethod = typed(method)

            # Add the typedmethod to the class
            setattr(klass, typedmethod.func.__name__, typedmethod)

    @classmethod
    def from_callable(cls, func, type_):
        """
        Create a wrapper from a callable.
        This is used when wrapping callables.
        """
        args = _getArgs(type_)
        return_type = Any

        if args:
            # The last arg is always the return type
            return_type = args[-1]
            args = args[:len(args)-1]

        # Get the annotations
        names = _getArgNames(func.__code__)
        annotations = {}
        nAnnotations = len(args)

        # Loop through names
        for i in range(len(args)):
            # if there is an available annotation
            if i < nAnnotations:
                # add the arg with the annotation
                annotations[names[i]] = args[i]
            else:
                # No available annotation, use Any
                annotations[names[i]] = Any

        # Add the return type to the annotations
        annotations["return"] = return_type

        if __DEBUG__:
            print("[WRCLL]:", func, type_)

        # Get a dummy typedwrapper (empty)
        wrapper = cls(None, _dummy=True)

        # set values
        wrapper._setArgs(names)\
            ._setFunc(func)\
            ._setReturnType(return_type)\
            ._setAnnotations(annotations)

        return wrapper

    def __init__(self, func: Callable, *, wrap_callables: bool=True, _dummy: bool=False):
        if _dummy:
            return

        # We cant use descriptor wrappers
        if isinstance(func, WrapperDescriptorType):
            raise TypeError("typed descriptor cannot be used on a descriptor wrapper")
        
        # get annotations
        rawAnnotations = func.__annotations__
        annotations = {}
        names = _getArgNames(func.__code__)

        for name in names:
            # Use types for any args with annotations
            # otherwise use Any
            if name in rawAnnotations:
                annotations[name] = rawAnnotations[name]
            else:
                annotations[name] = Any

        # Get return type
        if "return" in rawAnnotations:
            rt = rawAnnotations["return"]
        else:
            rt = Any

        annotations["return"] = rt

        self.wrap_callables = wrap_callables
        self._setFunc(func)
        self._setArgs(names)
        self._setAnnotations(annotations)
        self._setReturnType(rt)

    def _setArgs(self, args):
        """
        Internal method to set the args.
        """
        self.args = args
        return self

    def _setAnnotations(self, annotations):
        """
        Internal method to set the annotations.
        """
        self.annotations = annotations
        return self

    def _setReturnType(self, return_type):
        """
        Internal method to set the return type.
        """
        self.return_type = return_type
        self.return_type_name = _getTypeName(self.return_type)

        # Add to annotations if not already there
        if hasattr(self, "annotations") and ("return" not in self.annotations or self.annotations["return"] != return_type):
            self.annotations["return"] = return_type
        return self

    def _setFunc(self, func):
        self.func = func

        # Function name
        if hasattr(func, "__name__"):
            name = func.__name__
        elif hasattr(func, "__qualname__"):
            name = func.__qualname__
        else:
            name = "<unknown>"

        self.name = name
        self.__doc__ = func.__doc__
        self.__name__ = name
        self.__qualname__ = name
        return self

    def __call__(self, *args, **kwargs):
        ret = self.typedfunc(args, kwargs)

        if __DEBUG__:
            print("[CKRTN]:", ret, self.return_type)

        if _isCallable(ret) and self.wrap_callables:
            # Wrap the returned callable.
            return self.__class__.from_callable(ret, self.return_type)

        # Perform a typecheck on the returned value
        if _typecheck(ret, self.return_type):
            return ret
        else:
            raise TypeError("Function '%s' must return type '%s'" % (self.name, self.return_type_name))

    def __get__(self, x, t):
        """
        Allows for instance binding (partial function)
        """
        return _partial(self.__call__, x)

    def typedfunc(self, args, kwargs):
        """
        Performs type checking on args and then calls the function.
        """
        argzip = dict(zip(self.args, args))

        for arg in argzip:
            if __DEBUG__:
                print("[CHECK]:", arg, argzip[arg], _getTypeName(type(argzip[arg])), _getTypeName(self.annotations[arg]))

            if not _typecheck(argzip[arg], self.annotations[arg]):
                typename = _getTypeName(self.annotations[arg])
                raise TypeError("Function '%s' argument '%s' must be type '%s'" % (self.name, arg, typename))

        try:
            return self.func(*args, **kwargs)
        except Exception as exc:
            if __DEBUG__:
                print("[ERROR]:", exc.__class__.__qualname__, str(exc))
            raise

def typed(func):
    """
    Typed descriptor which allows for strict typing in python.
    """
    if not hasattr(func, "__code__") and hasattr(func, "__dict__"):
        # For Classes use the from_class method
        _TypedWrapper.from_class(func)
        return func # return the class
    else:
        return _TypedWrapper(func)

def _main():
    """
    Testing function
    """
    X = TypeVar("X", bound=int)

    @typed
    def myFunc(x: int, y=None) -> Callable[[int, int, Optional[bool]], int]:
        def test(x, y, test=None) -> int:
            return int(x + y)
        return test

    inner_wrapped = myFunc(2) # this will wrap and return the test callable
    x = inner_wrapped(2, 2) # this is calling the test function wrapped by _TypedWrapper

    if __DEBUG__:
        print("Return Value:", x) # x+y=4 This should be 4 and there should be no errors.
        
    # This should cause an error. These are not ints
    try:
        y = inner_wrapped(2.0, 2.0)
    except TypeError as exc:
        if __DEBUG__:
            print("[ERROR]:", f"{exc.__class__.__qualname__}:", str(exc))

    else:
        if __DEBUG__:
            print("This should not happen. An error should be raised here.")
            print("y=%s" % y)


    @typed
    def passInADict(data: Dict) -> None:
        return data

    try:
        passInADict(['test'])
    except TypeError as exc:
        if __DEBUG__:
            print("[ERROR]:", f"{exc.__class__.__qualname__}:", str(exc))


    class Test:
        def __init__(self):
            pass

        @classmethod
        @typed
        def classmethod(cls):
            print("class!", cls)

        @staticmethod
        @typed
        def staticmethod():
            print("static")

    t = Test()
    t.classmethod()
    t.staticmethod()
    Test.staticmethod()

if __name__ == "__main__":
    __DEBUG__ = True

    _main()