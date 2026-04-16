import importlib.util
import os
import re
import subprocess

from dome import core, project, runargs


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
    parse_tuple = project.parse(args.projectfile, args)
    if parse_tuple is None:
        return
    p, pm = parse_tuple

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
    print_row("Id", p.id)
    if p.name:
        print_row("Name", p.name)
    if p.description:
        print_row("Description", p.description)
    print_row("Lines", f"{total_code_lines:,}")
    print_row("Files", code_file_count)
    if biggest_code_lines[1]:
        print_row("Biggest", biggest_code_lines[1])
    print_row("Branch", branch)
    print_row("Changes", f"{changes} pending")
    print("-" * 69)
