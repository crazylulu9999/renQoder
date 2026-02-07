import subprocess
import sys
import os

def run_command(cmd):
    try:
        # 'cmd /c' prefix is used for stability as per Windows CLI rules
        full_cmd = f'cmd /c "{cmd}"'
        result = subprocess.run(full_cmd, capture_output=True, text=True, encoding='utf-8', shell=True)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)

def main():
    # Force UTF-8 for output to handle Korean characters correctly
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("# Git Context Report\n")

    # 1. Branch information
    branch, _ = run_command("git branch --show-current")
    print(f"## Current Branch: `{branch}`\n")

    # 2. Status
    status, _ = run_command("git status")
    print("## Git Status")
    print("```")
    print(status)
    print("```\n")

    # 3. Diff Stat
    stat, _ = run_command("git diff --cached --stat")
    if stat:
        print("## Staged Changes Summary (Stat)")
        print("```")
        print(stat)
        print("```\n")

    # 4. Full Diff
    diff, _ = run_command("git diff --cached")
    if diff:
        print("## Full Staged Diff")
        # To avoid overwhelming the terminal if the diff is massive,
        # we might want to truncate, but for now we'll provide the full diff.
        print("```diff")
        print(diff)
        print("```\n")
    else:
        print("## Full Staged Diff")
        print("*No staged changes or empty diff.*\n")

    # 5. Recent Commits (for context)
    log, _ = run_command("git log -n 5 --oneline")
    print("## Recent Commits")
    print("```")
    print(log)
    print("```\n")

if __name__ == "__main__":
    main()
