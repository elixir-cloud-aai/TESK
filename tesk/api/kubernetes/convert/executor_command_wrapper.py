"""Wraps list of executor's command.

Such that:
- If any of executor's stdin/stdout/stderr params is set, the command runs in shell
- Each part of the original command (single command/argument) that contained shell
  special chars is surrounded by single quotes, plus single quote inside such string
  are replaced with '"'"' sequence
- `stdin`, `stdout`, `stderr` streams are redirected to paths according to executors
  params
"""

import re
from typing import List

from tesk.api.ga4gh.tes.models import TesExecutor


class ExecutorCommandWrapper:
    SPECIAL_CHARS = re.compile(r"[ !\"#$&'()*;<>?\[\\`{|~\t\n]")

    def __init__(self, executor: TesExecutor):
        self.executor = executor

    def get_commands_with_stream_redirects(self) -> List[str]:
        result = []

        if (
            not self.executor.stdin
            and not self.executor.stdout
            and not self.executor.stderr
        ):
            return self.executor.command

        result.append("/bin/sh")
        result.append("-c")

        command_parts = []

        for command_part in self.executor.command:
            if self.SPECIAL_CHARS.search(command_part):
                if "'" in command_part:
                    command_part = command_part.replace("'", "'\"'\"'")
                command_part = f"'{command_part}'"
            command_parts.append(command_part)

        if self.executor.stdin:
            command_parts.append("<")
            command_parts.append(self.executor.stdin)

        if self.executor.stdout:
            command_parts.append(">")
            command_parts.append(self.executor.stdout)

        if self.executor.stderr:
            command_parts.append("2>")
            command_parts.append(self.executor.stderr)

        result.append(" ".join(command_parts))

        return result
