import asyncio
import importlib.util
import re

import colorama

import core
import sdk


def _is_valid_id(id_string: str) -> bool:
    # ^[a-z-]       -> Part 1: starts with lowercase letter or hyphen
    # [a-z0-9-]*    -> Part 1: remaining lowercase alnum or hyphen
    # \.            -> Literal dot
    # [a-z-]        -> Part 2: starts with lowercase letter or hyphen
    # [a-z0-9-]*$   -> Part 2: remaining lowercase alnum or hyphen
    pattern = r"^[a-z-][a-z0-9-]*\.[a-z-][a-z0-9-]*$"

    return bool(re.match(pattern, id_string))


async def run(args, *, instruction: str | None = None):
    spec = importlib.util.spec_from_file_location("projectfile", args.projectfile)
    if spec is None or spec.loader is None:
        core.error(f"projectfile is not found at '{args.projectfile}'")
        return
    project_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project_module)

    project_id = getattr(project_module, "id", None)
    if project_id is None:
        core.error(f"project.py must define 'id'")
        return
    if not isinstance(project_id, str):
        core.error(f"project.py:id must be a string")
        return
    project_id = project_id.strip().lower()
    if not _is_valid_id(project_id):
        core.error(f"incorrect id '{project_id}', must follow the form 'domain.id'")
    try:
        tech, shortid = project_id.split(".")
    except ValueError:
        assert False, "must be regex-protected"

    project_name = getattr(project_module, "name", None)
    if project_name is not None and not isinstance(project_name, str):
        core.error(f"project.py:name must be a string")
        return
    if project_name is not None:
        project_name = project_name.strip()
    project_description = getattr(project_module, "description", None)
    if project_description is not None and not isinstance(project_description, str):
        core.error(f"project.py:description must be a string")
        return
    if project_description is not None:
        project_description = project_description.strip()

    args.response()
    args.response(f"== execute: {colorama.Fore.CYAN}{project_id}{colorama.Fore.RESET} ==")

    # intentional private call to secure sdk namespace
    sdk._set_context(sdk.ProjectFunctionContext(
        id=project_id,
        tech=tech,
        shortid=shortid,
        name=project_name,
        description=project_description,
        args=args.args,
        cwd=args.cwd,
        version=args.version,
        debug=args.debug,
        mode=args.mode,
        projectfile=args.projectfile,
        build_dir=args.build_dir,
        source=args.source,
    ))

    if instruction is None:
        function_name = args.args.function_name
        function_args = args.args.positional
        function_kwargs = dict(args.args.kw if args.args.kw else {})

        target_function = getattr(project_module, function_name, None)
        if target_function is None:
            core.error(f"function '{function_name}' is not found")
            return
        try:
            await target_function(*function_args, **function_kwargs)
        except Exception as e:
            core.error(f"during execution of function '{function_name}', an error occurred: {e}")
            return
    else:
        exec_globals = {"asyncio": asyncio}

        try:
            exec(f"async def __async_task:\n{[f'    {line}\n' for line in instruction.splitlines()]}", exec_globals)
            await exec_globals["__async_task"]()  # type: ignore
        except Exception as e:
            core.error(f"during execution of instruction '{instruction}', an error occurred: {e}")
            return
