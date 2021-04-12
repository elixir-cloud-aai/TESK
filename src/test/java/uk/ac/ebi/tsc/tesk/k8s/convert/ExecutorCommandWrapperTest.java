package uk.ac.ebi.tsc.tesk.k8s.convert;

import org.junit.Test;
import uk.ac.ebi.tsc.tesk.tes.model.TesExecutor;

import java.util.Arrays;
import java.util.List;

import static org.hamcrest.CoreMatchers.is;
import static org.junit.Assert.assertThat;

public class ExecutorCommandWrapperTest {

    @Test
    public void noStreams() {
        TesExecutor executor = new TesExecutor().addCommandItem("ls");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("ls")));
    }

    @Test
    public void noStreamsList() {
        TesExecutor executor = new TesExecutor().addCommandItem("echo").addCommandItem("Hello").addCommandItem("World");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("echo", "Hello", "World")));
    }
    @Test
    public void input() {
        TesExecutor executor = new TesExecutor().addCommandItem("sort").stdin("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "sort < /path/file.txt")));
    }
    @Test
    public void inputList() {
        TesExecutor executor = new TesExecutor().addCommandItem("./executable").addCommandItem("-v").stdin("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "./executable -v < /path/file.txt")));
    }
    @Test
    public void output() {
        TesExecutor executor = new TesExecutor().addCommandItem("ls").stdout("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "ls > /path/file.txt")));
    }
    @Test
    public void outputList() {
        TesExecutor executor = new TesExecutor().addCommandItem("./executable").addCommandItem("-v").stdout("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "./executable -v > /path/file.txt")));
    }
    @Test
    public void error() {
        TesExecutor executor = new TesExecutor().addCommandItem("ls").stderr("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "ls 2> /path/file.txt")));
    }
    @Test
    public void errorList() {
        TesExecutor executor = new TesExecutor().addCommandItem("./executable").addCommandItem("-v").stderr("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "./executable -v 2> /path/file.txt")));
    }
    @Test
    public void outputAndError() {
        TesExecutor executor = new TesExecutor().addCommandItem("./executable").addCommandItem("-v").stdout("/path/file.txt").stderr("/path/error.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "./executable -v > /path/file.txt 2> /path/error.txt")));
    }
    @Test
    public void allStreams() {
        TesExecutor executor = new TesExecutor().addCommandItem("./executable").addCommandItem("-v").stdout("/path/file.txt").stderr("/path/error.txt").stdin("/other/input");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "./executable -v < /other/input > /path/file.txt 2> /path/error.txt")));
    }

    @Test
    public void escapeSpecialChar() {
        TesExecutor executor = new TesExecutor().addCommandItem("echo").addCommandItem("It costs").addCommandItem("$25").stdout("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "echo 'It costs' '$25' > /path/file.txt")));
    }
    @Test
    public void escapeSpecialCharShell() {
        TesExecutor executor = new TesExecutor().addCommandItem("sh").addCommandItem("-c").addCommandItem("echo It costs a $FORTUNE").stdout("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "sh -c 'echo It costs a $FORTUNE' > /path/file.txt")));
    }
    @Test
    public void escapeSingleQuote() {
        TesExecutor executor = new TesExecutor().addCommandItem("echo").addCommandItem("I say 'Do it'").stdout("/path/file.txt");
        List<String> result = new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects();
        assertThat(result, is(Arrays.asList("/bin/sh", "-c", "echo 'I say '\"'\"'Do it'\"'\"'' > /path/file.txt")));
    }
}