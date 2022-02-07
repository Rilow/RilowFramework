"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: framework.py
Description: the core module of the framework.
All modules depend on this.
"""
from typing import Set

# Because typed is not part of the framework
# it is not guarenteed to be available.
try:
	from typed import typed
except ImportError:
	def typed(x): return x

__DEFINES__: Set[str] = set()

@typed
def define(x: str) -> None:
	"""
	Define `x` marking it as true.
	"""
	__DEFINES__.add(x.lower())

@typed
def defined(x: str) -> bool:
	"""
	Returns True if `x` is defined.
	"""
	return x.lower() in __DEFINES__

# Normally modules that are part of the framework will define themselves
# but because typed is imported by the framework to avoid circular imports
# it is defined here. We can check if the module for the typed
# function defined at the tope of this file is of the "typed" module
# and not "__main__" or "framework"
if typed.__module__ == "typed":
	define("TYPED_PY")