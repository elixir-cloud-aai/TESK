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
import uk.ac.ebi.tsc.tesk.model.TesPorts;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * Executor describes a command to be executed, and its environment.
 */
@ApiModel(description = "Executor describes a command to be executed, and its environment.")
@javax.annotation.Generated(value = "io.swagger.codegen.languages.SpringCodegen", date = "2017-11-07T14:45:12.993Z")

public class TesExecutor   {
  @JsonProperty("image_name")
  private String imageName = null;

  @JsonProperty("cmd")
  private List<String> cmd = null;

  @JsonProperty("workdir")
  private String workdir = null;

  @JsonProperty("stdin")
  private String stdin = null;

  @JsonProperty("stdout")
  private String stdout = null;

  @JsonProperty("stderr")
  private String stderr = null;

  @JsonProperty("ports")
  private List<TesPorts> ports = null;

  @JsonProperty("environ")
  private Map<String, String> environ = null;

  public TesExecutor imageName(String imageName) {
    this.imageName = imageName;
    return this;
  }

   /**
   * Name of the container image, for example: ubuntu quay.io/aptible/ubuntu gcr.io/my-org/my-image etc...
   * @return imageName
  **/
  @ApiModelProperty(value = "Name of the container image, for example: ubuntu quay.io/aptible/ubuntu gcr.io/my-org/my-image etc...")


  public String getImageName() {
    return imageName;
  }

  public void setImageName(String imageName) {
    this.imageName = imageName;
  }

  public TesExecutor cmd(List<String> cmd) {
    this.cmd = cmd;
    return this;
  }

  public TesExecutor addCmdItem(String cmdItem) {
    if (this.cmd == null) {
      this.cmd = new ArrayList<String>();
    }
    this.cmd.add(cmdItem);
    return this;
  }

   /**
   * A sequence of program arguments to execute, where the first argument is the program to execute (i.e. argv).
   * @return cmd
  **/
  @ApiModelProperty(value = "A sequence of program arguments to execute, where the first argument is the program to execute (i.e. argv).")


  public List<String> getCmd() {
    return cmd;
  }

  public void setCmd(List<String> cmd) {
    this.cmd = cmd;
  }

  public TesExecutor workdir(String workdir) {
    this.workdir = workdir;
    return this;
  }

   /**
   * The working directory that the command will be executed in. Defaults to the directory set by the container image.
   * @return workdir
  **/
  @ApiModelProperty(value = "The working directory that the command will be executed in. Defaults to the directory set by the container image.")


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
   * Path inside the container to a file which will be piped to the executor's stdin. Must be an absolute path.
   * @return stdin
  **/
  @ApiModelProperty(value = "Path inside the container to a file which will be piped to the executor's stdin. Must be an absolute path.")


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
   * Path inside the container to a file where the executor's stdout will be written to. Must be an absolute path.
   * @return stdout
  **/
  @ApiModelProperty(value = "Path inside the container to a file where the executor's stdout will be written to. Must be an absolute path.")


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
   * Path inside the container to a file where the executor's stderr will be written to. Must be an absolute path.
   * @return stderr
  **/
  @ApiModelProperty(value = "Path inside the container to a file where the executor's stderr will be written to. Must be an absolute path.")


  public String getStderr() {
    return stderr;
  }

  public void setStderr(String stderr) {
    this.stderr = stderr;
  }

  public TesExecutor ports(List<TesPorts> ports) {
    this.ports = ports;
    return this;
  }

  public TesExecutor addPortsItem(TesPorts portsItem) {
    if (this.ports == null) {
      this.ports = new ArrayList<TesPorts>();
    }
    this.ports.add(portsItem);
    return this;
  }

   /**
   * A list of port bindings between the container and host. For example, a Docker implementation might map this to `docker run -p host:container`.  Port bindings are included in ExecutorLogs, which allows TES clients to discover port bindings and communicate with running tasks/executors.
   * @return ports
  **/
  @ApiModelProperty(value = "A list of port bindings between the container and host. For example, a Docker implementation might map this to `docker run -p host:container`.  Port bindings are included in ExecutorLogs, which allows TES clients to discover port bindings and communicate with running tasks/executors.")

  @Valid

  public List<TesPorts> getPorts() {
    return ports;
  }

  public void setPorts(List<TesPorts> ports) {
    this.ports = ports;
  }

  public TesExecutor environ(Map<String, String> environ) {
    this.environ = environ;
    return this;
  }

  public TesExecutor putEnvironItem(String key, String environItem) {
    if (this.environ == null) {
      this.environ = new HashMap<String, String>();
    }
    this.environ.put(key, environItem);
    return this;
  }

   /**
   * Enviromental variables to set within the container.
   * @return environ
  **/
  @ApiModelProperty(value = "Enviromental variables to set within the container.")


  public Map<String, String> getEnviron() {
    return environ;
  }

  public void setEnviron(Map<String, String> environ) {
    this.environ = environ;
  }


  @Override
  public boolean equals(java.lang.Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesExecutor tesExecutor = (TesExecutor) o;
    return Objects.equals(this.imageName, tesExecutor.imageName) &&
        Objects.equals(this.cmd, tesExecutor.cmd) &&
        Objects.equals(this.workdir, tesExecutor.workdir) &&
        Objects.equals(this.stdin, tesExecutor.stdin) &&
        Objects.equals(this.stdout, tesExecutor.stdout) &&
        Objects.equals(this.stderr, tesExecutor.stderr) &&
        Objects.equals(this.ports, tesExecutor.ports) &&
        Objects.equals(this.environ, tesExecutor.environ);
  }

  @Override
  public int hashCode() {
    return Objects.hash(imageName, cmd, workdir, stdin, stdout, stderr, ports, environ);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesExecutor {\n");
    
    sb.append("    imageName: ").append(toIndentedString(imageName)).append("\n");
    sb.append("    cmd: ").append(toIndentedString(cmd)).append("\n");
    sb.append("    workdir: ").append(toIndentedString(workdir)).append("\n");
    sb.append("    stdin: ").append(toIndentedString(stdin)).append("\n");
    sb.append("    stdout: ").append(toIndentedString(stdout)).append("\n");
    sb.append("    stderr: ").append(toIndentedString(stderr)).append("\n");
    sb.append("    ports: ").append(toIndentedString(ports)).append("\n");
    sb.append("    environ: ").append(toIndentedString(environ)).append("\n");
    sb.append("}");
    return sb.toString();
  }

  /**
   * Convert the given object to string with each line indented by 4 spaces
   * (except the first line).
   */
  private String toIndentedString(java.lang.Object o) {
    if (o == null) {
      return "null";
    }
    return o.toString().replace("\n", "\n    ");
  }
}

