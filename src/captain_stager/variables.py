import re
from captain_core.errors import ManifestError

_PATTERN=re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
def substitute(value: str, variables: dict[str,str], field_name: str) -> str:
    def repl(m):
        key=m.group(1)
        if key not in variables: raise ManifestError(f"{field_name} references undefined variable: {key}")
        return variables[key]
    return _PATTERN.sub(repl,value)
