from core.models import Result
from dataclasses import asdict

def read_source(path):

    target = {"file": path,
              "source": ''}

    with open(path, 'r') as file:
        target['source'] = file.read()

    return target

def build_context(Result:Result, previous_attempts):
    CONTEXT = {}

    CONTEXT['target'] = read_source(Result.file)
    for i in Result.findings:
        find_dict = []
        find_dict.append(asdict(i))
        CONTEXT['findings'] = find_dict
    CONTEXT['errors'] = Result.errors
    CONTEXT['previous_attempts'] = previous_attempts

    return CONTEXT

def record_attempts(previous_attempts: list, Result, patch):

    previous_attempts.append({
        "patches": patch,
        "errors": {
            "verify": Result.errors.get("verify"),
            "patch": Result.errors.get("patch")
            }
        })