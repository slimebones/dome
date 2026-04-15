def get_extension(tech: str) -> str:
    match tech:
        case "python":
            return "py"
        case "javascript":
            return "js"
        case "typescript" | "angular":
            return "ts"
        case "godot":
            return "gd"
        case _:
            return tech