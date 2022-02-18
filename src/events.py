"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: events.py
Description: An easy to use events manager.
"""
from typing import Union, List, Dict, Callable

from rilowenum import enum

# EventType can be either the event name (str   ) or the events code (int)
EventType = Union[str, int]

# Builtin events.
Events = enum(
    # FRAMEWORK_LOAD is called when the framework finishes loading.
    # Args:
    #   modules -> A dict of loaded framework modules (not finalized)
    # NOTE: This should only be triggered once (it is used internally)
    # This event is special in that it can trigger without a
    # on() call if a framework module has a onFrameworkLoad() function
    # inside of its global namespace. When this event is triggered
    # all framework modules then have access to the framework namespace. 
    # Do not attempt to access the framework namespace before this
    # event is triggered.
    "FRAMEWORK_LOAD",

    # FRAMEWORK_FINALIZE is called when the framework is finalizing.
    # NOTE: This is different from when python is finalizing. This event
    # isn't guarenteed to be run. It's more reliant to use __del__ for python
    # finalization in order to do finalizing.
    "FRAMEWORK_FINALIZE",

    # MODULE_LOAD is called when a framework module is loaded. 
    # Args: 
    #   module -> The module that was loaded.
    "MODULE_LOAD",

    # EVENT is called whenever an event is triggered.
    # Args:
    #   name -> The events name
    #   *args **kwargs -> The events arguments.
    "EVENT",

    # CALLBACK_ERROR is called when an error ocurrs during a callbacks
    # error handler callback.
    # Args:
    #   binding -> The EventBinding object that caused the error.
    #   exc -> The exception that was raised
    "CALLBACK_ERROR",

    # EXCEPTION is called whenever an error ocurrs.
    # Args:
    #   exc_type -> The type of exception
    #   exc_value -> The value of the exception (the object)
    #   exc_tb -> The exception traceback
    #   defer -> The defer function (see more below)
    #   Optional Arg: binding -> The binding argument is optional
    #   and is only passed in when an exception is raised while inside of
    #   an event callback (and that exception is unhandled.)
    "EXCEPTION",
)

def _getEventCode(event: EventType) -> int:
    """
    Returns the code for a given event.
    """
    if isinstance(event, int):
        return event
    elif not isinstance(event, str):
        raise TypeError("event must be a string or an int")

    if event in Events:
        return Events(event)
    else:
        # Generate a new code.
        code = 0
        for i, char in enumerate(event):
            n = ord(char)-97 # 97 == ord("a")
            # Alternate between adding and subtracting so that
            # the order matters
            if i % 2 == 0:
                code += n
            else:
                code -= n

        # After the code has been generated we need to make sure there
        # are no duplicates.
        while Events._hasValue(code):
            code += 1

        # Add to events.
        Events[event] = code
        return code

def _getEventName(event: EventType) -> str:
    """
    Returns the name for a given event.
    """
    if isinstance(event, str):
        return event
    elif not isinstance(event, int):
        raise TypeError("event must be a string or an int")

    if Events._hasValue(event):
        return Events[event]
    else:
        raise ValueError(f"unknown event '{event}'")

class EventBinding:
    def __init__(self):

        # The event name and code
        self.event: str = None
        self.eventCode: int = None

        # The callback binding to the event.
        self.callback: Callable = None

        # Should the callback only be called once? (doOnce)
        self.once: bool = False


        # Optional onError callback
        self.errCallback: Callable = None

    def on(self, event: EventType) -> "EventBinding":
        if self.event is not None or self.eventCode is not None:
            raise TypeError("cannot call EventBinding.on() more than once")
        
        code = _getEventCode(event)
        name = _getEventName(code)
        self.event = name
        self.eventCode = code
        return self

    def onError(self, function: Callable) -> "EventBinding":
        if self.errCallback is not None:
            raise TypeError("cannot call EventBinding.onError() more than once")

        self.errCallback = function
        return self

    def do(self, function: Callable) -> "EventBinding":
        if self.callback is not None:
            raise TypeError("cannot call EventBinding.do() more than once")

        self.callback = function
        return self

    def doOnce(self, function: Callable) -> "EventBinding":
        if self.callback is not None:
            raise TypeError("cannot call EventBinding.do() more than once")

        self.callback = fuction
        self.once = True
        return self


class EventManager:
    # The current active event binding.
    _current_bind: EventBinding = None

    # If this is true during an Events.EXCEPTION trigger
    # then the event will be deferred. This is changed
    # by calling the defer() function from within the
    # event callback.
    _should_defer: bool = False

    _registry: Dict[int, List[EventBinding]] = {}

    @classmethod
    def _finalize_bind(cls):
        # Finalize the current bind if one exists.
        if cls._current_bind is None:
            return

        bind = cls._current_bind
        cls._current_bind = None

        if bind.eventCode is None:
            raise TypeError("event not specified for binding")
        elif bind.callback is None:
            raise TypeError("callback not specified for binding")

        if bind.eventCode in cls._registry:
            cls._registry[bind.eventCode].append(bind)
        else:
            cls._registry[bind.eventCode] = [bind]

    @classmethod
    def _remove_bind(cls, binding: EventBinding) -> None:
        if binding.eventCode is None:
            raise TypeError("event not specified for binding")

        if binding.eventCode not in cls._registry:
            return

        bindings = cls._registry[binding.eventCode]

        if binding in bindings:
            bindings.remove(binding)

        if len(bindings) == 0:
            del cls._registry[binding.eventCode], bindings

    @classmethod
    def _defer(cls):
        """
        Defers the Events.EXCEPTION from raising.
        """
        cls._should_defer = True

    @classmethod
    def _do_exception_event(cls, exc, binding=None):
        """
        Performs an Events.EXCEPTION event.
        Internal method do not use.
        """
        if Events.EXCEPTION not in cls._registry:
            raise exc

        exc_value = exc
        exc_type = exc.__class__
        exc_tb = exc.__traceback__

        for binding in cls._registry[Events.EXCEPTION]:
            cls._should_defer = False

            # Wrap in try/except only to respect doOnce
            try:
                binding.callback.__call__(exc_type, exc_value, exc_tb, cls._defer, binding)
            finally:
                if binding.once:
                    cls._remove_bind(binding)


            if cls._should_defer:
                continue
            else:
                raise exc

    @classmethod
    def on(cls, event: EventType) -> EventBinding:
        cls._finalize_bind()

        cls._current_bind = EventBinding()
        cls._current_bind.on(event)
        return cls._current_bind

    @classmethod
    def do(cls, event: EventType, *args, **kwargs):
        cls._finalize_bind()

        code = _getEventCode(event)

        if code not in cls._registry:
            return

        bindingsWithErrors = []
        bindingsWithErrorsWithoutOnErrorCallback = []
        bindingsWithErrorsWithErrorsCallingOnErrorCallbacks = []

        # Try and run every bindings callback, if there are any errors
        # append the error and the binding to the bindingsWithErrors list.
        for binding in cls._registry[code]:
            try:
                binding.callback.__call__(*args, **kwargs)
            except Exception as exc:
                bindingsWithErrors.append((exc, binding))

        # Go through the bindingsWithErrors list and check if they have an err callback
        # if they dont add them to the bindingsWithErrorsWithoutOnErrorCallback list.
        # Otherwise try to run the error callback. If there is an error during the 
        # error callback then add them to the
        # bindingsWtihErrorsWithErrorsCallingOnErrorCallbacks list.
        for (exc, binding) in bindingsWithErrors:
            if binding.errCallback is None:
                bindingsWithErrorsWithoutOnErrorCallback.append((exc, binding))
                continue

            
            try:
                binding.errCallback.__call__(exc)
            except Exception as exc2:
                bindingsWithErrorsWithErrorsCallingOnErrorCallbacks.append((exc2, binding))

        # If an error was raised while calling an onError callback then we don't really
        # want to trigger an exception we just kind of ignore it. But we do
        # send out a Events.CALLBACK_ERROR event with the binding and exception.
        for (exc, binding) in bindingsWithErrorsWithErrorsCallingOnErrorCallbacks:
            if event != Events.CALLBACK_ERROR:
                cls.do(Events.CALLBACK_ERROR, binding, exc)

        # Now that all the above code has managed to run (MAKE SURE THIS IS LAST
        # WE WANT TO MAKE SURE ALL CODE THAT NEEDS TO RUN RUNS BEFORE 
        # WE RAISE AN EXCEPTION)
        # Now we do a Events.EXCEPTION event and pass it a defer function.
        # If that defer function is called it means that the exception was
        # handled (or ignored) and can be defered and does not need to be raised.
        for (exc, binding) in bindingsWithErrorsWithoutOnErrorCallback:
            cls._do_exception_event(exc, binding)

if __name__ == "__main__":
    def test():
        raise TypeError("testing")

    def errorHandler(exc_type, exc_value, exc_tb, defer, binding=None):
        print(exc_type, exc_value, exc_tb, defer, binding)

        defer()

    #EventManager.on("test", test)
    EventManager.on(Events.EVENT).do(test)
    EventManager.on(Events.EXCEPTION).do(errorHandler)
    EventManager.do(Events.EVENT)

    raise TypeError("test")