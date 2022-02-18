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
from rilowenum import enum
from rilowtypes import TypeWrapper
from rilowstruct import Struct
from typed import typed
from util import *
