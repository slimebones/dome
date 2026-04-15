import importlib.util
import os
import re
import subprocess

from dome import core, runargs


def _get_git_info(command):
    try:
        return subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode().strip()
    except Exception as e:
        return "Not a git repo"


def _get_git_files():
    try:
        output = subprocess.check_output("git ls-files", shell=True, stderr=subprocess.STDOUT).decode().strip()
        return output.splitlines()
    except:
        return []


def is_code_file(file_path):
    code_extensions = {
        '.py', '.pyw', '.js', '.mjs', '.jsx', '.ts', '.tsx', '.c', '.cpp', '.h', '.hpp',
        '.cc', '.cxx', '.cs', '.java', '.rb', '.go', '.rs', '.php', '.sh', '.html',
        '.css', '.sql', '.kt', '.kts', '.swift', '.m', '.mm', '.lua', '.pl', '.pm',
        '.r', '.sc', '.scala', '.dart', '.jl', '.clj', '.cljs', '.edn', '.hs', '.erl',
        '.hrl', '.f', '.f90', '.asm', '.s', '.v', '.vhdl', '.vhd', '.yaml', '.yml',
        '.json', '.xml', '.toml', '.md', '.markdown', '.bat', '.ps1', '.bash',
        '.zig', '.odin', '.gd', '.tscn', '.tres', '.cpp', '.hpp', '.glsl', '.hlsl',
        '.vert', '.frag', '.geom', '.comp', '.nim', '.cr', '.ex', '.exs', '.erl',
        '.hrl', '.lisp', '.scm', '.ss', '.cl', '.ml', '.mli', '.fs', '.fsi', '.fsx',
        '.fsscript', '.v', '.sv', '.svh', '.pas', '.pp', '.inc', '.d', '.pwn',
        '.inc', '.nut', '.gm', '.as', '.adoc', '.rst', '.tex', '.bib'
    }
    return os.path.splitext(file_path)[1].lower() in code_extensions


def _is_valid_id(id_string: str) -> bool:
    # ^[a-z-]       -> Part 1: starts with lowercase letter or hyphen
    # [a-z0-9-]*    -> Part 1: remaining lowercase alnum or hyphen
    # \.            -> Literal dot
    # [a-z-]        -> Part 2: starts with lowercase letter or hyphen
    # [a-z0-9-]*$   -> Part 2: remaining lowercase alnum or hyphen
    pattern = r"^[a-z-][a-z0-9-]*\.[a-z-][a-z0-9-]*$"

    return bool(re.match(pattern, id_string))


async def run(args: runargs.RunArgs):
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


    tracked_files = _get_git_info("git ls-files").splitlines()
    code_file_count = 0
    total_code_lines = 0
    biggest_code_lines = [0, ""]

    for file_path in tracked_files:
        if os.path.isfile(file_path) and is_code_file(file_path):
            code_file_count += 1
            try:
                with open(file_path, "rb") as f:
                    l = sum(1 for _ in f)
                    if l > biggest_code_lines[0]:
                        biggest_code_lines[0] = l
                        biggest_code_lines[1] = file_path
                    total_code_lines += l
            except:
                continue

    branch = _get_git_info("git rev-parse --abbrev-ref HEAD")
    changes = _get_git_info("git status --short | wc -l")

    def print_row(title, content):
        title_width = 12
        gap = 4
        formatted_title = f"{title}:"
        print(f"{formatted_title:<{title_width}}{' ' * gap}{content}")

    print("-" * 69)
    print_row("Id", project_id)
    if project_name:
        print_row("Name", project_name)
    if project_description:
        print_row("Description", project_description)
    print_row("Lines", f"{total_code_lines:,}")
    print_row("Files", code_file_count)
    if biggest_code_lines[1]:
        print_row("Biggest", biggest_code_lines[1])
    print_row("Branch", branch)
    print_row("Changes", f"{changes} pending")
    print("-" * 69)
