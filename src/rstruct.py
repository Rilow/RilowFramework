"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: rilowstruct.py
Description: Contains the Struct class. Which allows the creation of a 
dummy object that can hold any data.

Also contains the FrozenStruct which only allows attribute reading.
"""
import inspect

class FrozenError(Exception):
    """
    Raised when attempting to modify a frozen object.  
    """
    pass

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
        s = f"<{self.__class__.__qualname__}("

        # For empty structs, otherwise
        # it shows "<Struc)>"
        if len(self.__dict__) == 0:
            return s + ")>"

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

    def __setitem__(self, item, value):
        return self.__setattr__(item, value)

    def _hasValue(self, attr: str) -> bool:
        """
        Returns True if `attr` is inside of the struct values.
        """
        return attr in self.__dict__.values()

    def _freeze(self) -> "FrozenStruct":
        """
        Returns a FrozenStruct copy of this struct.
        NOTE: Does NOT freeze this struct.
        """
        return freeze(self)

class FrozenStruct(Struct):
    def __setattr__(self, attr, value):
        # Check if the previous frame was within the FrozenStruct class or not.
        # Currently the only way to set attributes of a FrozenStruct
        # is inside FrozenStruct.__init__ / Struct.__init__
        _self = inspect.stack()[1][0].f_locals.get("self", None)

        if _self and (_self == self or _self == FrozenStruct):
            self.__dict__[attr] = value
        else:
            raise FrozenError("Struct is frozen and cannot be modified.")

    def __setitem__(self, item, value):
        raise FrozenError("Struct is frozen and cannot be modified.")

def freeze(struct: Struct) -> FrozenStruct:
    """
    Freezes a struct.
    """
    return FrozenStruct(**struct.__dict__)