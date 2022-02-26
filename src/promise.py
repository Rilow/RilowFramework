"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: promise.py
Description: Promise-like objects in python.
"""
import asyncio

from renum import frozenenum
# Promise States
PromiseStates = frozenenum(
    "PENDING",
    "CANCELLED",
    "FINISHED",
)

class PromiseResult:
    FAILURE = 0
    SUCCESS = 1

    def __init__(self, status, promise=None, data=None):
        self.status = status
        self.promise = promise
        self.data = data

    def __str__(self):
        status = self.status
        return f"<PromiseResult({status=})>"

class Promise:
    def __init__(self, function, *, loop=None):
        # Promise State
        self._state = PromiseStates.PENDING

        # Result value
        self._result = None

        # Any exception raised getting result
        self._exception = None

        # Next promise in chain
        self._then = None

        # Last promise in chain
        self._parent = None

        # Exception handler callback
        self._error = None

        # Function callback
        self._function = function

    def __str__(self):
        state = PromiseStates[self._state]
        return f"<Promise({state=!s})>"

    def _get_root(self):
        p = self
        while p._parent is not None:
            p = p._parent
        return p 

    def get_result(self):
        if self._state == PromiseStates.PENDING:
            self._get_result()

        if not isinstance(self._result, PromiseResult):
            status = PromiseResult.FAILURE if self._exception is not None else PromiseResult.SUCCESS
            self._result = PromiseResult(status, self, self._result)
        return self._result

    def _get_result_async(self):
        p = self._get_result()

        if p._exception is not None:
            pass

    def _get_result(self):
        if self._parent is not None:
            raise TypeError("Can only call getResult on root promise")
        elif self._state != PromiseStates.PENDING:
            raise TypeError("cannot get new result of non-pending promise state")

        p = self

        if p._then is None:
            self._result = p._function()
            return

        i = 0
        while True:
            i+=1
            if i>10000: raise RecursionError("maximum recursion reached in Promise._get_result()")

            if p._parent is not None and p._parent._result is not None:
                args = (p._parent._result,)
            else:
                args = tuple()

            try:
                p._result = p._function(*args)
                p.finish()
            except Exception as exc:
                p._exception = exc
                p.cancel()
                return p

            if p._then is None:
                break

            p = p._then


        return p
            
    def _get_error_handler(self):
        # Start at the next promise.
        if self._then is not None:
            p = self._then
        else:
            p = self

        i=0
        while True:
            i+=1
            if i>10000: raise RecursionError("maximum recursion reached in Promise._get_error_handler()")

            if p._error is not None:
                break

            if p._parent is None:
                break

            p = p._parent

        return p._error


    def cancelled(self):
        return self._state == PromiseStates.CANCELLED

    def done(self):
        return self._state == PromiseStates.FINISHED

    def finish(self):
        self._state = PromiseStates.FINISHED

    def cancel(self):
        self._state = PromiseStates.CANCELLED
        
        if self._exception is None:
            raise TypeError("cancelled with no exception")

        # Find the closest parent (or this object)
        # with a error handler.
        handler = self._get_error_handler()

        if handler is not None:
            e = self._exception
            handler(e.__class__, e, e.__traceback__)

        else:
            # If there is no handler present then raise the error.
            raise self._exception

    def then(self, func):
        self._then = Promise(func)
        self._then._parent = self
        return self._then

    def error(self, func):
        self._error = func
        return self  

    def __enter__(self):
        root = self._get_root()
        root._get_result()
        return root.get_result()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

if __name__ == "__main__":
    def _internalGetJson():
        return {"test": 123}

    def _internalGetJsonWithError():
        raise TypeError("some error")

    def getJson():
        return Promise(_internalGetJson)

    def getJsonError():
        return Promise(_internalGetJsonWithError)

    def test(data):
        print("IN TEST:", data)

    def onError(type, exc, tb):
        print("ON ERROR:", type, exc, tb)

    getJson().then(test).error(onError)

    with getJson().then(test).error(onError) as result:
        print(result, result.data, result.promise)

    print()

    with getJsonError().then(test).error(onError) as result:
        print(result, result.data, result.promise)

    print()

    try:
        with getJsonError().then(test) as result:
            pass
    except TypeError:
        print("Thrown!")
    else:
        raise TypeError("an error should be thrown here")