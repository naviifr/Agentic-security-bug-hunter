import subprocess
import json
import re
from core.config import CLANG
                    
    
def build_fuzzer(file, collect_evidence):

    stage = "build_fuzzer"
    command = [
        CLANG,
        "-g", 
        "-fsanitize=fuzzer,address",
        file,
        "./target/libfuzz/fuzz_target.c",
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
         "./target/libfuzz/corpus",
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


def json_write(evidence):

    with open(f'./results/libfuzz.json', 'w') as file:
        json.dump(evidence, file, indent= 4)


def parse_output(Result,stderr):

    output = {}

    if stderr:

        error_type = re.search(
                            r"ERROR:\s*AddressSanitizer:\s*([^\s]+)",stderr
                        )
        operation = re.search(
                            r"\b(READ|WRITE)\s+of\s+size\s+(\d+)", stderr
                        )
        location = re.search(
                            r"process_input.*?([A-Za-z]:\\[^:\r\n]+):(\d+)", stderr
                        )
        reproducer = re.search(
                            r"(crash-[a-fA-F0-9]+)", stderr
                        )
        if error_type:
            output["error"] = error_type.group(1)
        if operation:
            output["operation"] = operation.group(1)
            output["operation_size"] = int(operation.group(2))
        if location:
            output["location"] = location.group(1)
            output["line"] = int(location.group(2))
        if reproducer:
            output["reproducer"] = reproducer.group(1)


    Result.plg_data["libfuzz"] = output
    Result.evidence["libfuzz"] = EVIDENCE


def libfuzzer_initiate(Result):
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
        json_write(EVIDENCE)


