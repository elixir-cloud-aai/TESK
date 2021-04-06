package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * TaskLog describes logging information related to a Task.
 */
@ApiModel(description = "TaskLog describes logging information related to a Task.")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesTaskLog   {
  @JsonProperty("logs")
  @Valid
  private List<TesExecutorLog> logs = new ArrayList<>();

  @JsonProperty("metadata")
  @Valid
  private Map<String, String> metadata = null;

  @JsonProperty("start_time")
  private String startTime;

  @JsonProperty("end_time")
  private String endTime;

  @JsonProperty("outputs")
  @Valid
  //non-standard. Outputs currently not supported in TESK.
  private List<TesOutputFileLog> outputs = null;

  @JsonProperty("system_logs")
  @Valid
  private List<String> systemLogs = null;

  public TesTaskLog logs(List<TesExecutorLog> logs) {
    this.logs = logs;
    return this;
  }

  public TesTaskLog addLogsItem(TesExecutorLog logsItem) {
    if (this.logs == null) {
      this.logs = new ArrayList<>();
    }
    this.logs.add(logsItem);
    return this;
  }

  /**
   * Logs for each executor
   * @return logs
  */
  @ApiModelProperty(required = true, value = "Logs for each executor")
  @NotNull

  @Valid

  public List<TesExecutorLog> getLogs() {
    return logs;
  }

  public void setLogs(List<TesExecutorLog> logs) {
    this.logs = logs;
  }

  public TesTaskLog metadata(Map<String, String> metadata) {
    this.metadata = metadata;
    return this;
  }

  public TesTaskLog putMetadataItem(String key, String metadataItem) {
    if (this.metadata == null) {
      this.metadata = new HashMap<>();
    }
    this.metadata.put(key, metadataItem);
    return this;
  }

  /**
   * Arbitrary logging metadata included by the implementation.
   * @return metadata
  */
  @ApiModelProperty(example = "{\"host\":\"worker-001\",\"slurmm_id\":123456}", value = "Arbitrary logging metadata included by the implementation.")


  public Map<String, String> getMetadata() {
    return metadata;
  }

  public void setMetadata(Map<String, String> metadata) {
    this.metadata = metadata;
  }

  public TesTaskLog startTime(String startTime) {
    this.startTime = startTime;
    return this;
  }

  /**
   * When the task started, in RFC 3339 format.
   * @return startTime
  */
  @ApiModelProperty(example = "2020-10-02T10:00:00-05:00", value = "When the task started, in RFC 3339 format.")


  public String getStartTime() {
    return startTime;
  }

  public void setStartTime(String startTime) {
    this.startTime = startTime;
  }

  public TesTaskLog endTime(String endTime) {
    this.endTime = endTime;
    return this;
  }

  /**
   * When the task ended, in RFC 3339 format.
   * @return endTime
  */
  @ApiModelProperty(example = "2020-10-02T11:00:00-05:00", value = "When the task ended, in RFC 3339 format.")


  public String getEndTime() {
    return endTime;
  }

  public void setEndTime(String endTime) {
    this.endTime = endTime;
  }

  public TesTaskLog outputs(List<TesOutputFileLog> outputs) {
    this.outputs = outputs;
    return this;
  }

  public TesTaskLog addOutputsItem(TesOutputFileLog outputsItem) {
    if (this.outputs == null) {
      this.outputs = new ArrayList<>();
    }
    this.outputs.add(outputsItem);
    return this;
  }

  /**
   * Information about all output files. Directory outputs are flattened into separate items.
   * @return outputs
  */
  @ApiModelProperty(required = true, value = "Information about all output files. Directory outputs are flattened into separate items.")
  @NotNull

  @Valid

  public List<TesOutputFileLog> getOutputs() {
    return outputs;
  }

  public void setOutputs(List<TesOutputFileLog> outputs) {
    this.outputs = outputs;
  }

  public TesTaskLog systemLogs(List<String> systemLogs) {
    this.systemLogs = systemLogs;
    return this;
  }

  public TesTaskLog addSystemLogsItem(String systemLogsItem) {
    if (this.systemLogs == null) {
      this.systemLogs = new ArrayList<>();
    }
    this.systemLogs.add(systemLogsItem);
    return this;
  }

  /**
   * System logs are any logs the system decides are relevant, which are not tied directly to an Executor process. Content is implementation specific: format, size, etc.  System logs may be collected here to provide convenient access.  For example, the system may include the name of the host where the task is executing, an error message that caused a SYSTEM_ERROR state (e.g. disk is full), etc.  System logs are only included in the FULL task view.
   * @return systemLogs
  */
  @ApiModelProperty(value = "System logs are any logs the system decides are relevant, which are not tied directly to an Executor process. Content is implementation specific: format, size, etc.  System logs may be collected here to provide convenient access.  For example, the system may include the name of the host where the task is executing, an error message that caused a SYSTEM_ERROR state (e.g. disk is full), etc.  System logs are only included in the FULL task view.")


  public List<String> getSystemLogs() {
    return systemLogs;
  }

  public void setSystemLogs(List<String> systemLogs) {
    this.systemLogs = systemLogs;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesTaskLog tesTaskLog = (TesTaskLog) o;
    return Objects.equals(this.logs, tesTaskLog.logs) &&
        Objects.equals(this.metadata, tesTaskLog.metadata) &&
        Objects.equals(this.startTime, tesTaskLog.startTime) &&
        Objects.equals(this.endTime, tesTaskLog.endTime) &&
        Objects.equals(this.outputs, tesTaskLog.outputs) &&
        Objects.equals(this.systemLogs, tesTaskLog.systemLogs);
  }

  @Override
  public int hashCode() {
    return Objects.hash(logs, metadata, startTime, endTime, outputs, systemLogs);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesTaskLog {\n");
    
    sb.append("    logs: ").append(toIndentedString(logs)).append("\n");
    sb.append("    metadata: ").append(toIndentedString(metadata)).append("\n");
    sb.append("    startTime: ").append(toIndentedString(startTime)).append("\n");
    sb.append("    endTime: ").append(toIndentedString(endTime)).append("\n");
    sb.append("    outputs: ").append(toIndentedString(outputs)).append("\n");
    sb.append("    systemLogs: ").append(toIndentedString(systemLogs)).append("\n");
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

