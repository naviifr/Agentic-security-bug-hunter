from analysis import semgrep, libfuzzer
import verify
from core.models import Result

result = Result("/target/libfuzz/target.c")

try:
    libfuzzer.libfuzzer_initiate(result)
    semgrep.semgrep_initiate(result)
    verify.verify_initiate(result)
    print("done")

except Exception as e:
    print(str(e))