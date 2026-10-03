import os
from dotenv import load_dotenv
import google.genai as genai
from google.genai import errors

load_dotenv()

api_key = os.environ["GEMINI_API_KEY"] #create a .env file and write GEMINI_API_KEY="yourapikey"
client = genai.Client(api_key=api_key)

def generate_patch(prompt:str):
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model = "gemini-3.6-flash",
                contents = prompt
            )

            if not response.text:
                raise Exception("LLM returned an empty response")

            else:
                print("Patch generated")
                return response.text
        
        except errors.ServerError as e:

            if e.code!=503 or attempt==2:
                print("Could not connect to the Agent")
                raise
        

def build_prompt(context):

    file = context["target"]["file"]
    file = file.replace("\\", "/")
    
    if file.startswith("./"):
        file = file[2:]

    prompt = f'''You are a senior C/C++ security engineer who writes minimal, surgical vulnerability patches. You favor the smallest correct fix over a clever or broad one.

    <task>
    Fix exactly one memory-safety or undefined-behavior vulnerability in the source file provided below. Base your fix only on the evidence provided. Do not extrapolate beyond it.
    </task>

    <rules>
    1. MUST change the fewest lines that remove the root cause. Fix the cause of the bug, not only the line where the sanitizer reported it.
    2. MUST NOT touch unrelated code: no refactoring, renaming, reformatting, whitespace changes, comment edits, added features, or "while I'm here" cleanups.
    3. MUST NOT modify the fuzz harness, test files, build files, or verify.py. Edit only the source file named in <source_file>.
    4. MUST preserve existing behavior for all valid inputs. Only the behavior on the crashing/malicious input may change.
    5. NEVER fix the crash by deleting functionality, adding a blanket early return, catching and hiding the failure, or special-casing the crashing input bytes.
    6. Use only functions and headers already available in the file or the C standard library. If you need a new #include, add only that one line.
    7. Base your response only on the provided context. If the evidence is insufficient to identify a root cause, do NOT guess: output the NEED_MORE_CONTEXT line described below.
    </rules>

    <evidence>
    <fuzzer_crash>
    {context["findings"]["libfuzz"]}
    </fuzzer_crash>

    <static_analysis>
    {context["findings"]["semgrep"]}
    </static_analysis>

    <source_file path="{file}">
    {context['target']['source']}
    </source_file>

    <errors>
    {context['errors']}
    </errors>
    </evidence>

    <previous_attempts>
    {context['previous_attempts']}
    </previous_attempts>

    <how_to_use_previous_attempts>
    Each previous attempt lists the diff you produced and the exact verify.py result. Treat the failure as the ground truth about what is still wrong:
    - "patch does not apply": your diff had wrong context lines or line numbers. Re-copy the context lines exactly from <source_file>.
    - "build failed": fix the compiler error shown; do not change approach unless the error shows the approach is invalid.
    - "PoV still crashes": your fix did not remove the root cause. Re-read the sanitizer stack trace and fix an earlier point in the data flow.
    - "regression test failed": your fix changed valid-input behavior. Narrow it.
    - "new crash found": your fix moved the bug. Fix the underlying invariant.
    NEVER repeat a diff that already failed. Each attempt must differ from all previous ones in substance.
    </how_to_use_previous_attempts>

    <output_format>
    Return ONLY a unified diff, and nothing else: no prose, no explanation, no markdown fences, no text before or after.

    Required format:
    --- a/{file}
    +++ b/{file}
    @@ -START,COUNT +START,COUNT @@
    context line (unchanged, exactly as in the source)
    -removed line
    +added line
    context line (unchanged, exactly as in the source)

    Diff rules:
    - Include 3 unchanged context lines before and after each change when available, copied character-for-character from <source_file> (line numbers in the prompt are for your reference only and MUST NOT appear in the diff).
    - Hunk header counts MUST match the number of lines in the hunk.
    - One file only. Prefer one hunk; use more only if the fix genuinely requires it.
    - Preserve the original indentation and line endings.

    If, and only if, the evidence is insufficient to identify the root cause, output this single line instead of a diff:
    NEED_MORE_CONTEXT: <one sentence naming the specific file, function, or data you need>
    </output_format>
    '''

    return prompt