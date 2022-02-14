"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: util.py
Description: Utility functions
"""
from typing import Iterable, Callable, Union, Optional

Number = Union[int, float, complex]
NumberTypes = (int, float, complex)

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

