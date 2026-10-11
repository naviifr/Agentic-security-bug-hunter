from core.models import Result, Finding
from pathlib import Path

def mapper_initiate(Result:Result):

    for sg in Result.plg_data["semgrep"]:
        obj_instantiated = False
        semgrep_file = normalize_path(sg["file"])

        for lf in Result.plg_data["libfuzz"]:

            if obj_instantiated:
                break

            for frame in lf["frames"]:
                libfuzz_file = normalize_path(frame["file"])

                if semgrep_file != libfuzz_file:
                    continue

                if frame["function"] != sg["function"]:
                    continue

                if sg["start_line"] <= frame["line"] <= sg["end_line"]:
                    finding_obj = Finding(file=semgrep_file,
                                        function=sg["function"],
                                        line=sg["start_line"],
                                        cwe=sg["cwe"],
                                        confidence= sg["confidence"],
                                        source=["semgrep","libfuzz"]
                                        )
                    obj_instantiated = True
                    Result.findings.append(finding_obj)
                    break

        if not obj_instantiated:
            finding_obj = Finding(file=semgrep_file,
                                function=sg["function"],
                                line=sg["start_line"],
                                cwe=sg["cwe"],
                                confidence= sg["confidence"],
                                source=["semgrep"]
                                )
            Result.findings.append(finding_obj)
                    


def normalize_path(path):

    repo_root = Path.cwd().resolve()
    path = Path(path)

    if path.is_absolute():
        path = path.resolve().relative_to(repo_root)

    return path.as_posix()