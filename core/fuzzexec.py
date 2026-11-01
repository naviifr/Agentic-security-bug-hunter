from core.config import CLANG
from dataclasses import dataclass
from pathlib import Path
import subprocess
import os
import uuid
from datetime import datetime

CRASH_MARKERS = (
    "ERROR: AddressSanitizer",
    "SUMMARY: AddressSanitizer",
    "ERROR: LeakSanitizer",
    "ERROR: UndefinedBehaviorSanitizer",
    "runtime error:",                      # UBSan
    "ERROR: libFuzzer: deadly signal",
    "ERROR: libFuzzer: timeout",
    "ERROR: libFuzzer: out-of-memory",
)

INFRA_MARKERS = (
    "GetFileAttributesA() failed",
    "ERROR: no interesting inputs were found",     #low code coverage
    "ERROR: The required directory",
    "unrecognized flag",
)


@dataclass
class BuildResult:
    ok: bool
    returncode: int | None
    command: list
    stderr: str
    stdout: str
    binary: Path | None
    failure: str | None


@dataclass
class FuzzRun:
    returncode: int | None
    crashed: bool        # sanitizer report or new crash file = fact
    failure: str | None
    artifact_dir: Path | None
    artifact: tuple
    timed_out: bool
    stdout: str
    stderr: str

    @property
    def clean(self) -> bool:
        return not self.crashed and self.failure is None and not self.timed_out


def _text(value) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", "replace") if isinstance(value, bytes) else value

def _sanitizer_list(value) -> list[str]:
    if isinstance(value, str):
        value = value.split(",")
    parts = [p.strip() for p in value if p.strip()]
    if not parts:
        raise ValueError("at least one sanitizer is required")
    return parts

def build_fuzzer(target, harness, output, *, sanitizers=("address",), driver=True, flags=(), timeout_s=120):

    sanitizers = [*_sanitizer_list(sanitizers), *(["fuzzer"] if driver else [])]

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)  
    
    cmd = [
        CLANG,
        "-g", 
        f"-fsanitize={','.join(sanitizers)}",
        *flags,
        str(target),
        str(harness),
        "-o",
        str(output),
        
    ]
    try:
        
        if output.exists():
            output.unlink(missing_ok=True) 
        query = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8", 
                errors="replace", 
                timeout= timeout_s,
            )

    except OSError as e:
        return BuildResult(ok=False, returncode=None, command=cmd, stderr=str(e),
                           stdout="", binary=None,
                           failure=f"could not run compiler {CLANG}: {e}")
    except subprocess.TimeoutExpired as e:
        return BuildResult(ok=False, returncode=None, binary=None, command=cmd,
                        stdout=_text(e.stdout), stderr=_text(e.stderr), failure="build timed out")

    ok = query.returncode == 0 and output.is_file()
    return BuildResult(
    ok=ok,
    returncode= query.returncode,
    binary=output if ok else None,
    command=cmd,
    stdout=query.stdout,
    stderr=query.stderr,
    failure= "compiler returned 0 but produced no file" if query.returncode == 0 and  not output.is_file() else None,
    )


def run_fuzzer(fuzzer, corpus, artifact_dir, *, fuzz_time=10, seed=0,
               rss_limit_mb=2048, timeout_s=None, run_name= None):

    fuzzer = Path(fuzzer)
    corpus = Path(corpus)
    base = Path(artifact_dir)

    run_name = run_name or f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"
    run_artifacts = base / run_name

    if not fuzzer.is_file():
        return FuzzRun(returncode=None, crashed=False,timed_out=False, stdout="", stderr="",
                       artifact=(), artifact_dir=None, failure=f"fuzzer binary not found: {fuzzer}")

    cmd = [
        str(fuzzer),
        str(corpus),
        f"-max_total_time={fuzz_time}",
        f"-artifact_prefix={run_artifacts.resolve()}{os.sep}",
        f"-rss_limit_mb={rss_limit_mb}",                     #max allowed memory
        f"-seed={seed}",
        "-error_exitcode=77",                                #defined return codes
        "-timeout_exitcode=77"
    ]

    timeout_s = fuzz_time + 60 if timeout_s is None else timeout_s

    try:
        corpus.mkdir(parents=True, exist_ok=True)
        run_artifacts.mkdir(parents = True, exist_ok=False)

    except OSError as e:
        return FuzzRun(returncode=None, crashed=False, timed_out=False, stdout="", stderr=str(e),
                        artifact=(), artifact_dir=None, failure=f"could not create corpus/artifact dir: {e}")

    try:
        query = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8", 
                    errors="replace", 
                    timeout=timeout_s
                )
        rc, out, err, timed_out = query.returncode, query.stdout, query.stderr, False

    except OSError as e:
        return FuzzRun(returncode=None, crashed=False, timed_out=False, stdout="", stderr=str(e),
                        artifact=(), artifact_dir=None, failure=f"could not run fuzzer {fuzzer}: {e}")
    except subprocess.TimeoutExpired as e:
        rc, out, err, timed_out = None, _text(e.stdout), _text(e.stderr), True

    new = tuple(sorted(f for f in run_artifacts.iterdir() if f.is_file()))

    text = err + out
    crashed = bool(new) or any(m in text for m in CRASH_MARKERS)
    infra = next((n for n in INFRA_MARKERS if n in text), None)

    failure = None
    if timed_out:
        failure = f"fuzzer did not exit within {timeout_s}s"
    elif infra:
        failure = f"fuzzer could not run: {infra}"
    elif not crashed and rc != 0:
        failure = f"unexplained exit code {rc}"

    return FuzzRun(returncode=rc, crashed=crashed, failure=failure,
                   artifact=new, artifact_dir=run_artifacts,timed_out=timed_out, stdout=out, stderr=err)
    
        

    