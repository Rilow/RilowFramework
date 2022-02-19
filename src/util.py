"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: util.py
Description: Utility functions
"""
from typing import Iterable, Callable, Union, Optional

import rilowtypes as _types

Number = Union[int, float, complex]
NumberTypes = (int, float, complex)

__all__ = [
	"ClampedInt",
	"forEach",
	"clamp"
]

class ClampedInt(_types.TypeWrapper):
	ALLOWED_OPERATIONS = _types.ALL_OPERATIONS

	def __init__(self, x: int=0, min: Optional[int]=None, max: Optional[int]=None):
		self.min = min
		self.max = max

		if self.min is None: self.min = float("-inf")
		if self.max is None: self.max = float("inf")

		if self.min > self.max:
			# Swap
			temp = self.min
			self.min = self.max
			self.max = temp
			del temp

		self._value = x
		_types.TypeWrapper.__init__(self, x)

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, value):
		if isinstance(value, ClampedInt):
			value = value.value

		self._value = clamp(value, self.min, self.max)

def forEach(i: Iterable, func: Callable) -> None:
	if not isinstance(i, Iterable):
		raise TypeError("i must be iterable")
	elif not callable(func):
		raise TypeError(f"{func} is not callable")

	for x in i:
		func(x)
	return

def clamp(x: Number, min_: Optional[Number]=None, max_: Optional[Number]=None) -> Number:
	if min_ is None: min_ = float("-inf")
	if max_ is None: max_ = float("inf")

	if not isinstance(x, NumberTypes):
		raise TypeError("x must be a number")
	elif not isinstance(min_, NumberTypes):
		raise TypeError("min_ must be a number")
	elif not isinstance(max_, NumberTypes):
		raise TypeError("max_ must be a number")
	elif min_ > max_:
		raise ValueError("Minimum value cannot be greater than maximum value")

	return max(min(x, max_), min_)
