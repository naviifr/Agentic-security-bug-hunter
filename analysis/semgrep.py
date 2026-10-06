import subprocess
import json
import re
from core.models import Result

def analyze(file):
    stage = "analyze"
    command = [
        "semgrep",
        r"--config=./rules/memory.yml",
        "--json",
        file
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

    data = []
    data.append(parsed_data)
    data.append(output)
    
    with open(f'./results/semgrep.json', 'w') as file:
            json.dump(data, file, indent= 4)


def parse_json(data, Result:Result):

    output = json.loads(data)
    results = output["results"]
    findings = []
    count = 0
    function_pattern = r'^\s*(?:[A-Za-z_]\w*\s+|\*+\s*)*([A-Za-z_]\w*)\s*\([^;{}]*\)\s*$'

    for i in results:
        count+=1
        current_function_name = None
        brace_depth = 0
        pending_function_name = None
        path = './' + i['path']
        path = path.replace("\\",'/')

        with open(path, 'r') as file:
            lines = file.readlines()

        for line_no, line_data in enumerate(lines, start=1):
            if line_no > i["start"]["line"]:
                break

            if brace_depth == 0:
                match = re.search(function_pattern, line_data)
                if match:
                    pending_function_name = match.group(1)

                if pending_function_name and "{" in line_data:
                    current_function_name = pending_function_name
                    pending_function_name = None

            brace_depth += line_data.count("{") - line_data.count("}")

            if current_function_name and brace_depth == 0:
                current_function_name = None

    
        finding = {
            "id": f"semgrep-{count:03d}",
            "rule_id": i["check_id"],
            "file": i["path"],
            "function": str(current_function_name),
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


def semgrep_initiate(Result:Result):
    global EVIDENCE
    
    EVIDENCE = {"semgrep_completed":'',
            "stages":{}}
    
    try:
        analyze(Result.file)
        parsed_data = parse_json(EVIDENCE["analyze"]["stdout"], Result)
        write_json(parsed_data, EVIDENCE)
        EVIDENCE["semgrep_completed"] = True
        print("semgrep done")

    except Exception as e:
        print("semgrep Failed")
        EVIDENCE["semgrep_completed"] = False
        Result.errors["semgrep"] = str(e)


