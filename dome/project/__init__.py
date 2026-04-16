import importlib.util
from pathlib import Path
import re
from types import ModuleType

from dome import core
from dome.model import Model
from dome.runargs import RunArgs


class Project(Model):
    id: str
    shortid: str
    tech: str
    name: str | None
    description: str | None

    args: dict
    cwd: Path
    version: str
    debug: bool
    mode: str

    file_path: Path
    source_dir: Path
    build_dir: Path

    umbrella_file_path: Path
    umbrella_source_dir: Path
    umbrella_build_dir: Path


def _is_valid_id(id_string: str) -> bool:
    # ^[a-z-]       -> Part 1: starts with lowercase letter or hyphen
    # [a-z0-9-]*    -> Part 1: remaining lowercase alnum or hyphen
    # \.            -> Literal dot
    # [a-z-]        -> Part 2: starts with lowercase letter or hyphen
    # [a-z0-9-]*$   -> Part 2: remaining lowercase alnum or hyphen
    pattern = r"^[a-z-][a-z0-9-]*\.[a-z-][a-z0-9-]*$"

    return bool(re.match(pattern, id_string))


def parse(path: Path, args: RunArgs) -> tuple[Project, ModuleType] | None:
    spec = importlib.util.spec_from_file_location("projectfile", path)
    if spec is None or spec.loader is None:
        core.error(f"projectfile is not found at '{path}'")
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # @todo enumerate all project_ fields and error on unreserved use

    project_id = getattr(module, "project_id", None)
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
        shortid, tech = project_id.split(".")
    except ValueError:
        assert False, "must be regex-protected"

    name = getattr(module, "project_name", None)
    if name is not None and not isinstance(name, str):
        core.error(f"project.py:name must be a string")
        return
    if name is not None:
        name = name.strip()
    description = getattr(module, "project_description", None)
    if description is not None and not isinstance(description, str):
        core.error(f"project.py:description must be a string")
        return
    if description is not None:
        description = description.strip()

    return Project(
        id=project_id,
        shortid=shortid,
        tech=tech,
        name=name,
        description=description,
        args=vars(args.args),
        cwd=args.cwd,
        version=args.version,
        debug=args.debug,
        mode=args.mode,

        file_path=path,
        # for now we always use "build" here. Maybe forever - we want standard practice applied.
        build_dir=Path(path.parent, "build"),
        source_dir=path.parent,

        umbrella_file_path=args.projectfile,
        umbrella_build_dir=args.build_dir,
        umbrella_source_dir=args.source,
    ), module