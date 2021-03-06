"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: debug.py
Description: Useful debugging tools.
"""
import ast
from collections import defaultdict
import sys
import os
from typing import Optional, List, Tuple, Callable, Any, TypeVar, Type
from types import FrameType, TracebackType

from util import ClampedInt

# Not really sure what to name this, its used as a type hint
# for a argument that is only passed in/modified by the function itself.
# (i.e. only used internally)
Internal = TypeVar("Internal", bound=list)

class QualnameVisitor(ast.NodeVisitor):
    """
    A qualname visitor is used to get qualnames
    from nodes and is only used if
    QUALNAMES_ENABLED == True
    """
    def __init__(self):
        ast.NodeVisitor.__init__(self)

        # Stack of names and dict
        self.stack: List[str] = []

        # (name, linenumber) -> qualname
        self.qualnames: Dict[Tuple[str, int], str] = {}

    def add_qualname(self, node: ast.AST, name: Optional[str]=None) -> None:
        # Add a new qualname from a given node (optional name)
        name = name or node.name
        self.stack.append(name)
        if getattr(node, "decorator_list", ()):
            lineno = node.decorator_list[0].lineno
        else:
            lineno = node.lineno
        self.qualnames.setdefault((name, lineno), ".".join(self.stack))

    def visit_FunctionDef(self, node: ast.AST, name: Optional[str]=None) -> None:
        self.add_qualname(node, name)
        self.stack.append("<locals>")
        if isinstance(node, ast.Lambda):
            children = [node.body]
        else:
            children = node.body

        for child in children:
            self.visit(child)
        self.stack.pop()
        self.stack.pop()

        for field, child in ast.iter_fields(node):
            if field == "body":
                continue
            if isinstance(child, ast.AST):
                self.visit(child)
            elif isinstance(child, list):
                for grandchild in child:
                    if isinstance(grandchild, ast.AST):
                        self.visit(grandchild)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_lambda(self, node: ast.AST) -> None:
        self.visit_FunctionDef(node, "<lambda>")

    def visit_ClassDef(self, node: ast.AST) -> None:
        self.add_qualname(node)
        self.generic_visit(node)
        self.stack.pop()

class Debugger:

    IGNORED_AUDITS = (
        "object.__getattr__",
        "compile",
        "sys.excepthook",
        "marshal.loads"
    )

    def __init__(self):

        # Flags
        self.PROFILER_ENABLED = False
        self.QUALNAMES_ENABLED = False
        self.AUDITER_ENABLED = False
        self.EXCEPTIONS_ENABLED = False

        # Hooks
        self._profilers = [self.profiler]
        self._auditers = [self.auditer]
        self._exceptions = [self.exception]

        # Qualname caching
        # (name, linenumber) -> qualname
        self._qualnames: Dict[Tuple[str, int], str] = {}

        # file -> lines
        self._linecache: Dict[str, List[str]] = {}

        # Should we defer?
        # This is used for exceptions. If we should defer then
        # the exception is ignored.
        self._should_defer = False

        # Add hooks
        sys.setprofile(self._profilerhook)
        sys.addaudithook(self._auditerhook)
        sys.addaudithook(self._exceptionshook)
        sys.excepthook = self._defer_excepthook

    def _profilerhook(self, frame: FrameType, event: str, arg: Any) -> Callable:
        """
        The internal profiler hook. Do not call.

        This is a system profiler which calls all profile hooks.
        """
        if not self.PROFILER_ENABLED:
            return self._profilerhook

        for hook in self._profilers:
            hook(frame, event, arg)
        return self._profilerhook

    def _auditerhook(self, name: str, args: Any) -> Callable:
        """
        The internal audit hook. Do not call.

        This is a audit hook which calls all audit hooks.
        """
        if not self.AUDITER_ENABLED:
            return self._auditerhook

        for hook in self._auditers:
            hook(name, args)
        return self._auditerhook

    def _defer(self) -> None:
        """
        Should we defer the exception?
        """
        self._should_defer = True

    def _exceptionshook(self, name: str, args: Any) -> Callable:
        """
        The internal exceptions hook. Do not call.

        This is an audithook that will trigger all exception hooks
        if the audit name is "sys.excepthook"
        """
        if not self.EXCEPTIONS_ENABLED or name != "sys.excepthook":
            return self._exceptionshook

        args = args[1:] # <built-in function excepthook> is the first arg.
        defers = []

        for hook in self._exceptions:
            self._should_defer = False
            hook(*args, self._defer)
            defers.append(self._should_defer)
        
        # We only defer if every callback thinks we should defer.
        self._should_defer = all(defers)
        
        # NOTE: This audit hook is called internally by python right
        # before the sys.excepthook function is called.
        # This means we don't need to call _defer_excepthook directly
        # it will ALWAYS be called right after this function. 
        return self._exceptionshook

    def _defer_excepthook(self, exc_type: Type[Exception], exc_value: Exception, exc_tb: TracebackType) -> Callable:
        if not self._should_defer:
            # sys.__excepthook__ is a copy of sys.excepthook.
            # Because we overwrite sys.excepthook with _defer_excepthook we
            # can call the internal copy. This will raise the exception.
            sys.__excepthook__(exc_type, exc_value, exc_tb)
        else:
            # Defer the exception. Do nothing.
            self._should_defer = False
            return self._defer_excepthook

    #                                    frame,   event, arg    return
    def addProfiler(self, func: Callable[[FrameType, str, Any], None]) -> None:
        """
        Add a profile hook.
        Does nothing if the function is already a profile hook.
        """
        if func not in self._profilers:
            self._profilers.append(func)

    def removeProfiler(self, func: Callable) -> None:
        """
        Removes a profile hook.
        Does nothing if the function is not a profile hook.
        """
        if func in self._profilers:
            self._profiles.remove(func)

    #                                  name, args,  return
    def addAuditer(self, func: Callable[[str, Any], None]) -> None:
        """
        Add an audit hook.
        Does nothing if the function is already an audit hook.
        """
        if func not in self._auditers:
            self._auditers.append(func)

    def removeAuditer(self, func: Callable) -> None:
        """
        Removes an audit hook.
        Does nothing if the function is not an audit hook.
        """
        if func in self._auditers:
            self._auditers.remove(func)

    #                                      type,            value,     traceback,      return
    def addException(self, func: Callable[[Type[Exception], Exception, TracebackType], None]) -> None:
        """
        Add an exception hook.
        Does nothing if the function is already an exception hook.
        """
        if func not in self._exceptions:
            self._exceptions.append(func)

    def removeException(self, func: Callable) -> None:
        """
        Remove an exception hook.
        Does nothing if the function is not an exception hook.
        """
        if func in self._exceptions:
            self._exceptions.remove(func)

    def setProfiler(self, flag: bool) -> None:
        """
        Set the PROFILER_ENABLED flag.
        """
        self.PROFILER_ENABLED = flag

    def setQualnames(self, flag: bool) -> None:
        """
        Set the QUALNAMES_ENABLED flag.
        """
        self.QUALNAMES_ENABLED = flag

    def setAuditer(self, flag: bool) -> None:
        """
        Set the AUDITER_ENABLED flag.
        """
        self.AUDITER_ENABLED = flag

    def setExceptions(self, flag: bool) -> None:
        """
        Set the EXCEPTIONS_ENABLED flag.
        """
        self.EXCEPTIONS_ENABLED = flag

    def setAll(self, flag: bool) -> None:
        """
        Shortcut for calling
        setProfiler(flag)
        setQualnames(flag)
        setAuditer(flag)
        setExceptions(flag)
        """
        self.setProfiler(flag)
        self.setQualnames(flag)
        self.setAuditer(flag)
        self.setExceptions(flag)

    def _getLines(self, file: str) -> Optional[List[str]]:
        """
        Get lines for a file from the linecache.
        Used Internally.
        """
        if file not in self._linecache:
            try:
                with open(file) as f:
                    self._linecache[file] = f.read().splitlines()
            except UnicodeDecodeError:
                pass 

        return self._linecache.get(file, None)

    def _getQualname(self, frame: FrameType) -> str:
        """
        Returns the qualname for a given frame.
        Used internally.
        """
        code = frame.f_code
        file = code.co_filename

        if file in self._qualnames:
            return self._qualnames[file].get((code.co_name, code.co_firstlineno), code.co_name)

        if file.startswith("<") and file.endswith(">"): # <module> <locals> <lambda>
            return code.co_name

        try:
            lines = self._getLines(file)
        except MemoryError:
            self._linecache.clear()
            lines = self._getLines(file)

        if lines is None:
            return code.co_name

        text = "\n".join(lines)
        lines = [line.rstrip("\r\n") for line in lines]

        tree = ast.parse(text)
        visitor = QualnameVisitor()
        visitor.visit(tree)

        self._qualnames[file] = visitor.qualnames
        return self._qualnames[file].get((code.co_name, code.co_firstlineno), code.co_name)

    def profiler(self, frame: FrameType, event: str, arg: Any, indent: Internal=ClampedInt(0, 2, None)) -> None:
        """
        Builtin profiler callback.
        Prints profile info to stdout
        """
        if event[0] == "c" and hasattr(arg, "__qualname__"):
            # Most c calls contain the function as the arg.
            qualname = f"builtins.{arg.__qualname__}"
        elif self.QUALNAMES_ENABLED:
            qualname = self._getQualname(frame)

            if qualname == "<module>":
                name = os.path.basename(frame.f_code.co_filename)
                qualname = f"<module '{name}'>"

        else:
            qualname = frame.f_code.co_name

        # The order here is important (handle c calls fast for performance reasons.)
        # Python is very slow. Having to call slow python code every time you call a
        # c function can cause a lot of latency in the c code.
        if event == "c_return" or event == "return":
            indent -= 2
            print("-" * indent, f"~{qualname}()")
            
            return

        elif event == "c_call" or event == "call":
            print("-" * indent, f"{qualname}()")
            indent += 2
            return

        else: # "c_exception"
            print("-" * indent, f"err {arg}")
            return

    def auditer(self, name: str, args: Any) -> None:
        """
        Default auditer callback.
        Prints audit info depending on the type.
        """
        if name in self.IGNORED_AUDITS:
            return

        msg = ""

        print("[AUDIT] ", end='')

        if name == "import":
            msg = args[0]
        elif name == "open":
            fp = args[0]
            mode = args[1]
            msg = f"{fp}, {mode=}"
        elif name == "exec":
            code = args[0]
            if code.co_name == "<module>":
                msg = code.co_filename
            else:
                msg = code.co_name

        print(name + " ", end='')

        # Print message if available otherwise just
        # print the args.
        s = msg if msg else args

        print(str(s)) # std::endl;

    def exception(self, type: Type[Exception], value: Exception, traceback: TracebackType, defer: Callable):
        """
        Builtin exception call back.
        Prints the exception to stdout.
        """
        # Output the error
        print(f"[EXCEPTION] {type.__qualname__}: {value}")

        # Defer
        defer()

# Only provide once instance of the debugger.
Debugger = Debugger()

if __name__ == "__main__":
    Debugger.setAll(True)
    raise TypeError("test")
    print("test")