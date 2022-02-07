"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: framework.py
Description: the core module of the framework.
All modules depend on this.
"""
from typing import Set

__DEFINES__: Set[str] = set()

def define(x: str) -> None:
	"""
	Define `x` marking it as true.
	"""
	__DEFINES__.add(x.lower())

def defined(x: str) -> bool:
	"""
	Returns True if `x` is defined.
	"""
	return x.lower() in __DEFINES__
