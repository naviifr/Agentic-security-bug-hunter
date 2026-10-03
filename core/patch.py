import subprocess

def validate_patch(diff: str, expected_file:str):

    expected_file = expected_file.replace("\\", "/")
    if expected_file.startswith("./"):
        expected_file = expected_file[2:]

    old_header = f"--- a/{expected_file}"
    new_header = f"+++ b/{expected_file}"

    if not diff or not diff.strip():
        raise Exception("empty patch")

    if diff.strip().startswith("NEED_MORE_CONTEXT"):
        raise Exception("NEED_MORE_CONTEXT")

    if old_header not in diff:
        raise Exception("missing old file header")

    if new_header not in diff:
        raise Exception("missing new file header")

    if not any( line.startswith("@@") and "@@" in line[2:]
                for line in diff.splitlines()
                ):
        raise Exception("no diff hunk" )

    for line in diff.splitlines():
        if line.startswith("--- a/"):
            path = line[len("--- a/"):]

            if path != expected_file:
                raise Exception(f"unexpected file: {path}")

        if line.startswith("+++ b/"):
            path = line[len("+++ b/"):]

            if path != expected_file:
                raise Exception(f"unexpected file: {path}")

def write_patch(diff:str, path:str):
    try:
        with open(path, "w", encoding="utf-8") as f:
            if not diff.endswith("\n"):
                diff += "\n"
            f.write(diff)
    except Exception as e:
        raise Exception(f"Could not write into the file: {e}")

def check_patch(path:str):

    command = [
            'git',
            "apply", 
            "--check",
            path
        ]
    
    result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

    if result.returncode == 0:
        print("Diff applies cleanly!")
        
    else:
        raise Exception(f"Diff doesn't apply:\n{result.stderr}")

def apply_patch(path:str):

    command = [
            'git',
            "apply",
            path
            ]
            
    result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
    
    if result.returncode == 0:
        print("Diff applied successfully")
    else:
        raise Exception(f"Diff wasnt applied:\n{result.stderr}")

def patch_initiate(diff:str, file_path:str, patch_path:str, Result):

    Result.errors.pop("patch", None)
    try:
        validate_patch(diff, file_path)
        write_patch(diff, patch_path)
        check_patch(patch_path)
        apply_patch(patch_path) 
        
        return True
    
    except Exception as e:
        Result.errors["patch"] = str(e)
        return False

def reverse_patch(path):
    command = [
                'git',
                "apply",
                "-R", 
                path
            ]
        
    result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

    if result.returncode == 0:
        print("Original file restored")
        return True
    else:
        print("Couldnt restore the file", result.stderr)
        return False