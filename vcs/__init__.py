from core import CodeError
import core
import subprocess
from pathlib import Path
import re
from typing import Callable

_git_files_cmd = "git ls-files --other --modified --exclude-standard"
_git_commit_cmd = "git add . && git commit -m \"{0}\""
_git_title_core = "Update {0}"
_git_title_extra_limit = 50
_ansi_red = "\033[31m"
_ansi_reset = "\033[0m"


def _merge_consecutive_spaces(text):
    return re.sub(r"[ \t]+", " ", text)


def _decisive_call(command: str) -> tuple[str, int]:
    process = subprocess.run(command, shell=True, text=True, capture_output=True)
    if process.returncode == 0:
        return process.stdout, 0
    else:
        return process.stderr, 1


async def _commit(args):
    # Check if any of non-gitignored files contain unescaped '@nocommit'. @ignore
    # Note that only cwd-child files are inspected, and we don't inspect all git root -
    # this is logical, since we commit only the cwd's files.
    grep, e = _decisive_call("git grep @nocommit")  # @ignore
    # `git grep` returns error if search was unsuccessful, so we treat error positively.
    if e == 0:
        grep_lines = grep.splitlines()
        for line in grep_lines:
            if "@ignore" not in line:
                merged = _merge_consecutive_spaces(line).strip()
                args.response(f"{_ansi_red}CANNOT COMMIT{_ansi_reset}: tag '@nocommit' found in context (spaces merged):\n\t'{merged}'")  # @ignore
                args.response("To ignore: place '@ignore' tag on the same line as '@nocommit'.")
                exit(1)

    p = subprocess.run(_git_files_cmd, shell=True, text=True, stdout=subprocess.PIPE)
    if p.returncode > 0:
        args.response(f"'git ls-files' process returned code {p.returncode}, error content is: {p.stderr}")
        exit(p.returncode)
    stdout = p.stdout
    if stdout == "":
        args.response("Nothing to commit.")
        exit(1)

    raw_names = list(filter(
        lambda l: l and not l.isspace(), stdout.split("\n")))
    # collect filenames, put them up until limit is reached
    extra = ""
    names = [raw_name.split("/")[-1] for raw_name in raw_names]
    names_len = len(names)
    for i, name in enumerate(names):
        fname = name
        # not last name receive comma
        if i + 1 < names_len:
            fname += ", "
        if len(extra) + len(name) >= _git_title_extra_limit:
            extra += "..."
            break
        extra += fname

    core = _git_title_core.format(extra)

    if not core or core.isspace() or names_len == 0:
        args.response(
            "Failed to find commited files info in git ls files stdout:"
            f" {stdout}")
        exit(1)

    p = subprocess.run(
        _git_commit_cmd.format(core),
        shell=True,
        text=True,
        stdout=subprocess.PIPE)
    if p.returncode > 0:
        args.response(
            f"Failed to commit: git returned code {p.returncode},"
            f" error content is: {p.stderr}")
        exit(p.returncode)
    args.response(f"Commited {len(raw_names)} entries with message \"{core}\"")


async def _push(args):
    stdout, stderr, e = core.call("git push")
    if e > 0:
        args.response(f"project push finished with code #{e}")
    args.response(stdout, end="")
    args.response(stderr, end="")

    stdout, stderr, e = core.call("git push --tags")
    if e > 0:
        args.response(f"project push tags finished with code #{e}")
    args.response(stdout, end="")
    args.response(stderr, end="")


async def _update(args):
    stdout, stderr, e = core.call("git pull")
    if e > 0:
        args.response(f"project update finished with code #{e}")
    args.response(stdout, end="")
    args.response(stderr, end="")


async def run(args):
    target = args.vcs

    match target:
        case "commit":
            await _commit(args)
        case "push":
            await _push(args)
        case "update":
            await _update(args)
        case _:
            raise CodeError(1, f"unrecognized target '{target}'")