from analysis import semgrep, libfuzzer
import verify
from core.models import Result
import agent.context as cntxt
import agent.prompt
import agent.client

file_path = "./target/libfuzz/target.c"
result = Result(file_path)

libfuzzer.libfuzzer_initiate(result)
semgrep.semgrep_initiate(result)
verify.verify_initiate(result)

context = cntxt.build_context(result)
prompt = agent.prompt.build_prompt(context)
response = agent.client.generate_patch(prompt)
print(response)

