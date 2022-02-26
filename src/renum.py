"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: rilowenum.py
Description: A simple way to create enums that are incremental 
integer values for each key.
"""
from typing import Any, T

from rstruct import FrozenStruct, Struct

def _enum(structklass: T, *args: Any) -> T:
    """
    Internal enum creation function. Used by enum() and frozenenum()

    Takes the struct class to use and the enum arguments.
    """
    data = {}
    counter = 0

    # Give each arg an integer value and return a struct.
    for arg in args:
        data[arg] = counter
        counter += 1

    return structklass(**data)

def enum(*args: Any) -> Struct:
    """
    Takes a list of string keys and returns a
    enum-like Struct object which automatically creates 
    integer values for the enum values.
    """
    return _enum(Struct, *args)

def frozenenum(*args: Any) -> FrozenStruct:
    """
    Takes a list of string keys and returns a
    enum-like FrozenStruct object which automatically creates
    integer values for the enum values.
    """
    return _enum(FrozenStruct, *args)