import subprocess

def validate_patch(diff: str, expected_file:str):

    expected_file = expected_file.replace("\\", "/")
    if expected_file.startswith("./"):
        expected_file = expected_file[2:]

    old_header = f"--- a/{expected_file}"
    new_header = f"+++ b/{expected_file}"

    if not diff or not diff.strip():
        print("empty patch")
        return False

    if diff.strip().startswith("NEED_MORE_CONTEXT"):
        print("NEED_MORE_CONTEXT")
        return False

    if old_header not in diff:
        print("missing old file header")
        return False

    if new_header not in diff:
        print("missing new file header")
        return False

    if not any( line.startswith("@@") and "@@" in line[2:]
                for line in diff.splitlines()
                ):
        print("no diff hunk" )
        return False

    for line in diff.splitlines():
        if line.startswith("--- a/"):
            path = line[len("--- a/"):]

            if path != expected_file:
                print(f"unexpected file: {path}")
                return False

        if line.startswith("+++ b/"):
            path = line[len("+++ b/"):]

            if path != expected_file:
                print(f"unexpected file: {path}")
                return False

    return True

def write_patch(diff:str, path:str):
    try:
        with open(path, "w", encoding="utf-8") as f:
            if not diff.endswith("\n"):
                diff += "\n"
            f.write(diff)
        return True
    except Exception as e:
        print("Could not write into the file",e)
        return False

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
        return True
        
    else:
        print(f"Diff doesn't apply:\n{result.stderr}")
        return False

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
        return True
    else:
        print(f"Diff wasnt applied:\n{result.stderr}")
        return False

def patch_initiate(diff:str, file_path:str, patch_path:str):

    if not ( 
            validate_patch(diff, file_path) and
            write_patch(diff, patch_path) and
            check_patch(patch_path) and
            apply_patch(patch_path) 
            ) : 
        return False
    
    return True

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