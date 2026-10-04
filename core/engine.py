from analysis import semgrep, libfuzzer
import core.verify as verify
from core.models import Result
import agent.context as cntxt
import agent.client
from core.patch import patch_initiate, reverse_patch

class Engine:

    def __init__(self, max_attempts=3):
        self.max_attempts = max_attempts

    def start(self, patch_path, result:Result):

        final_status = "ATTEMPTS_EXHAUSTED"
        prev_attempts = []

        libfuzzer.libfuzzer_initiate(result)
        semgrep.semgrep_initiate(result)

        for i in range(self.max_attempts):

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
                final_status = "PATCH_ACCEPTED"
                break

            print(result.errors["verify"])
            rollback_status = reverse_patch(patch_path)

            if not rollback_status:
                final_status = "ROLLBACK_FAILED"
                break

            cntxt.record_attempts(prev_attempts, result, response)

        return final_status