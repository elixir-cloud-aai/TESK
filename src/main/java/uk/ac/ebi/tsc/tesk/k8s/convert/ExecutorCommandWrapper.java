package uk.ac.ebi.tsc.tesk.k8s.convert;

import org.apache.commons.lang.StringUtils;
import uk.ac.ebi.tsc.tesk.tes.model.TesExecutor;

import java.util.ArrayList;
import java.util.List;
import java.util.StringJoiner;
import java.util.regex.Pattern;

/**
 * Wraps list of executor's command, so that:
 * - if any of executor's stdin/stdout/stderr params is set, the command runs in shell
 * - Each part of the original command (single command/argument) that contained shell special chars is surrounded by single quotes,
 *   plus single quote inside such string are replaced with '"'"' sequence
 * - stdin, stdout, stderr streams are redirected to paths according to executors params
 */
public class ExecutorCommandWrapper {

    private static final Pattern SPECIAL_CHARS = Pattern.compile("[ !\"#$&'()*;<>?\\[\\\\`{|~\\t\\n]");
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
        for (String commandPart : executor.getCommand()) {
            if (SPECIAL_CHARS.matcher(commandPart).find()) {
                if (commandPart.contains("'")) {
                    commandPart = commandPart.replaceAll("'", "'\"'\"'");
                }
                commandPart = "'" + commandPart + "'";
            }
            sj.add(commandPart);
        }
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
