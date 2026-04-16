from dome import sdk

project_id = "project-1.py"

async def build():
    sdk.generate_build_info()
    sdk.generate_codes()
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