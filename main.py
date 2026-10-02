from analysis import semgrep, libfuzzer
import verify
from core.models import Result
import agent.context as cntxt
import agent.client
from core.patch import patch_initiate

file_path = "./target/libfuzz/target.c"
result = Result(file_path)

libfuzzer.libfuzzer_initiate(result)
semgrep.semgrep_initiate(result)

context = cntxt.build_context(result)
prompt = agent.client.build_prompt(context)
response = agent.client.generate_patch(prompt)
patch = patch_initiate(response, result.file, "./results/candidate.patch")

verify.verify_initiate(result)
