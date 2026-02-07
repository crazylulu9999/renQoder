# Windows CLI Execution Rules (윈도우 CLI 실행 규칙)

This document defines rules to prevent common issues such as path misinterpretation, quoting errors, and missing status checks in the Windows environment.

## 1. Paths & File System (경로 및 파일 시스템)
- **Always use Backslashes (`\`)**: Use backslashes for all file paths in commands executed via `cmd.exe`. Forward slashes (`/`) may be misinterpreted as command-line flags.
- **Prefer Relative Paths**: Use the `Cwd` parameter to set the working directory and use relative paths instead of absolute paths (`C:\...`). This prevents issues with spaces or special characters in the absolute path.

## 2. Command Execution Strategy (명령어 실행 전략)
- **Interactive Shell Fallback**: If a direct `run_command` fails due to path or argument errors, immediately switch to using an interactive `cmd` session with `send_command_input`.
- **Avoid Nested Quotes**: Do not use commands with nested quotes (e.g., `cmd /c "node ... "`) unless necessary, as they are prone to escaping errors in Windows.

## 3. Verification (결과 검증)
- **Mandatory Status Check**: If `run_command` returns a `CommandId` (background execution), you MUST call `command_status` to verify the exit code and output (stdout/stderr).
- **Physical Verification**: Do not rely on the command's success return value alone. Always verify the results using `list_dir` or `grep_search` to ensure files were created or modified as expected.

## 4. Encoding & Output (인코딩 및 출력)
- **UTF-8 with BOM**: To prevent broken Korean text in Windows CLI or Excel, always include the UTF-8 BOM (`\ufeff`) when creating CSV or text files that contain Korean characters.
- **Node.js Output Verification**: If script output is not visible or broken, check the stdout explicitly and consider encoding settings.
