"""Shared external-dependency names and static source scanners."""

from __future__ import annotations

import ast
from pathlib import Path
import re
import shlex
import sys

STDLIB_MODULES = frozenset({
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio", "asyncore",
    "atexit", "audioop", "base64", "bdb", "binascii", "binhex", "bisect", "builtins",
    "bz2", "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
    "codeop", "collections", "colorsys", "compileall", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib",
    "dis", "distutils", "doctest", "email", "encodings", "enum", "errno", "faulthandler",
    "fcntl", "filecmp", "fileinput", "fnmatch", "formatter", "fractions", "ftplib",
    "functools", "gc", "getopt", "getpass", "gettext", "glob", "graphlib", "grp",
    "gzip", "hashlib", "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr",
    "imp", "importlib", "inspect", "io", "ipaddress", "itertools", "json", "keyword",
    "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox", "mailcap", "marshal",
    "math", "mimetypes", "mmap", "modulefinder", "multiprocessing", "netrc", "nis",
    "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev", "parser", "pathlib",
    "pdb", "pickle", "pickletools", "pipes", "pkgutil", "platform", "plistlib",
    "poplib", "posix", "posixpath", "pprint", "profile", "pstats", "pty", "pwd",
    "py_compile", "pyclbr", "pydoc", "queue", "quopri", "random", "re", "readline",
    "reprlib", "resource", "rlcompleter", "runpy", "sched", "secrets", "select",
    "selectors", "shelve", "shlex", "shutil", "signal", "site", "smtpd", "smtplib",
    "sndhdr", "socket", "socketserver", "sqlite3", "ssl", "stat", "statistics",
    "string", "stringprep", "struct", "subprocess", "sunau", "symtable", "sys",
    "sysconfig", "syslog", "tabnanny", "tarfile", "telnetlib", "tempfile", "termios",
    "test", "textwrap", "threading", "time", "timeit", "tkinter", "token", "tokenize",
    "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types",
    "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp",
    "zipfile", "zipimport", "zlib",
    "__future__",
})


CANONICAL_DEPENDENCY_ALIASES = {
    "agent cli": ("agent cli", "selected agent", "selected agent cli", "claude", "codex", "opencode"),
    "browser": ("browser",),
    "bun": ("bun",),
    "cagent": ("cagent",),
    "coreutils": ("coreutils",),
    "gh": ("gh", "gh cli", "github cli"),
    "git": ("git",),
    "github": ("github",),
    "github api": ("github api",),
    "herdr": ("herdr", "herdr cli"),
    "inkscape": ("inkscape",),
    "jq": ("jq",),
    "librsvg": ("librsvg", "rsvg-convert", "rsvgconvert"),
    "node": ("node", "node.js", "nodejs"),
    "npm": ("npm",),
    "npx": ("npx",),
    "playwright": ("playwright", "playwright cli"),
    "posix shell": ("posix", "posix shell"),
    "python": ("python", "python 3", "python3"),
    "pyyaml": ("pyyaml", "yaml"),
    "rg": ("rg", "ripgrep"),
    "tailwind": ("tailwind", "tailwind css", "tailwindcss"),
    "uv": ("uv",),
    "web access": ("web access",),
}

COMMAND_CANONICAL = {
    alias: canonical
    for canonical, aliases in CANONICAL_DEPENDENCY_ALIASES.items()
    for alias in aliases
    if " " not in alias and alias not in {"yaml"}
}
PYTHON_IMPORT_CANONICAL = {"PIL": "pillow", "cv2": "opencv python", "yaml": "pyyaml"}
NODE_BUILTINS = {
    "assert", "buffer", "child_process", "cluster", "console", "crypto", "dgram", "diagnostics_channel",
    "dns", "domain", "events", "fs", "http", "http2", "https", "module", "net", "os", "path",
    "perf_hooks", "process", "punycode", "querystring", "readline", "repl", "stream", "string_decoder",
    "timers", "tls", "trace_events", "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
}
NON_EXTERNAL_COMMANDS = {
    ".", "[", "alias", "break", "case", "cd", "command", "continue", "do", "done", "echo", "elif",
    "else", "env", "esac", "eval", "exec", "exit", "export", "false", "fi", "for", "function",
    "getopts", "hash", "if", "local", "printf", "pwd", "read", "readonly", "return", "set", "shift",
    "source", "test", "then", "time", "trap", "true", "type", "typeset", "ulimit", "umask", "unalias", "unset",
    "until", "wait", "while", "basename", "cat", "chmod", "cmp", "cp", "cut", "date", "dirname",
    "find", "head", "ln", "ls", "mkdir", "mktemp", "mv", "readlink", "rm", "sort", "tail", "tee",
    "touch", "tr", "wc", "xargs",
}
SUBPROCESS_METHODS = {"run", "Popen", "call", "check_call", "check_output", "check_returncode"}
OS_PROCESS_FUNCTIONS = {
    "system", "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
    "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
}


