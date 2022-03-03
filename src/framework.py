"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: framework.py
Description: The core module framework.
"""
# Import debug first.
from debug import Debugger

if __name__ == '__main__':
    # Enable debugger.
    Debugger.setAll(True)

# Import framework modules
from config import Config, MemoryConfig
from events import EventManager, Events
import lang
from override import override
from private import private
from profiler import Profiler
from renum import enum
from rstruct import Struct, FrozenStruct
from rtest import *
from rtypes import TypeWrapper, ALL_OPERATIONS, COPY_OPERATIONS_ONCE, COPY_OPERATIONS
from typed import typed
from util import *
