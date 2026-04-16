import asyncio
import importlib.util
from pathlib import Path
import re

import colorama

from dome import core, project
from dome import sdk
from dome.runargs import RunArgs


async def run(args: RunArgs):
    if args.args.all:
        paths = list(Path(".").rglob("project.py"))
        for p in paths:
            await _execute_project(p, args)
    else:
        await _execute_project(args.projectfile, args)


async def _execute_project(path: Path, args: RunArgs):
    parse_tuple = project.parse(path, args)
    if parse_tuple is None:
        return
    p, pm = parse_tuple

    args.response()
    args.response(f"== execute: {colorama.Fore.CYAN}{p.id}{colorama.Fore.RESET} ==")

    # intentional private call to secure sdk namespace
    sdk._set_project(p)

    function_name = args.args.function_name
    function_args = args.args.positional
    function_kwargs = dict(args.args.kw if args.args.kw else {})

    target_function = getattr(pm, function_name, None)
    if target_function is None:
        core.error(f"function '{function_name}' is not found")
        return
    try:
        await target_function(*function_args, **function_kwargs)
    except Exception as e:
        core.error(f"during execution of function '{function_name}', an error occurred: {e}", e)
        return
