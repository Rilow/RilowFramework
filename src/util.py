"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: util.py
Description: Utility functions
"""
from typing import Iterable, Callable

def forEach(i: Iterable, func: Callable) -> None:
	for x in i:
		func(x)
