"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: debug.py
Description: Useful debugging tools.
"""
import ast
from collections import defaultdict
import sys
import os

class QualnameVisitor(ast.NodeVisitor):
    """
    A qualname visitor is used to get qualnames
    from nodes and is only used if
    QUALNAMES_ENABLED == True
    """
    def __init__(self):
        ast.NodeVisitor.__init__(self)

        # Stack of names and dict
        self.stack = []
        self.qualnames = {}

    def add_qualname(self, node, name=None):
        # Add a new qualname from a given node (optional name)
        name = name or node.name
        self.stack.append(name)
        if getattr(node, "decorator_list", ()):
            lineno = node.decorator_list[0].lineno
        else:
            lineno = node.lineno
        self.qualnames.setdefault((name, lineno), ".".join(self.stack))

    def visit_FunctionDef(self, node, name=None):
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

    def visit_lambda(self, node):
        self.visit_FunctionDef(node, "<lambda>")

    def visit_ClassDef(self, node):
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
        self._qualnames = {}
        self._linecache = {}

        # Add hooks
        sys.setprofile(self._profilerhook)
        sys.addaudithook(self._auditerhook)
        sys.addaudithook(self._exceptionshook)

    def _profilerhook(self, frame, event, arg):
        if not self.PROFILER_ENABLED:
            return self._profilerhook

        for hook in self._profilers:
            hook(frame, event, arg)
        return self._profilerhook

    def _auditerhook(self, name, args):
        if not self.AUDITER_ENABLED:
            return self._auditerhook

        for hook in self._auditers:
            hook(name, args)
        return self._auditerhook

    def _exceptionshook(self, name, args):
        if not self.EXCEPTIONS_ENABLED or name != "sys.excepthook":
            return self._exceptionshook

        for hook in self._exceptionshook:
            hook(*args)
        return self._exceptionshook

    def addProfiler(self, func):
        if func not in self._profilers:
            self._profilers.append(func)

    def removeProfiler(self, func):
        if func in self._profilers:
            self._profiles.remove(func)

    def addAuditer(self, func):
        if func not in self._auditers:
            self._auditers.append(func)

    def removeAuditer(self, func):
        if func in self._auditers:
            self._auditers.remove(func)

    def addException(self, func):
        if func not in self._exceptions:
            self._exceptions.append(func)

    def removeException(self, func):
        if func in self._exceptions:
            self._exceptions.remove(func)

    def setProfiler(self, flag):
        self.PROFILER_ENABLED = flag

    def setQualnames(self, flag):
        self.QUALNAMES_ENABLED = flag

    def setAuditer(self, flag):
        self.AUDITER_ENABLED = flag

    def setExceptions(self, flag):
        self.EXCEPTIONS_ENABLED = flag

    def setAll(self, flag):
        self.setProfiler(flag)
        self.setQualnames(flag)
        self.setAuditer(flag)
        self.setExceptions(flag)

    def _getLines(self, file):
        if file not in self._linecache:
            try:
                with open(file) as f:
                    self._linecache[file] = f.read().splitlines()
            except UnicodeDecodeError:
                pass 

        return self._linecache.get(file, None)

    def _getQualname(self, frame):
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

    def profiler(self, frame, event, arg, indent=[0]):
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
        if event == "c_call":
            indent[0] += 2
            print("-" * indent[0], f"{qualname}()")
            return

        elif event == "c_return":
            #print("-" * indent[0], f"return {qualname}")
            indent[0] -= 2
            return

        elif event == "call":
            indent[0] += 2
            print("-" * indent[0], f"{qualname}()")
            return

        elif event == "return":
            #print("-" * indent[0], f"return {qualname}")
            indent[0] -= 2
            return

        else: # "c_exception"
            print("-" * indent[0], f"err {arg}")
            return

    def auditer(self, name, args):
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

    def exception(self, type, value, traceback):
        return print(f"[EXCEPTION] {type.__qualname__}: {value}")

# Only provide once instance of the debugger.
Debugger = Debugger()

if __name__ == "__main__":
    Debugger.setAll(True)