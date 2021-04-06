package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;

import javax.validation.constraints.*;

/**
 * ExecutorLog describes logging information related to an Executor.
 */
@ApiModel(description = "ExecutorLog describes logging information related to an Executor.")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesExecutorLog   {
  @JsonProperty("start_time")
  private String startTime;

  @JsonProperty("end_time")
  private String endTime;

  @JsonProperty("stdout")
  private String stdout;

  @JsonProperty("stderr")
  private String stderr;

  @JsonProperty("exit_code")
  private Integer exitCode;

  public TesExecutorLog startTime(String startTime) {
    this.startTime = startTime;
    return this;
  }

  /**
   * Time the executor started, in RFC 3339 format.
   * @return startTime
  */
  @ApiModelProperty(example = "2020-10-02T10:00:00-05:00", value = "Time the executor started, in RFC 3339 format.")


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
  */
  @ApiModelProperty(example = "2020-10-02T11:00:00-05:00", value = "Time the executor ended, in RFC 3339 format.")


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
   * Stdout content.  This is meant for convenience. No guarantees are made about the content. Implementations may chose different approaches: only the head, only the tail, a URL reference only, etc.  In order to capture the full stdout client should set Executor.stdout to a container file path, and use Task.outputs to upload that file to permanent storage.
   * @return stdout
  */
  @ApiModelProperty(value = "Stdout content.  This is meant for convenience. No guarantees are made about the content. Implementations may chose different approaches: only the head, only the tail, a URL reference only, etc.  In order to capture the full stdout client should set Executor.stdout to a container file path, and use Task.outputs to upload that file to permanent storage.")


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
   * Stderr content.  This is meant for convenience. No guarantees are made about the content. Implementations may chose different approaches: only the head, only the tail, a URL reference only, etc.  In order to capture the full stderr client should set Executor.stderr to a container file path, and use Task.outputs to upload that file to permanent storage.
   * @return stderr
  */
  @ApiModelProperty(value = "Stderr content.  This is meant for convenience. No guarantees are made about the content. Implementations may chose different approaches: only the head, only the tail, a URL reference only, etc.  In order to capture the full stderr client should set Executor.stderr to a container file path, and use Task.outputs to upload that file to permanent storage.")


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
  */
  @ApiModelProperty(required = true, value = "Exit code.")
  @NotNull


  public Integer getExitCode() {
    return exitCode;
  }

  public void setExitCode(Integer exitCode) {
    this.exitCode = exitCode;
  }


  @Override
  public boolean equals(Object o) {
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
        Objects.equals(this.exitCode, tesExecutorLog.exitCode);
  }

  @Override
  public int hashCode() {
    return Objects.hash(startTime, endTime, stdout, stderr, exitCode);
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

