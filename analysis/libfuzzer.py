import subprocess
import json
import re
from core.config import CLANG
from core.models import Result
                    
    
def build_fuzzer(file, collect_evidence):

    stage = "build_fuzzer"
    command = [
        CLANG,
        "-g", 
        "-fsanitize=fuzzer,address",
        file,
        "./target/fuzz_target.c",
        "-o",
        "./builds/fuzzer.exe",
    ]

    result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

    if result.returncode == 0:
        print("Fuzzer build successful")
        collect_evidence(stage, True, result)
    else:
        collect_evidence(stage, False, result)
        raise Exception(f"Fuzzer build failed:\n{result.stderr}")


def run_fuzzer(collect_evidence):

    stage = "run_fuzzer"
    command = [
         "./builds/fuzzer.exe",
         "./target/corpus",
         "-max_total_time=10"
    ]

    result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
    collect_evidence(stage, True, result)
    if result.returncode == 0:
        return True
    else:
        return False


def collect_evidence(stage:str, passed:bool, result:subprocess.CompletedProcess):

    EVIDENCE["stages"][stage] =  passed
    EVIDENCE[stage] = {
                        "passed":passed,
                        "return_code":result.returncode,
                        "stdout":result.stdout,
                        "stderr":result.stderr,
                       }


def json_write(evidence, plg_data): 

    data = []
    data.append(plg_data)
    data.append(evidence)

    with open(f'./results/libfuzz.json', 'w') as file:
        json.dump(data, file, indent= 4)


def parse_output(Result: Result,stderr):
    
    count = 1
    output = {
        "id":f"libfuzz-{count:03d}",
    }

    if stderr:

        error_type = re.search(
                            r"ERROR:\s*AddressSanitizer:\s*([^\s]+)",stderr
                        )
        operation = re.search(
                            r"\b(READ|WRITE)\s+of\s+size\s+(\d+)", stderr
                        )
        reproducer = re.search(
                            r"(crash-[a-fA-F0-9]+)", stderr
                        )
        #location
        output["frames"] = filter_stack(Result.file, stderr, EVIDENCE)
            
        if error_type:
            output["error"] = error_type.group(1)

        if operation:
            output["operation"] = operation.group(1)
            output["operation_size"] = int(operation.group(2))
            
        if reproducer:
            output["reproducer"] = reproducer.group(1)

    result_list = []
    result_list.append(output)
    Result.plg_data["libfuzz"] = result_list
    Result.evidence["libfuzz"] = EVIDENCE

def filter_stack(file, stderr, evidence):
    from pathlib import Path

    root = Path(file).resolve().parent.parent
    
    pattern = re.compile(r"^\s*#\d+\s+0x[0-9a-fA-F]+\s+in\s+(.+?)\s+([A-Za-z]:\\.+?):(\d+)(?::\d+)?$")
    stack_trace = []
    filtered_frames = []

    for line in stderr.splitlines():
        line = line.strip()
        match = pattern.match(line)
        if line.startswith("Address ") and "is located in" in line:
            break
        if match:
            stack_trace.append({
                    "file": match.group(2),
                    "function": match.group(1),
                    "line": int(match.group(3)),
                })
            frame_path = Path(match.group(2)).resolve()
            try:
                frame_path.relative_to(root)
                filtered_frames.append({
                    "file": match.group(2),
                    "function": match.group(1),
                    "line": int(match.group(3)),
                })
            except ValueError:
                pass

    evidence["stack"] = stack_trace
    return filtered_frames

def libfuzzer_initiate(Result: Result):
    global EVIDENCE
    EVIDENCE= {"libfuzz_completed": '',
           "stages":{}}
    try:

        build_fuzzer(Result.file, collect_evidence)
        print("No error detected") if run_fuzzer(collect_evidence) else print("Error detected")
        parse_output(Result, EVIDENCE["run_fuzzer"]["stderr"])
        print("Fuzzing done")
        EVIDENCE["libfuzz_completed"] = True

    except Exception as e:
        EVIDENCE["libfuzz_completed"] = False
        print("Fuzzing Failed")
        Result.errors["libfuzz"] = str(e)

    finally:
        json_write(EVIDENCE, Result.plg_data["libfuzz"])


