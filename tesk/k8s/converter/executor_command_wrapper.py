"""Wraps list of executor's command.

Such that:
- If any of executor's stdin/stdout/stderr params is set, the command runs in shell
- Each part of the original command (single command/argument) that contained shell
  special chars is surrounded by single quotes, plus single quote inside such string
  are replaced with '"'"' sequence
- `stdin`, `stdout`, `stderr` streams are redirected to paths according to executors
  params
"""

from typing import List

from tesk.api.ga4gh.tes.models import TesExecutor


class ExecutorCommandWrapper:
    """Wraps executor's command.
    
    Attributes:
        executor: executor to wrap
    """

    def __init__(self, executor: TesExecutor):
        """Initialize the wrapper.
        
        Args:
            executor: executor to wrap
        """
        self.executor = executor

    def get_commands_with_stream_redirects(self) -> List[str]:
        """Get command with stream redirects.
        
        Returns:
            List[str]: command to run by exector with stream redirects
        """
        if (
            not self.executor.stdin
            and not self.executor.stdout
            and not self.executor.stderr
        ):
            return self.executor.command

        result = ["/bin/sh", "-c"]

        command_parts = [" ".join(self.executor.command)]

        if self.executor.stdin:
            command_parts.extend(["<", self.executor.stdin])
        if self.executor.stdout:
            command_parts.extend([">", self.executor.stdout])
        if self.executor.stderr:
            command_parts.extend(["2>", self.executor.stderr])

        result.append(" ".join(command_parts))

        return result
