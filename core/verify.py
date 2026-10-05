import subprocess
import json
from analysis.libfuzzer import build_fuzzer, run_fuzzer
from core.config import CLANG


def build_regression_test():

    stage = "build_regression_test"
    command = [
        CLANG,
        "-g",
        "-fsanitize=address",
        "./target/libfuzz/target.c",
        "./target/libfuzz/test_target.c",
        "-o",
        "./builds/test.exe",
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("Build successful")
        collect_evidence(stage, True, result)
    else:
        collect_evidence(stage, False, result)
        raise Exception(f"Build Failed:\n{result.stderr}")

def verify_test():

    stage = "verify_test"
    command = [
        "./builds/test.exe"
    ]

    result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )
    
    if result.returncode == 0:
        print("Verified")
        collect_evidence(stage, True, result)
    else:
        collect_evidence(stage, False, result)
        print("Verification failed")
        raise Exception(f"Verification failed:\n{result.stderr}\n{result.stdout}")
    
def replay_crash(reproducer:str):
    
    stage = "replay_crash"
    command = [
            "./builds/fuzzer.exe",
            reproducer
        ]

    result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )

    if result.returncode == 0:
        print("Crash replayed, nothing detected")
        collect_evidence(stage, True, result)
    else:
        collect_evidence(stage, False, result)
        print("Crash replayed, crash detected")
        raise Exception(f"Crash detected\n{result.stderr}")

def json_write(evidence, Result):

    with open(f'./results/verification.json', 'w') as file:
        json.dump(evidence, file, indent= 4)
    Result.evidence["verification"] = evidence


def collect_evidence(stage:str, passed:bool, result:subprocess.CompletedProcess):

    EVIDENCE["stages"][stage] =  passed
    EVIDENCE[stage] = {
                        "passed":passed,
                        "return_code":result.returncode,
                        "stdout":result.stdout,
                        "stderr":result.stderr,
                    }


def verify_initiate(Result):
    global EVIDENCE
    EVIDENCE= {"verification_passed": '',
           "stages":{}}

    Result.errors.pop("verify", None)
    try:
        build_regression_test()
        verify_test()
        build_fuzzer(Result.file, collect_evidence)

        if Result.plg_data['libfuzz'].get('reproducer') == None:
            raise Exception("reproducer not found")
        else:
            replay_crash(Result.plg_data['libfuzz']['reproducer'])
            
        status = run_fuzzer(collect_evidence)
        if status:
            EVIDENCE["verification_passed"] = True
            print("Patch Successful")
        else:
            EVIDENCE["verification_passed"] = False
            EVIDENCE["run_fuzzer"]["passed"] =  False
            print("Patch Unsuccessful")

    except Exception as e:
        EVIDENCE["verification_passed"] = False
        Result.errors["verify"] = str(e)
    
    finally:
        json_write(EVIDENCE, Result)
