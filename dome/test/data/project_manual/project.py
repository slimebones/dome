from dome import sdk

project_id = "project-1"

async def build():
    sdk.init_build()
    sdk.generate_build_info("build.py")
    sdk.generate_codes("codes.py")
    sdk.include_python()


modules = {
    "module_a": {
        "id": "example.module_a",
        "version": "latest",
    },
    "module_b": {
        "id": "example.module_b",
        "version": "latest",
    },
}