def normalize_dependency_name(value: str) -> str:
    value = value.replace("`", "").casefold().strip().rstrip(".")
    value = re.sub(r"\b(selected|version)\b", "", value)
    value = re.sub(r"[^a-z0-9@]+", " ", value)
    normalized = " ".join(value.split())
    for canonical, aliases in CANONICAL_DEPENDENCY_ALIASES.items():
        if normalized == canonical or normalized in {re.sub(r"[^a-z0-9@]+", " ", alias.casefold()).strip() for alias in aliases}:
            return canonical
    return normalized


def command_dependency_name(command: str) -> str:
    base = Path(command).name.casefold()
    return COMMAND_CANONICAL.get(base, base)


def declared_matches(evidence: str, declared: str) -> bool:
    evidence = normalize_dependency_name(evidence)
    declared = normalize_dependency_name(declared)
    aliases = CANONICAL_DEPENDENCY_ALIASES.get(evidence, (evidence,))
    normalized_aliases = {normalize_dependency_name(alias) for alias in aliases} | {evidence}
    return any(re.search(rf"(?:^| ){re.escape(alias)}(?: |$)", declared) for alias in normalized_aliases if alias)


def python_source_evidence(path: Path, repo_root: Path, local_modules: set[str]) -> list[tuple[int, str, str]]:
    """Return ``(line, kind, dependency)`` for imports and static process calls."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []
    result: list[tuple[int, str, str]] = []
    aliases: dict[str, tuple[str, str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".", 1)[0]
                name = alias.asname if alias.asname else alias.name
                aliases[name] = (base, base)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            module = node.module.split(".", 1)[0]
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                aliases[name] = (module, alias.name)
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules = [node.module.split(".", 1)[0]]
        for module in modules:
            if module not in getattr(sys, 'stdlib_module_names', STDLIB_MODULES) and module not in local_modules:
                result.append((getattr(node, "lineno", 1), "python-import", PYTHON_IMPORT_CANONICAL.get(module, module)))
        if not isinstance(node, ast.Call) or not _is_process_call(node.func, aliases):
            continue
        argument = node.args[0] if node.args else next((item.value for item in node.keywords if item.arg == "args"), None)
        command = _static_command(argument)
        if command and Path(command).name not in NON_EXTERNAL_COMMANDS and not _is_repository_script(command, path.parent, repo_root):
            result.append((getattr(node, "lineno", 1), "command", command_dependency_name(command)))
    return sorted(set(result))


def _is_process_call(function: ast.expr, aliases: dict[str, tuple[str, str]]) -> bool:
    if isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
        module, _original = aliases.get(function.value.id, (None, None))
        if module == "subprocess":
            return function.attr in SUBPROCESS_METHODS
        if module == "os":
            return function.attr in OS_PROCESS_FUNCTIONS
        return False
    if isinstance(function, ast.Name):
        module, original = aliases.get(function.id, (None, None))
        if module == "subprocess":
            return original in SUBPROCESS_METHODS
        if module == "os":
            return original in OS_PROCESS_FUNCTIONS
    return False


def _static_command(argument: ast.expr | None) -> str | None:
    value: str | None = None
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        value = argument.value
    elif isinstance(argument, (ast.List, ast.Tuple)) and argument.elts:
        first = argument.elts[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            value = first.value
    if not value:
        return None
    try:
        return shlex.split(value)[0]
    except (ValueError, IndexError):
        return None


def _is_repository_script(command: str, source_dir: Path, repo_root: Path) -> bool:
    if re.match(r"(?:<skill-dir>|\$\{?SKILL_DIR\}?)/scripts/", command, re.IGNORECASE) and Path(command).suffix in {".py", ".sh", ".js", ".ts"}:
        return True
    candidate = Path(command)
    if not candidate.is_absolute():
        candidate = source_dir / candidate
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(repo_root.resolve())
        return resolved.suffix in {".py", ".sh", ".js", ".ts"}
    except ValueError:
        return False


def javascript_source_evidence(path: Path) -> list[tuple[int, str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    pattern = re.compile(
        r"(?:\bimport\s+(?:[^'\";]+?\s+from\s+)?|\brequire\s*\(|\bimport\s*\()"
        r"['\"]([^'\"]+)['\"]"
    )
    result: list[tuple[int, str, str]] = []
    for match in pattern.finditer(text):
        module = match.group(1)
        if module.startswith((".", "/", "node:")):
            continue
        root = "/".join(module.split("/")[:2]) if module.startswith("@") else module.split("/", 1)[0]
        if root not in NODE_BUILTINS:
            result.append((text[:match.start()].count("\n") + 1, "js-import", root))
    return sorted(set(result))
