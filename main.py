from core.models import Result
from core.engine import Engine


file_path = "./target/target.c"
patch_path = "./results/candidate.patch"

result = Result(file_path, [])

engine = Engine()
status = engine.start(patch_path, result)

print(status)