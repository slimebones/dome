import importlib.util

import colorama

from core import CodeError
import const
import core


async def run(args):
    function_name = args.args.function_name
    function_args = args.args.positional
    function_kwargs = dict(args.args.kw if args.args.kw else {})
    spec = importlib.util.spec_from_file_location("projectfile", args.projectfile)
    if spec is None or spec.loader is None:
        core.error(f"projectfile is not found at '{args.projectfile}'")
        return
    project_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project_module)

    project_id = project_module.id
    args.response()
    args.response(f"== execute: {colorama.Fore.CYAN}{project_id}{colorama.Fore.RESET} ==")

    target_function = getattr(project_module, function_name, None)
    if target_function is None:
        core.error(f"function '{function_name}' is not found")
        return
    try:
        target_function(*function_args, **function_kwargs)
    except Exception as e:
        core.error(f"during execution of function '{function_name}', an error occurred: {e}")