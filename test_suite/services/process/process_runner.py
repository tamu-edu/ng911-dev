import subprocess
import threading
import sys


def _pipe_reader(pipe, tee_stream):
    """
    Read subprocess pipe line-by-line and tee it into:
      - real terminal (stdout/stderr)
      - console_output.log via TeeStream
    """
    try:
        for line in iter(pipe.readline, b""):
            text = line.decode(errors="replace")
            tee_stream.write(text)
            tee_stream.flush()
    finally:
        pipe.close()


def run_process(cmd, *, name="process", env=None, cwd=None, preexec_fn=None):
    """
    Start subprocess with stdout/stderr captured and tee'd to:
      - real terminal
      - console_output.log (via TeeStream)

    Returns subprocess.Popen instance (unchanged lifecycle).
    """

    # IMPORTANT:
    # sys.stdout / sys.stderr are already TeeStream instances
    # (set in main.py), so writing to them writes BOTH to terminal + file.

    if preexec_fn:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=cwd,
            preexec_fn=preexec_fn,
            bufsize=1,
            close_fds=True,
        )
    else:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=cwd,
            bufsize=1,
            close_fds=True,
        )

    # Drain stdout
    threading.Thread(
        target=_pipe_reader,
        args=(proc.stdout, sys.stdout),
        daemon=True,
        name=f"{name}-stdout",
    ).start()

    # Drain stderr
    threading.Thread(
        target=_pipe_reader,
        args=(proc.stderr, sys.stderr),
        daemon=True,
        name=f"{name}-stderr",
    ).start()

    return proc
