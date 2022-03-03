"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: rtest.py
Description: A simple testing library.
"""
from typing import Any, Callable, Type, Iterable, Union, List, Dict, Optional

Number = Union[float, int]

class RAssertionError(AssertionError):
    """
    A subclass of AssertionError used by this testing library.
    This is useful to differentiate a normal assertion
    from one caused by this library.
    """
    pass

# Internal Assert Functions.
def _assert(x: Any, msg: Optional[str]="") -> None:
    """
    Same as `assert x`
    Raises RAssertionError if x is false.
    """
    if x: return

    raise RAssertionError(msg)

# Copy of original function. Because
# all assertion functions call this one internally
# this allows you to overwrite assertion behaviour
# by overwriting this function. You can then restore the
# original (or call the original) by using `__assert__`
__assert__ = _assert

def _assertNoError(func: Callable, msg: Optional[str]="") -> None:
    """
    Asserts that function `func` does not raise an exception.
    Calls _assert(x) where x is True if an exception was raised.
    """
    try:
        func()
    except:
        exc = False
    else:
        exc = True

    _assert(exc, msg)

def _assertError(func: Callable, type_: Type[Exception], msg: Optional[str]="") -> None:
    """
    Asserts that function `func` raises an exception of type `type_`
    Calls _assert(x) where x is True if an exception of type `type_` was raised.
    """
    try:
        func()
    except type_:
        exc = True
    except Exception:
        exc = False
    else:
        exc = True

    return _assert(exc)

# Public Assert Functions
def assertTrue(x: Any, msg: Optional[str]="") -> None:
    """
    Assert that x is True.
    """
    _assert(x, msg)

def assertFalse(x: Any, msg: Optional[str]="") -> None:
    """
    Assert that x is False.
    """
    _assert(not x, msg)

def assertNone(x: Any, msg: Optional[str]="") -> None:
    """
    Assert that x is None
    """
    _assert(x is None, msg)

def assertNotNone(x: Any, msg: Optional[str]="") -> None:
    """
    Assert that x is not None
    """
    _assert(x is not None, msg)

def assertContains(item: Any, x: Iterable, msg: Optional[str]="") -> None:
    """
    Assert that `x` contains `item`
    """
    assertIterable(x, msg)
    _assert(item in x, msg)

def assertDoesNotContain(item: Any, x: Iterable, msg: Optional[str]="") -> None:
    """
    Assert that `x` does not contain `item`
    """
    assertIterable(x, msg)
    _assert(item not in x, msg)

def assertIs(x: Any, y: Any, msg: Optional[str]="") -> None:
    """
    Assert x is y
    """
    _assert(x is y, msg)

def assertIsNot(x: Any, y: Any, msg: Optional[str]="") -> None:
    """
    Assert x is not y
    """
    _assert(x is not y, msg)

def assertEqual(x: Any, y: Any, msg: Optional[str]="") -> None:
    """
    Assert x == y
    """
    _assert(x == y, msg)

def assertNotEqual(x: Any, y: Any, msg: Optional[str]="") -> None:
    """
    Assert x != y
    """
    _assert(x != y, msg)

def assertIterable(x: Any, msg: Optional[str]="") -> None:
    """
    Assert that x is iterable.
    """
    _assertNoError(lambda: iter(x), msg)

def assertNotNaN(x: Any, msg: Optional[str]="") -> None:
    """
    Assert x is not NaN (not a number).
    """
    # float("NaN") == float("NaN") => False
    _assert(x == x)

def assertIsInstance(x: Any, y: Type, msg: Optional[str]="") -> None:
    """
    Assert x is an instance of y
    """
    _assert(isinstance(x, y))

def assertInRange(n: Number, x: Number, y: Number, msg: Optional[str]="") -> None:
    """
    Assert that x < n < y
    """
    _assert((x < y) and (n > x and n < y), msg)

def assertNotInRange(n: Number, x: Number, y: Number, msg: Optional[str]="") -> None:
    """
    Assert that n < x || n > y
    """
    _assert((x < y) and (n < x or n > y), msg)

def _getArgs(args: List[Any], funcName: str) -> List[Any]:
    """
    Internal function used by function with *args varargs that require at
    least one argument. Returns any nested list.
    e.g.
    someFunction([1, 2, 3, 4]) == someFunction(1, 2, 3, 4)
    If someFunction uses _getArgs.
    """
    if len(args) == 0:
        raise TypeError(f"must call {funcName} with at least one argument")
    elif len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = args[0]
    return args

def assertAll(*args: Any, msg: Optional[str]="") -> None:
    """
    Assert all(*args)
    """
    args = _getArgs(args, "assertAll")
    _assert(all(args), msg)

def assertNotAll(*args: Any, msg: Optional[str]="") -> None:
    """
    Assert all(not arg for arg in *args)
    """
    args = _getArgs(args, "assertNotAll")
    _assert(all([not x for x in args]), msg)

def assertAny(*args: Any, msg: Optional[str]="") -> None:
    """
    Assert any(*args)
    """
    args = _getArgs(args, "assertAny")
    _assert(any(args), msg)

def assertRaises(func: Callable, exc: Type[Exception], *args: Any, msg: Optional[str]="", **kwargs: Any) -> None:
    """
    Assert that function `func` raises exception(s) `exc`
    """
    _assertError(lambda: func(*args, **kwargs), exc, msg)

def assertDoesNotRaise(func: Callable, *args: Any, msg: Optional[str]="", **kwargs: Any) -> None:
    """
    Assert that function `func` does not raise exception(s)
    """
    _assertNoError(lambda: func(*args, **kwargs), msg)

class TestResult:
    """
    A class that holds the result of a single test.
    """
    def __init__(self, test_: "test", passed: bool):
        self.test = test_
        self.name = test_.name
        self.function = test_.function
        self.passed = passed

class _TestSuiteMeta(type):
    def __new__(cls, name, bases, attrs):
        # Ignore meta-ing TestSuite class.
        if "TestSuite" not in globals():
            return type.__new__(cls, name, bases, attrs)

        tests = {}
        _startup = None
        _startupAll = None
        _teardown = None
        _teardownAll = None

        for attr, value in attrs.items():
            if isinstance(value, test):
                tests[attr] = value
            elif isinstance(value, startup):
                _startup = value
            elif isinstance(value, startupAll):
                _startupAll = value
            elif isinstance(value, teardown):
                _teardown = value
            elif isinstance(value, teardownAll):
                _teardownAll = value

        attrs["_tests"] = tests
        attrs["_startup"] = _startup
        attrs["_startupAll"] = _startupAll
        attrs["_teardown"] = _teardown
        attrs["_teardownAll"] = _teardownAll

        return type.__new__(cls, name, bases, attrs)

class TestSuite(metaclass=_TestSuiteMeta):
    def __getattr__(self, attr):
        # Check globals (for assertion methods)
        if attr in globals():
            return globals()[attr]
        raise AttributeError(f"TestSuite has no attribute {attr}")

    def _printresults(self) -> None:

        print("============================")

        print("{:<20s}{:<7s}".format("NAME", "PASSED?"), "\n", sep="")

        for testresult in self._results:
            n = testresult.name + ":"
            print(f"{n:<20s}{str(testresult.passed):<5s}")

        self._results.clear()

        print("============================")

    @classmethod
    def run(cls, printresults: Optional[bool]=True) -> None:
        """
        Start running this test suites tests.
        """
        self = cls()
        self._doTests()

        if printresults:
            self._printresults()

    def _doTests(self) -> None:
        """
        Runs tests.
        """
        # Initialize suite.
        self._results: List[TestResult] = []

        # startupAll
        if self._startupAll is not None:
            self._startupAll(self)

        # Run each test,
        for test_ in self._tests.values():
            self._runTest(test_)

        if self._teardownAll is not None:
            self._teardownAll(self)

    def _runTest(self, test_: "test") -> None:
        """
        Run a test.
        """
        if self._startup is not None:
            self._startup(self)

        if not isinstance(test_, test):
            raise TypeError("`test` must be an instance of test")

        try:
            test_.__call__(self)
        except RAssertionError: #, AssertionError: # Py_AssertionError
            passed = False
        else:
            passed = True

        self._results.append(TestResult(test_, passed))

        if self._teardown is not None:
            self._teardown(self)

_MISSING_SELF = "missing 1 required positional argument: 'self'"
_MISSING_SELF_MODULE_TEST_SUITE = TestSuite()

class _BaseFunctionCaller:
    def __init__(self, function: Callable):
        self.function = function
        self.name = function.__name__

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        try:
            return self.function.__call__(*args, **kwargs)
        except TypeError as exc:
            if _MISSING_SELF not in exc.args[0]:
                raise
            
            # Have to catch RAssertionError manually for module level tests,
            # and then return a result.
            passed = True
            try:
                self.function.__call__(_MISSING_SELF_MODULE_TEST_SUITE, *args, **kwargs)
            except RAssertionError:
                passed = False

            return TestResult(self, passed)




class test(_BaseFunctionCaller):
    """
    Represents a single test in a suite.
    """
    pass

class startup(_BaseFunctionCaller):
    """
    Represents a test suite startup.
    """
    pass

class startupAll(_BaseFunctionCaller):
    """
    Represents a test suite startup all.
    """
    pass

class teardown(_BaseFunctionCaller):
    """
    Represents a test suite teardown.
    """
    pass

class teardownAll(_BaseFunctionCaller):
    """
    Represents a test suite teardown all
    """
    pass

def _test() -> None:
    """
    A method which tests if the assertions are working.
    """
    # Test assertRaises first. So we can 
    # make sure it works to be able to test _assert.

    # assertRaises
    def func(): raise TypeError()
    assertRaises(func, TypeError)
    try:
        assertRaises(func, ValueError)
    except RAssertionError:
        pass
    else:
        raise RAssertionError()
    del func

    # assertDoesNotRaise
    def func(): raise TypeError()
    def func2(): pass
    assertDoesNotRaise(func2)
    assertRaises(assertDoesNotRaise, RAssertionError, func)
    del func, func2

    # _assert
    _assert(True)
    assertRaises(_assert, RAssertionError, False)

    # assertTrue
    assertTrue(True)
    assertRaises(assertTrue, RAssertionError, False)

    # assertFalse
    assertFalse(False)
    assertRaises(assertFalse, RAssertionError, True)

    # assertNone
    assertNone(None)
    assertRaises(assertNone, RAssertionError, 1)

    # assertNotNone
    assertNotNone(1)
    assertRaises(assertNotNone, RAssertionError, None)

    # assertContains
    list_ = [1, 2, 3, 4]
    assertContains(1, list_)
    assertRaises(assertContains, RAssertionError, 5, list_)
    del list_

    # assertDoesNotContain
    list_ = [1, 2, 3, 4]
    assertDoesNotContain(5, list_)
    assertRaises(assertDoesNotContain, RAssertionError, 1, list_)
    del list_

    # assertIs
    # NOTE: This may differ depending on implementation details.
    # But at least for CPython integer objects are cached and
    # are therefore the same object.
    assertIs(2, 2)
    assertRaises(assertIs, RAssertionError, 1, 2)

    # assertIsNot
    # NOTE: see above
    assertIsNot(1, 2)
    assertRaises(assertIsNot, RAssertionError, 2, 2)

    # assertEqual
    assertEqual(2, 2)
    assertRaises(assertEqual, RAssertionError, 1, 2)

    # assertNotEqual
    assertNotEqual(1, 2)
    assertRaises(assertNotEqual, RAssertionError, 2, 2)

    # assertIterable (must go before all asserts which check for iterables.)
    list_ = list()
    tuple_ = tuple()
    dict_ = dict()
    assertIterable(list_)
    assertIterable(tuple_)
    assertIterable(dict_)
    assertRaises(assertIterable, RAssertionError, None)
    del list_, tuple_, dict_

    # assertAll
    list1 = [True, True, True]
    list2 = [False, False, False]
    assertAll(list1)
    assertRaises(assertAll, RAssertionError, list2)
    del list1, list2

    # assertNotAll
    list1 = [False, False, False]
    list2 = [False, False, True]
    assertNotAll(list1)
    assertRaises(assertNotAll, RAssertionError, list2)
    del list1, list2

    # assertAny
    list1 = [False, False, True]
    list2 = [False, False, False]
    assertAny(list1)
    assertRaises(assertAny, RAssertionError, list2)
    del list1, list2

    # assertNotNaN
    x = float("NaN")
    assertNotNaN(2)
    assertRaises(assertNotNaN, RAssertionError, x)
    del x

    # assertIsInstance
    assertIsInstance(2, int)
    assertRaises(assertIsInstance, RAssertionError, 2, str)

    # assertInRange
    assertInRange(2, 0, 5)
    assertRaises(assertInRange, RAssertionError, 10, 0, 5)

    # assertNotInRange
    assertNotInRange(10, 0, 5)
    assertRaises(assertNotInRange, RAssertionError, 2, 0, 5)

    # Test TestSuite.
    # NOTE: Assertion methods (i.e. above can be called off the class itself)
    # i.e. the TestSuite class will lookup unknown attributes in the global
    # namespace this allows things like TestSuite.assertTrue (self.assertTrue)
    # to redirect to the global assertTrue function.
    class MyTests(TestSuite):
        @startupAll
        def myStartup(self):
            print("MY TESTS:")

        @startup
        def startup(self):
            print("HELLO WORLD!")

        @teardown
        def teardown(self):
            print("my teardown")

        @test
        def myTest(self):
            print("hello")
            self.assertTrue(False)

        @test
        def myTest2(self):
            print("world")

        @teardownAll
        def test(self):
            print("TEARDOWN ALL")

    MyTests.run()

    # Tests can also be run without a suite.
    @test
    def mytest(self):
        self.assertTrue(True)

    @test
    def myTestThatRaises(self):
        self.assertTrue(False)

    result = mytest()
    assertRaises(myTestThatRaises, RAssertionError)
    # print(result.function, result.name, result.passed)

__all__ = [
    "TestSuite",
    "startup", "startupAll",
    "teardown", "teardownAll",
    "test",
]

# Copy assertion methods.
for attr in globals().copy():
    if attr.startswith("assert") and attr[0] != "_":
        __all__.append(attr)

if __name__ == "__main__":
    _test()
