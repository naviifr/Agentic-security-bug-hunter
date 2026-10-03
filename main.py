from analysis import semgrep, libfuzzer
import core.verify as verify
from core.models import Result
import agent.context as cntxt
import agent.client
from core.patch import patch_initiate, reverse_patch

MAX_ATTEMPTS = 3

file_path = "./target/libfuzz/target.c"
patch_path = "./results/candidate.patch"

result = Result(file_path)
prev_attempts = []

libfuzzer.libfuzzer_initiate(result)
semgrep.semgrep_initiate(result)

for i in range(MAX_ATTEMPTS):

    context = cntxt.build_context(result, prev_attempts)
    prompt = agent.client.build_prompt(context)
    response = agent.client.generate_patch(prompt)
    patch = patch_initiate(response, result.file, patch_path, result)

    if not patch:
        print(result.errors["patch"])
        cntxt.record_attempts(prev_attempts, result, response)
        continue

    verify.verify_initiate(result)
    
    if result.evidence["verification"]["verification_passed"]:
        break

    print(result.errors["verify"])
    rollback = reverse_patch(patch_path)

    if not rollback:
        break

    cntxt.record_attempts(prev_attempts, result, response)
