"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: util.py
Description: Utility functions
"""
from typing import Iterable, Callable

def forEach(i: Iterable, func: Callable) -> None:
	if not isinstance(i, Iterable):
		raise TypeError("i must be iterable")
	elif not callable(func):
		raise TypeError(f"{func} is not callable")

	for x in i:
		func(x)
	return

