package uk.ac.ebi.tsc.tesk.util;

import org.apache.commons.lang.StringUtils;
import uk.ac.ebi.tsc.tesk.model.TesExecutor;

import java.util.ArrayList;
import java.util.List;
import java.util.StringJoiner;

/**
 * Wraps list of executor's command, so that:
 * - if any of executor's stdin/stdout/stderr params is set, the command runs in shell
 * - stdin, stdout, stderr streams are redirected to paths according to executors params
 * - no shell argument escaping at the moment
 */
public class ExecutorCommandWrapper {
    private final TesExecutor executor;

    public ExecutorCommandWrapper(TesExecutor executor) {
        this.executor = executor;
    }

    public List<String> getCommandsWithStreamRedirects() {
        List<String> result = new ArrayList<>();
        if (StringUtils.isEmpty(executor.getStdin()) && StringUtils.isEmpty(executor.getStdout()) && StringUtils.isEmpty(executor.getStderr())) {
            return executor.getCommand();
        }
        result.add("/bin/sh");
        result.add("-c");
        StringJoiner sj = new StringJoiner(" ");
        executor.getCommand().stream().forEach(sj::add);
        if (!StringUtils.isEmpty(executor.getStdin())) {
            sj.add("<");
            sj.add(executor.getStdin());
        }
        if (!StringUtils.isEmpty(executor.getStdout())) {
            sj.add(">");
            sj.add(executor.getStdout());
        }
        if (!StringUtils.isEmpty(executor.getStderr())) {
            sj.add("2>");
            sj.add(executor.getStderr());
        }
        result.add(sj.toString());
        return result;
    }
}
