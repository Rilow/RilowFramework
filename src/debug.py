"""
Copyright (c) 2022 Rilow, All rights reserved.

Name: debug.py
Description: Useful debugging tools.
"""
import ast
from collections import defaultdict
import sys

### Profiling ###
class QualnameVisitor(ast.NodeVisitor):
    def __init__(self):
        ast.NodeVisitor.__init__(self)

        self.stack = []
        self.qualnames = {}

    def add_qualname(self, node, name=None):
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


def profilehook(frame, event, arg):
    if not _profile_enabled:
        return profilehook

    for hook in _profile_hooks:
        hook(frame, event, arg)
    return profilehook # psuedo code for sys module: sys.profilehook = sys.profilehook(frame, event, arg)

def builtinprofilehook(frame, event, arg, indent=[0]):
    """
    A builtin profile hook.
    This can be enabled with enableProfileHook()
    """
    if arg and hasattr(arg, "__qualname__"):
        co_name = arg.__qualname__
    else:
        co_name = frame.f_code.co_name

    indent[0] = max(indent[0], 0) # Clamp indent to positive number

    # The order of these is important.
    # Because python code is very slow (compared to c)
    # we want to be as fast as possible for c functions so
    # we don't hold up the rest of the program flow.
    #print(event, arg)
    if event == "c_call":
        indent[0] += 2
        print("-" * indent[0] + "> call c function", co_name)
        return

    elif event == "c_return":
        print("<" + "-" * indent[0], "exit c function", co_name)
        indent[0] -= 2
        return

    elif event == "call":
        if _useQualnames:
            qualname = _getQualname(frame)
        else:
            qualname = co_name

        indent[0] += 2
        print("-" * indent[0] + "> call function", qualname)
        return

    elif event == "return":
        if co_name == "<module>":
            return

        if _useQualnames:
            qualname = _getQualname(frame)
        else:
            qualname = co_name

        print("<" + "-" * indent[0], "exit function", qualname)
        indent[0] -= 2
        return

    elif event == "c_exception":
        # c_exception is rarer than the others. so its at the bottom.
        print("-" * indent[0] + "> err", arg)
        return

    else:
        raise RuntimeError(f"unknown event {event}")

    return

def addProfileHook(hook):
    """
    Add a new profile hook.
    """
    if not callable(hook):
        raise TypeError("hook must be callable")
    elif hook in _profile_hooks:
        raise ValueError("hook already present")

    _profile_hooks.append(hook)

def removeProfileHook(hook):
    """
    Remove a profile hook.
    """
    if hook not in _profile_hooks:
        raise ValueError("hook not found")

    _profile_hooks.remove(hook)

def enableProfileHook():
    """
    Enable the builtin profile hook.
    See `builtinprofilehook`
    """
    try:
        addProfileHook(builtinprofilehook)
    except:
        pass

_profile_enabled = False
def setProfileHooks(flag):
    global _profile_enabled
    _profile_enabled = flag

_useQualnames = False
_linecache = {}
_qualnames = {}

def toggleQualnames():
    global _useQualnames
    _useQualnames = not _useQualnames

def setQualnames(flag):
    global _useQualnames
    _useQualnames = flag

def _getQualname(frame):
    file = frame.f_code.co_filename

    if file in _qualnames:
        return _qualnames[file].get((frame.f_code.co_name, frame.f_code.co_firstlineno), frame.f_code.co_name)

    if file.startswith("<") and file.endswith(">"):
        return frame.f_code.co_name

    if file not in _linecache:
        try:
            with open(file) as f:
                lines = f.read().splitlines()
            _linecache[file] = lines
        except UnicodeDecodeError:
            return frame.f_code.co_name
    else:
        lines = _linecache[file]

    text = '\n'.join(lines)
    lines = [line.rstrip("\r\n") for line in lines]

    tree = ast.parse(text)
    _nodes_by_line = defaultdict(list)

    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node

        if hasattr(node, "lineno"):
            if hasattr(node, "end_lineno") and isinstance(node, ast.expr):
                linenos = range(node.lineno, node.end_lineno + 1)
            else:
                linenos = [node.lineno]

            for lineno in linenos:
                _nodes_by_line[lineno].append(node)

    visitor = QualnameVisitor()
    visitor.visit(tree)
    
    # Update qualnames with visitor qualnames.
    _qualnames[file] = visitor.qualnames
    qualname = visitor.qualnames.get((frame.f_code.co_name, frame.f_code.co_firstlineno), frame.f_code.co_name)
    return qualname
    
### Auditing ###

def audithook(name, args):
    if not _audits_enabled:
        return audithook

    for hook in _audit_hooks:
        hook(name, args)
    return audithook

_ignored_audits = (
    "object.__getattr__", # Too much output
    "compile", # Contains output of the entire compilation.
    "sys.excepthook", # Can be handled by exceptionhook.
    "marshal.loads", # Spam

)

def builtinaudithook(name, args):

    if name in _ignored_audits:
        return

    msg = ""
    printName = True

    print("[AUDIT] ", end='')

    if name == "import":
        msg = args[0]
    elif name == "open":
        msg = f"{args[0]}, mode={args[1]}"
    elif name == "exec":
        code = args[0]
        if code.co_name == "<module>":
            msg = code.co_filename
        else:
            msg = code.co_name



    if printName: print(name + " ", end='')
    if msg: print(msg + " ", end='')
    else: print(str(args) + " ", end='')

    # endl;
    print()

def addAuditHook(hook):
    """
    Adds a new audit hook.
    """
    if not callable(hook):
        raise TypeError("hook must be callable")
    elif hook in _audit_hooks:
        raise ValueError("hook already present")

    _audit_hooks.append(hook)

def removeAuditHook(hook):
    """
    Removes an audit hook.
    """
    if hook not in _audit_hooks:
        raise ValueError("hook not found")

    _audit_hooks.remove(hook)

def enableAuditHook():
    """
    Enables the builtin audit hook.
    See `builtinaudithook`
    """
    try:
        addAuditHook(builtinaudithook)
    except:
        pass

_audits_enabled = False
def setAuditHooks(flag):
    global _audits_enabled
    _audits_enabled = flag

### Exception hook ###
def _excepthook_audit_hook(name, args):
    if name != "sys.excepthook":
        return

    excepthook(*args[1:])
    return _excepthook_audit_hook

def excepthook(type, value, traceback):
    if not _exceptions_enabled:
        return

    for hook in _exception_hooks:
        hook(type, value, traceback)

def builtinexcepthook(type, value, traceback):
    print("[EXCEPTION]", f"{type.__qualname__}:", f"{value}")

def addExceptionHook(func):
    """
    Adds an exception hook.
    """
    if func not in _exception_hooks:
        _exception_hooks.append(func)

def enableExceptionHook():
    """
    Enables the builtin exception hook.
    """
    addExceptionHook(builtinexcepthook)

_exceptions_enabled = False
def setExceptionHooks(flag):
    global _exceptions_enabled
    _exceptions_enabled = flag

# Hooks
_profile_hooks = [builtinprofilehook]
_audit_hooks = [builtinaudithook]
_exception_hooks = [builtinexcepthook]

# Set system hooks
sys.setprofile(profilehook)
sys.addaudithook(audithook)
sys.addaudithook(_excepthook_audit_hook)

if __name__ == "__main__":
    toggleQualnames()
    enableExceptionHook()
    enableAuditHook()
    enableProfileHook()