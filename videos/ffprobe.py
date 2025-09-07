import subprocess

def get_duration_seconds(path: str) -> int:
    """
    Return whole-second duration using ffprobe; 0 if failure.
    """
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "error",
             "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", path],
            stderr=subprocess.STDOUT,
        )
        return int(round(float(out.decode().strip())))
    except Exception:
        return 0