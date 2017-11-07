package uk.ac.ebi.tsc.tesk.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.util.ArrayList;
import java.util.List;
import uk.ac.ebi.tsc.tesk.model.TesPorts;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * ExecutorLog describes logging information related to an Executor.
 */
@ApiModel(description = "ExecutorLog describes logging information related to an Executor.")
@javax.annotation.Generated(value = "io.swagger.codegen.languages.SpringCodegen", date = "2017-11-07T14:45:12.993Z")

public class TesExecutorLog   {
  @JsonProperty("start_time")
  private String startTime = null;

  @JsonProperty("end_time")
  private String endTime = null;

  @JsonProperty("stdout")
  private String stdout = null;

  @JsonProperty("stderr")
  private String stderr = null;

  @JsonProperty("exit_code")
  private Integer exitCode = null;

  @JsonProperty("host_ip")
  private String hostIp = null;

  @JsonProperty("ports")
  private List<TesPorts> ports = null;

  public TesExecutorLog startTime(String startTime) {
    this.startTime = startTime;
    return this;
  }

   /**
   * Time the executor started, in RFC 3339 format.
   * @return startTime
  **/
  @ApiModelProperty(value = "Time the executor started, in RFC 3339 format.")


  public String getStartTime() {
    return startTime;
  }

  public void setStartTime(String startTime) {
    this.startTime = startTime;
  }

  public TesExecutorLog endTime(String endTime) {
    this.endTime = endTime;
    return this;
  }

   /**
   * Time the executor ended, in RFC 3339 format.
   * @return endTime
  **/
  @ApiModelProperty(value = "Time the executor ended, in RFC 3339 format.")


  public String getEndTime() {
    return endTime;
  }

  public void setEndTime(String endTime) {
    this.endTime = endTime;
  }

  public TesExecutorLog stdout(String stdout) {
    this.stdout = stdout;
    return this;
  }

   /**
   * Stdout tail. This is not guaranteed to be the entire log. Implementations determine the maximum size.
   * @return stdout
  **/
  @ApiModelProperty(value = "Stdout tail. This is not guaranteed to be the entire log. Implementations determine the maximum size.")


  public String getStdout() {
    return stdout;
  }

  public void setStdout(String stdout) {
    this.stdout = stdout;
  }

  public TesExecutorLog stderr(String stderr) {
    this.stderr = stderr;
    return this;
  }

   /**
   * Stderr tail. This is not guaranteed to be the entire log. Implementations determine the maximum size.
   * @return stderr
  **/
  @ApiModelProperty(value = "Stderr tail. This is not guaranteed to be the entire log. Implementations determine the maximum size.")


  public String getStderr() {
    return stderr;
  }

  public void setStderr(String stderr) {
    this.stderr = stderr;
  }

  public TesExecutorLog exitCode(Integer exitCode) {
    this.exitCode = exitCode;
    return this;
  }

   /**
   * Exit code.
   * @return exitCode
  **/
  @ApiModelProperty(value = "Exit code.")


  public Integer getExitCode() {
    return exitCode;
  }

  public void setExitCode(Integer exitCode) {
    this.exitCode = exitCode;
  }

  public TesExecutorLog hostIp(String hostIp) {
    this.hostIp = hostIp;
    return this;
  }

   /**
   * IP address of the host.
   * @return hostIp
  **/
  @ApiModelProperty(value = "IP address of the host.")


  public String getHostIp() {
    return hostIp;
  }

  public void setHostIp(String hostIp) {
    this.hostIp = hostIp;
  }

  public TesExecutorLog ports(List<TesPorts> ports) {
    this.ports = ports;
    return this;
  }

  public TesExecutorLog addPortsItem(TesPorts portsItem) {
    if (this.ports == null) {
      this.ports = new ArrayList<TesPorts>();
    }
    this.ports.add(portsItem);
    return this;
  }

   /**
   * Ports bound between the Executor's container and host.  TES clients can use these logs to discover port bindings and communicate with running tasks/executors.
   * @return ports
  **/
  @ApiModelProperty(value = "Ports bound between the Executor's container and host.  TES clients can use these logs to discover port bindings and communicate with running tasks/executors.")

  @Valid

  public List<TesPorts> getPorts() {
    return ports;
  }

  public void setPorts(List<TesPorts> ports) {
    this.ports = ports;
  }


  @Override
  public boolean equals(java.lang.Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesExecutorLog tesExecutorLog = (TesExecutorLog) o;
    return Objects.equals(this.startTime, tesExecutorLog.startTime) &&
        Objects.equals(this.endTime, tesExecutorLog.endTime) &&
        Objects.equals(this.stdout, tesExecutorLog.stdout) &&
        Objects.equals(this.stderr, tesExecutorLog.stderr) &&
        Objects.equals(this.exitCode, tesExecutorLog.exitCode) &&
        Objects.equals(this.hostIp, tesExecutorLog.hostIp) &&
        Objects.equals(this.ports, tesExecutorLog.ports);
  }

  @Override
  public int hashCode() {
    return Objects.hash(startTime, endTime, stdout, stderr, exitCode, hostIp, ports);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesExecutorLog {\n");
    
    sb.append("    startTime: ").append(toIndentedString(startTime)).append("\n");
    sb.append("    endTime: ").append(toIndentedString(endTime)).append("\n");
    sb.append("    stdout: ").append(toIndentedString(stdout)).append("\n");
    sb.append("    stderr: ").append(toIndentedString(stderr)).append("\n");
    sb.append("    exitCode: ").append(toIndentedString(exitCode)).append("\n");
    sb.append("    hostIp: ").append(toIndentedString(hostIp)).append("\n");
    sb.append("    ports: ").append(toIndentedString(ports)).append("\n");
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

