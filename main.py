from core.models import Result
from core.engine import Engine


root_path = "."
file_path = "./target/target.c"
patch_path = "./results/candidate.patch"

result = Result(root_path, file_path, [])

engine = Engine()
status = engine.start(patch_path, result)

print(status)