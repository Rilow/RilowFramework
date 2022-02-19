"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: framework.py
Description: The core module framework.
"""

from config import Config, MemoryConfig
from debug import Debugger
from events import EventManager, Events
import lang
from override import override
from private import private
from renum import enum
from rtypes import TypeWrapper, ALL_OPERATIONS, COPY_OPERATIONS_ONCE, COPY_OPERATIONS
from rstruct import Struct, FrozenStruct
from typed import typed
from util import *
