import asyncio
from pathlib import Path

from dotenv import load_dotenv
import core
import execute
from runargs import RunArgs
import vc

core.init("dome")
import argparse

cwd = Path.cwd()
build_dir = Path(cwd, ".build")
target_version = "latest"
target_mode = "default"
target_debug = False


def _response(m: str = "", *, end: str = "\n"):
    print(m, end=end)


async def main():
    await core.ainit()

    main_parser = argparse.ArgumentParser()
    main_parser.add_argument("-v", type=str, default="0.0.0", dest="version")
    main_parser.add_argument("-m", type=str, default="default", dest="mode")
    main_parser.add_argument("-d", action="store_true", dest="debug")
    main_parser.add_argument("-cwd", type=Path, dest="cwd", default=Path.cwd())

    module_subparser = main_parser.add_subparsers(title="Modules", help="Modules.", dest="module")


    # execute
    parser = module_subparser.add_parser("execute", help="Executes a function from the cwd's projectfile.")
    parser.add_argument("function_name", type=str)
    parser.add_argument("positional", nargs="*", help="Positional arguments to a project's function.")
    parser.add_argument("--kw", action="append", nargs=2, metavar=("KEY", "VALUE"), help="Keyword arguments to a project's function.")


    # status
    module_subparser.add_parser("status", help="Show project status.")


    # vc
    vc_parser = module_subparser.add_parser("vc", help="Version Control System")
    vc_subparser = vc_parser.add_subparsers(title="vc", help="vc actions.", dest="vc")
    # vc.commit
    vc_subparser.add_parser("commit", help="Commit changes.")
    # vc.push
    vc_subparser.add_parser("push", help="Push changes.")
    # vc.update
    vc_subparser.add_parser("update", help="Update from version control.")
    # vc.status
    vc_subparser.add_parser("status", help="Show version control status.")


    # package
    package_parser = module_subparser.add_parser("package", help="Packaging.")
    package_subparser = package_parser.add_subparsers(title="Package", help="Packaging actions.", dest="package")
    # package.add
    parser = package_subparser.add_parser("add", help="Adds a package.")
    parser.add_argument("package", type=str)
    parser.add_argument("version", type=str, default="latest")
    parser.add_argument("output", type=Path, default=None)
    # package.upload
    parser = package_subparser.add_parser("upload", help="Uploads a module.")
    parser.add_argument("dir", type=Path)
    # package.install
    package_subparser.add_parser("install", help="Installs/Refreshes all project-specified packages.")


    args = main_parser.parse_args()
    global cwd
    cwd = args.cwd
    global build_dir
    build_dir = Path(cwd, "build")
    global target_version
    target_version = args.version
    global target_debug
    target_debug = args.debug
    global target_mode
    target_mode = args.mode

    try:
        args_kw = args.kw
    except Exception:
        args_kw = {}

    if args_kw is None:
        args_kw = {}

    projectfile = Path(cwd, "project.py")
    dotenvfile = Path(cwd, ".env")
    load_dotenv(dotenvfile)

    rargs = RunArgs(
        args=args,
        projectfile=projectfile,
        build_dir=build_dir,
        cwd=cwd,
        version=target_version,
        debug=target_debug,
        mode=target_mode,
        response=_response,
    )

    match args.module:
        case "execute":
            await execute.run(rargs)
        case "vc":
            await vc.run(rargs)
        case "template":
            raise NotImplementedError
        case "status":
            raise NotImplementedError
        case _:
            raise Exception(f"unrecognized command '{args.command}'")
    _response()


if __name__ == "__main__":
    asyncio.run(main())
