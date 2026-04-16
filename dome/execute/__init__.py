import asyncio
import importlib.util
from pathlib import Path
import re
import subprocess

import colorama

from dome import core, project
from dome import const
from dome import sdk
from dome.runargs import RunArgs


async def run(args: RunArgs):
    if args.args.all:
        # find all projects respecting gitignore
        try:
            result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", "--cached"],
                capture_output=True,
                text=True,
                check=True
            )
            tracked_files = set(result.stdout.splitlines())
        except subprocess.CalledProcessError:
            tracked_files = set()

        paths = []
        for p in Path(".").rglob("project.py"):
            rel_p = str(p.relative_to(".")).replace("\\", "/")
            if rel_p in tracked_files:
                paths.append(p)

        for p in paths:
            await _execute_project(p, args)
    else:
        await _execute_project(args.projectfile, args)


async def _execute_project(path: Path, args: RunArgs):
    parse_tuple = project.parse(path, args)
    if parse_tuple is None:
        return
    p, pm = parse_tuple
    function_name = args.args.function_name
    function_args = args.args.positional
    function_kwargs = dict(args.args.kw if args.args.kw else {})

    args.response()
    args.response(f"{const.grey}<<< execute {colorama.Fore.YELLOW}{p.id}{const.grey}::{colorama.Fore.GREEN}{function_name}{colorama.Fore.RESET} {const.grey}>>>{const.reset}")

    # intentional private call to secure sdk namespace
    sdk._set_project(p)

    target_function = getattr(pm, function_name, None)
    if target_function is None:
        core.error(f"function '{function_name}' is not found")
        return
    try:
        await target_function(*function_args, **function_kwargs)
    except Exception as e:
        core.error(f"during execution of function '{function_name}', an error occurred: {e}", e)
        return
