"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: override.py
Description: Function overrides in python
"""
import functools
import inspect
from typing import Any, Callable, Dict, List, Union, Optional

from framework import typed, defined

@typed
def _getClassFromMethod(meth: Callable) -> Optional[type]:
	"""
	Attempts to get the class from a method/function.
	"""
	# Use the internal method for partial functions
	if isinstance(meth, functools.partial):
		return _getClassFromMethod(meth.func)

	# Scan the mro
	if inspect.ismethod(meth) or (inspect.isbuiltin(meth) and getattr(meth, '__self__', None) is not None and getattr(meth.__self__, '__class__', None)):
		for cls in inspect.getmro(meth.__self__.__class__):
			if meth.__name__ in cls.__dict__:
				return cls
		meth = getattr(meth, '__func__', meth) # Fallback to __qualname__ parsing

	# __qualname__ parsing
	if inspect.isfunction(meth):
		cls = getattr(inspect.getmodule(meth),
						meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0],
						None)
		if isinstance(cls, type):
			return cls

	return getattr(meth, '__objclass__', None) # special descriptor objects

@typed
def _getManagerId(func: Callable) -> str:
	"""
	Returns the manager id of a given function.
	"""
	cls = _getClassFromMethod(func)
	if cls:
		return cls.__qualname__
	else:
		return func.__module__

@typed
def _getHash(types: List[type]) -> int:
	"""
	Returns the hash to be used for a given list of types.
	"""
	# NOTE: Alternating between adding and subtracting allows
	# for different outputs based on the ORDER of types not just
	# on the types that are included. This allows for (int, str)
	# to be different from (str, int).
	# return sum([id(t) for t in types])
	ids = [id(t) for t in types]
	acc = 0
	for i, id_ in enumerate(ids):
		if i % 2 == 0:
			acc += id_
		else:
			acc -= id_
	return acc

class _OverrideManager:
	@typed
	def __init__(self, id: str):
		self.id = id
		self._overrides: Dict[str, Dict[int, Callable]] = {}

	@typed
	def _addOverride(self, func: Callable) -> None:
		"""
		Adds an override to the manager.
		"""
		name = func.__name__
		types = list(func.__annotations__.values())
		hash = _getHash(types)

		if name in self._overrides:
			self._overrides[name][hash] = func
		else:
			self._overrides[name] = {hash: func}

	@typed
	def _callOverride(self, func: Callable, args: Any, kwargs: Any) -> Any:
		name = func.__name__
		types = [type(arg) for arg in args]
		hash = _getHash(types)
		override = self._overrides[name][hash]
		return override.__call__(*args, **kwargs)

	@typed
	def getWrapper(self, func: Callable) -> Callable:
		"""
		Get an override wrapper for a given func.
		"""
		self._addOverride(func)

		def wrapper(*args, **kwargs):
			return self._callOverride(func, args, kwargs)

		wrapper.__doc__ = func.__doc__
		wrapper.__name__ = func.__name__
		wrapper.__qualname__ = func.__qualname__
		return wrapper

class _OverrideManagerFactory:
	_managers: Dict[str, _OverrideManager] = {}

	@classmethod
	@typed
	def getManager(cls, func: Callable) -> _OverrideManager:
		id = _getManagerId(func)

		if id in cls._managers:
			return cls._managers[id]

		else:
			manager = _OverrideManager(id)
			cls._managers[id] = manager
			return manager

def override(func):
	"""
	Override decorator.
	"""
	return _OverrideManagerFactory.getManager(func).getWrapper(func)

if __name__ == '__main__':
	@override
	def test(x: int):
		print("int!", x)

	@override
	def test(x: str):
		print("string!", x)

	@override
	def test(x: int, y: str):
		print("int str")

	@override
	def test(x: str, y: int):
		print("str int")

	k = list(_OverrideManagerFactory._managers.keys())[0]
	print(test)
	print(_OverrideManagerFactory._managers)
	print(_OverrideManagerFactory._managers[k]._overrides)
	print()

	test(2)
	test("testing")
	print()

	test(2, "hello")
	test("hello", 2)
	print()


