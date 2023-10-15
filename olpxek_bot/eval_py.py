from RestrictedPython import compile_restricted_eval
from RestrictedPython import (
    limited_builtins,
    # PrintCollector,
    safe_builtins,
    utility_builtins,
)
from RestrictedPython.Eval import default_guarded_getitem
from RestrictedPython.Guards import (
    # guarded_setattr,
    # guarded_delattr
    full_write_guard,
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
    safer_getattr,
)


def eval_py(source: str) -> str:
    builtins = safe_builtins.copy()
    builtins.update(utility_builtins)
    builtins.update(limited_builtins)
    restricted_globals = {
        "__builtins__": builtins,
        # '_print_': PrintCollector,
        "_getattr_": safer_getattr,
        "_write_": full_write_guard,
        # "_getiter_": iter,
        "_getitem_": default_guarded_getitem,
        "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        "_unpack_sequence_": guarded_unpack_sequence,
    }

    compiled = compile_restricted_eval(source)
    if compiled.errors:
        return ", ".join(compiled.errors)
    try:
        ret = eval(compiled.code, restricted_globals)  # noqa: S307
        return str(ret)
    except Exception as e:
        return str(e)
