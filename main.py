from analysis import semgrep, libfuzzer
import verify
from core.models import Result
import agent.context as cntxt
import agent.client
from core.patch import patch_initiate, reverse_patch

file_path = "./target/libfuzz/target.c"
patch_path = "./results/candidate.patch"
result = Result(file_path)

libfuzzer.libfuzzer_initiate(result)
semgrep.semgrep_initiate(result)

context = cntxt.build_context(result)
prompt = agent.client.build_prompt(context)
response = agent.client.generate_patch(prompt)
patch = patch_initiate(response, result.file, patch_path)

if patch:
    verify.verify_initiate(result)
    if not result.evidence["verification"]["verification_passed"]:
        reverse_patch(patch_path)
