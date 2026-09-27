import subprocess
import json

def analyze():
    stage = "analyze"
    command = [
        "semgrep",
        r"--config=./rules/memory.yml",
        "--json",
        "./target/semgrep/static.c"
    ]

    result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

    if result.returncode == 0:
        print("Analysis successful")
        EVIDENCE["stages"][stage] = True
        EVIDENCE[stage] = {"passed": True,
                           "return_code": result.returncode,
                           "stdout": result.stdout,
                           "stderr": result.stderr}

    else:
        EVIDENCE["stages"][stage] = False
        EVIDENCE[stage] = {"passed": False,
                            "return_code": result.returncode,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            }
        raise Exception(f"Error Occured while analyzing:\n{result.stderr}")
                

def write_json(parsed_data, output):
    
    with open(f'./results/semgrep.json', 'w') as file:
            json.dump(parsed_data, file, indent= 4)
            json.dump(output, file, indent= 4)


def parse_json(data, Result):

    output = json.loads(data)
    results = output["results"]
    findings = []

    for i in results:
        finding = {
            "rule_id": i["check_id"],
            "file": i["path"],
            "start_line": i["start"]["line"],
            "start_col": i["start"]["col"],
            "end_line": i["end"]["line"],
            "end_col": i["end"]["col"],
            "message": i["extra"]["message"],
            "severity": i["extra"]["severity"]
        }
        findings.append(finding)

    Result.plg_data['semgrep'] = findings
    Result.evidence['semgrep'] = EVIDENCE
    return findings

def semgrep_initiate(Result):
    global EVIDENCE
    
    EVIDENCE = {"semgrep_completed":'',
            "stages":{}}
    
    try:
        analyze()
        parsed_data = parse_json(EVIDENCE["analyze"]["stdout"], Result)
        write_json(parsed_data, EVIDENCE)
        EVIDENCE["semgrep_completed"] = True
        print("semgrep done")

    except Exception as e:
        print("semgrep Failed")
        EVIDENCE["semgrep_completed"] = False
        Result.errors["semgrep"] = str(e)


