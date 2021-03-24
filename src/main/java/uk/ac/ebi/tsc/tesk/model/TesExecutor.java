package uk.ac.ebi.tsc.tesk.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * Executor describes a command to be executed, and its environment.
 */
@ApiModel(description = "Executor describes a command to be executed, and its environment.")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesExecutor   {
  @JsonProperty("image")
  private String image;

  @JsonProperty("command")
  @Valid
  private List<String> command = new ArrayList<>();

  @JsonProperty("workdir")
  private String workdir;

  @JsonProperty("stdin")
  private String stdin;

  @JsonProperty("stdout")
  private String stdout;

  @JsonProperty("stderr")
  private String stderr;

  @JsonProperty("env")
  @Valid
  private Map<String, String> env = null;

  public TesExecutor image(String image) {
    this.image = image;
    return this;
  }

  /**
   * Name of the container image. The string will be passed as the image argument to the containerization run command. Examples:    - `ubuntu`    - `quay.io/aptible/ubuntu`    - `gcr.io/my-org/my-image`    - `myregistryhost:5000/fedora/httpd:version1.0`
   * @return image
  */
  @ApiModelProperty(example = "ubuntu:20.04", required = true, value = "Name of the container image. The string will be passed as the image argument to the containerization run command. Examples:    - `ubuntu`    - `quay.io/aptible/ubuntu`    - `gcr.io/my-org/my-image`    - `myregistryhost:5000/fedora/httpd:version1.0`")
  @NotNull


  public String getImage() {
    return image;
  }

  public void setImage(String image) {
    this.image = image;
  }

  public TesExecutor command(List<String> command) {
    this.command = command;
    return this;
  }

  public TesExecutor addCommandItem(String commandItem) {
    if (this.command == null) {
      this.command = new ArrayList<>();
    }
    this.command.add(commandItem);
    return this;
  }

  /**
   * A sequence of program arguments to execute, where the first argument is the program to execute (i.e. argv). Example: ``` {   \"command\" : [\"/bin/md5\", \"/data/file1\"] } ```
   * @return command
  */
  @ApiModelProperty(example = "[\"/bin/md5\",\"/data/file1\"]", required = true, value = "A sequence of program arguments to execute, where the first argument is the program to execute (i.e. argv). Example: ``` {   \"command\" : [\"/bin/md5\", \"/data/file1\"] } ```")
  @NotNull


  public List<String> getCommand() {
    return command;
  }

  public void setCommand(List<String> command) {
    this.command = command;
  }

  public TesExecutor workdir(String workdir) {
    this.workdir = workdir;
    return this;
  }

  /**
   * The working directory that the command will be executed in. If not defined, the system will default to the directory set by the container image.
   * @return workdir
  */
  @ApiModelProperty(example = "/data/", value = "The working directory that the command will be executed in. If not defined, the system will default to the directory set by the container image.")


  public String getWorkdir() {
    return workdir;
  }

  public void setWorkdir(String workdir) {
    this.workdir = workdir;
  }

  public TesExecutor stdin(String stdin) {
    this.stdin = stdin;
    return this;
  }

  /**
   * Path inside the container to a file which will be piped to the executor's stdin. This must be an absolute path. This mechanism could be used in conjunction with the input declaration to process a data file using a tool that expects STDIN.  For example, to get the MD5 sum of a file by reading it into the STDIN ``` {   \"command\" : [\"/bin/md5\"],   \"stdin\" : \"/data/file1\" } ```
   * @return stdin
  */
  @ApiModelProperty(example = "/data/file1", value = "Path inside the container to a file which will be piped to the executor's stdin. This must be an absolute path. This mechanism could be used in conjunction with the input declaration to process a data file using a tool that expects STDIN.  For example, to get the MD5 sum of a file by reading it into the STDIN ``` {   \"command\" : [\"/bin/md5\"],   \"stdin\" : \"/data/file1\" } ```")


  public String getStdin() {
    return stdin;
  }

  public void setStdin(String stdin) {
    this.stdin = stdin;
  }

  public TesExecutor stdout(String stdout) {
    this.stdout = stdout;
    return this;
  }

  /**
   * Path inside the container to a file where the executor's stdout will be written to. Must be an absolute path. Example: ``` {   \"stdout\" : \"/tmp/stdout.log\" } ```
   * @return stdout
  */
  @ApiModelProperty(example = "/tmp/stdout.log", value = "Path inside the container to a file where the executor's stdout will be written to. Must be an absolute path. Example: ``` {   \"stdout\" : \"/tmp/stdout.log\" } ```")


  public String getStdout() {
    return stdout;
  }

  public void setStdout(String stdout) {
    this.stdout = stdout;
  }

  public TesExecutor stderr(String stderr) {
    this.stderr = stderr;
    return this;
  }

  /**
   * Path inside the container to a file where the executor's stderr will be written to. Must be an absolute path. Example: ``` {   \"stderr\" : \"/tmp/stderr.log\" } ```
   * @return stderr
  */
  @ApiModelProperty(example = "/tmp/stderr.log", value = "Path inside the container to a file where the executor's stderr will be written to. Must be an absolute path. Example: ``` {   \"stderr\" : \"/tmp/stderr.log\" } ```")


  public String getStderr() {
    return stderr;
  }

  public void setStderr(String stderr) {
    this.stderr = stderr;
  }

  public TesExecutor env(Map<String, String> env) {
    this.env = env;
    return this;
  }

  public TesExecutor putEnvItem(String key, String envItem) {
    if (this.env == null) {
      this.env = new HashMap<>();
    }
    this.env.put(key, envItem);
    return this;
  }

  /**
   * Enviromental variables to set within the container. Example: ``` {   \"env\" : {     \"ENV_CONFIG_PATH\" : \"/data/config.file\",     \"BLASTDB\" : \"/data/GRC38\",     \"HMMERDB\" : \"/data/hmmer\"   } } ```
   * @return env
  */
  @ApiModelProperty(example = "{\"BLASTDB\":\"/data/GRC38\",\"HMMERDB\":\"/data/hmmer\"}", value = "Enviromental variables to set within the container. Example: ``` {   \"env\" : {     \"ENV_CONFIG_PATH\" : \"/data/config.file\",     \"BLASTDB\" : \"/data/GRC38\",     \"HMMERDB\" : \"/data/hmmer\"   } } ```")


  public Map<String, String> getEnv() {
    return env;
  }

  public void setEnv(Map<String, String> env) {
    this.env = env;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesExecutor tesExecutor = (TesExecutor) o;
    return Objects.equals(this.image, tesExecutor.image) &&
        Objects.equals(this.command, tesExecutor.command) &&
        Objects.equals(this.workdir, tesExecutor.workdir) &&
        Objects.equals(this.stdin, tesExecutor.stdin) &&
        Objects.equals(this.stdout, tesExecutor.stdout) &&
        Objects.equals(this.stderr, tesExecutor.stderr) &&
        Objects.equals(this.env, tesExecutor.env);
  }

  @Override
  public int hashCode() {
    return Objects.hash(image, command, workdir, stdin, stdout, stderr, env);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesExecutor {\n");
    
    sb.append("    image: ").append(toIndentedString(image)).append("\n");
    sb.append("    command: ").append(toIndentedString(command)).append("\n");
    sb.append("    workdir: ").append(toIndentedString(workdir)).append("\n");
    sb.append("    stdin: ").append(toIndentedString(stdin)).append("\n");
    sb.append("    stdout: ").append(toIndentedString(stdout)).append("\n");
    sb.append("    stderr: ").append(toIndentedString(stderr)).append("\n");
    sb.append("    env: ").append(toIndentedString(env)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(Object o) {
    if (o == null) {
      return "null";
    }
    return o.toString().replace("\n", "\n    ");
  }
}

