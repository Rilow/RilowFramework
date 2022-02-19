"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: rilowenum.py
Description: A simple way to create enums that are incremental 
integer values for each key.
"""
from typing import Any

from rstruct import Struct

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

