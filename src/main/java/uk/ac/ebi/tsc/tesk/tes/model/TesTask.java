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

import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.ABSOLUTE_PATH_MESSAGE;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.ABSOLUTE_PATH_REGEXP;

/**
 * Task describes an instance of a task.
 */
@ApiModel(description = "Task describes an instance of a task.")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesTask   {
  @JsonProperty("id")
  private String id;

  @JsonProperty("state")
  private TesState state = null;

  @JsonProperty("name")
  private String name;

  @JsonProperty("description")
  private String description;

  @JsonProperty("inputs")
  @Valid
  private List<TesInput> inputs = null;

  @JsonProperty("outputs")
  @Valid
  private List<TesOutput> outputs = null;

  @JsonProperty("resources")
  private TesResources resources;

  @JsonProperty("executors")
  @Valid
  //TES API design flaw - executors are required, but only for input (should not appear in minimal outputs)
  private List<TesExecutor> executors = null;

  @JsonProperty("volumes")
  @Valid
  private List<String> volumes = null;

  @JsonProperty("tags")
  @Valid
  private Map<String, String> tags = null;

  @JsonProperty("logs")
  @Valid
  private List<TesTaskLog> logs = null;

  @JsonProperty("creation_time")
  private String creationTime;

  public TesTask id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Task identifier assigned by the server.
   * @return id
  */
  @ApiModelProperty(example = "job-0012345", readOnly = true, value = "Task identifier assigned by the server.")


  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public TesTask state(TesState state) {
    this.state = state;
    return this;
  }

  /**
   * Get state
   * @return state
  */
  @ApiModelProperty(value = "")

  @Valid

  public TesState getState() {
    return state;
  }

  public void setState(TesState state) {
    this.state = state;
  }

  public TesTask name(String name) {
    this.name = name;
    return this;
  }

  /**
   * User-provided task name.
   * @return name
  */
  @ApiModelProperty(value = "User-provided task name.")


  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public TesTask description(String description) {
    this.description = description;
    return this;
  }

  /**
   * Optional user-provided description of task for documentation purposes.
   * @return description
  */
  @ApiModelProperty(value = "Optional user-provided description of task for documentation purposes.")


  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public TesTask inputs(List<TesInput> inputs) {
    this.inputs = inputs;
    return this;
  }

  public TesTask addInputsItem(TesInput inputsItem) {
    if (this.inputs == null) {
      this.inputs = new ArrayList<>();
    }
    this.inputs.add(inputsItem);
    return this;
  }

  /**
   * Input files that will be used by the task. Inputs will be downloaded and mounted into the executor container as defined by the task request document.
   * @return inputs
  */
  @ApiModelProperty(example = "[{\"url\":\"s3://my-object-store/file1\",\"path\":\"/data/file1\"}]", value = "Input files that will be used by the task. Inputs will be downloaded and mounted into the executor container as defined by the task request document.")

  @Valid

  public List<TesInput> getInputs() {
    return inputs;
  }

  public void setInputs(List<TesInput> inputs) {
    this.inputs = inputs;
  }

  public TesTask outputs(List<TesOutput> outputs) {
    this.outputs = outputs;
    return this;
  }

  public TesTask addOutputsItem(TesOutput outputsItem) {
    if (this.outputs == null) {
      this.outputs = new ArrayList<>();
    }
    this.outputs.add(outputsItem);
    return this;
  }

  /**
   * Output files. Outputs will be uploaded from the executor container to long-term storage.
   * @return outputs
  */
  @ApiModelProperty(example = "[{\"path\":\"/data/outfile\",\"url\":\"s3://my-object-store/outfile-1\",\"type\":\"FILE\"}]", value = "Output files. Outputs will be uploaded from the executor container to long-term storage.")

  @Valid

  public List<TesOutput> getOutputs() {
    return outputs;
  }

  public void setOutputs(List<TesOutput> outputs) {
    this.outputs = outputs;
  }

  public TesTask resources(TesResources resources) {
    this.resources = resources;
    return this;
  }

  /**
   * Get resources
   * @return resources
  */
  @ApiModelProperty(value = "")

  @Valid

  public TesResources getResources() {
    return resources;
  }

  public void setResources(TesResources resources) {
    this.resources = resources;
  }

  public TesTask executors(List<TesExecutor> executors) {
    this.executors = executors;
    return this;
  }

  public TesTask addExecutorsItem(TesExecutor executorsItem) {
    if (this.executors == null) {
      this.executors = new ArrayList<>();
    }
    this.executors.add(executorsItem);
    return this;
  }

  /**
   * An array of executors to be run. Each of the executors will run one at a time sequentially. Each executor is a different command that will be run, and each can utilize a different docker image. But each of the executors will see the same mapped inputs and volumes that are declared in the parent CreateTask message.  Execution stops on the first error.
   * @return executors
  */
  @ApiModelProperty(required = true, value = "An array of executors to be run. Each of the executors will run one at a time sequentially. Each executor is a different command that will be run, and each can utilize a different docker image. But each of the executors will see the same mapped inputs and volumes that are declared in the parent CreateTask message.  Execution stops on the first error.")
  @NotNull
  @NotEmpty
  @Valid

  public List<TesExecutor> getExecutors() {
    return executors;
  }

  public void setExecutors(List<TesExecutor> executors) {
    this.executors = executors;
  }

  public TesTask volumes(List<String> volumes) {
    this.volumes = volumes;
    return this;
  }

  public TesTask addVolumesItem(String volumesItem) {
    if (this.volumes == null) {
      this.volumes = new ArrayList<>();
    }
    this.volumes.add(volumesItem);
    return this;
  }

  /**
   * Volumes are directories which may be used to share data between Executors. Volumes are initialized as empty directories by the system when the task starts and are mounted at the same path in each Executor.  For example, given a volume defined at `/vol/A`, executor 1 may write a file to `/vol/A/exec1.out.txt`, then executor 2 may read from that file.  (Essentially, this translates to a `docker run -v` flag where the container path is the same for each executor).
   * @return volumes
  */
  @ApiModelProperty(example = "[\"/vol/A/\"]", value = "Volumes are directories which may be used to share data between Executors. Volumes are initialized as empty directories by the system when the task starts and are mounted at the same path in each Executor.  For example, given a volume defined at `/vol/A`, executor 1 may write a file to `/vol/A/exec1.out.txt`, then executor 2 may read from that file.  (Essentially, this translates to a `docker run -v` flag where the container path is the same for each executor).")


  public List<@Pattern(regexp = ABSOLUTE_PATH_REGEXP, message = ABSOLUTE_PATH_MESSAGE) String> getVolumes() {
    return volumes;
  }

  public void setVolumes(List<String> volumes) {
    this.volumes = volumes;
  }

  public TesTask tags(Map<String, String> tags) {
    this.tags = tags;
    return this;
  }

  public TesTask putTagsItem(String key, String tagsItem) {
    if (this.tags == null) {
      this.tags = new HashMap<>();
    }
    this.tags.put(key, tagsItem);
    return this;
  }

  /**
   * A key-value map of arbitrary tags. These can be used to store meta-data and annotations about a task. Example: ``` {   \"tags\" : {       \"WORKFLOW_ID\" : \"cwl-01234\",       \"PROJECT_GROUP\" : \"alice-lab\"   } } ```
   * @return tags
  */
  @ApiModelProperty(example = "{\"WORKFLOW_ID\":\"cwl-01234\",\"PROJECT_GROUP\":\"alice-lab\"}", value = "A key-value map of arbitrary tags. These can be used to store meta-data and annotations about a task. Example: ``` {   \"tags\" : {       \"WORKFLOW_ID\" : \"cwl-01234\",       \"PROJECT_GROUP\" : \"alice-lab\"   } } ```")


  public Map<String, String> getTags() {
    return tags;
  }

  public void setTags(Map<String, String> tags) {
    this.tags = tags;
  }

  public TesTask logs(List<TesTaskLog> logs) {
    this.logs = logs;
    return this;
  }

  public TesTask addLogsItem(TesTaskLog logsItem) {
    if (this.logs == null) {
      this.logs = new ArrayList<>();
    }
    this.logs.add(logsItem);
    return this;
  }

  /**
   * Task logging information. Normally, this will contain only one entry, but in the case where a task fails and is retried, an entry will be appended to this list.
   * @return logs
  */
  @ApiModelProperty(readOnly = true, value = "Task logging information. Normally, this will contain only one entry, but in the case where a task fails and is retried, an entry will be appended to this list.")

  @Valid

  public List<TesTaskLog> getLogs() {
    return logs;
  }

  public void setLogs(List<TesTaskLog> logs) {
    this.logs = logs;
  }

  public TesTask creationTime(String creationTime) {
    this.creationTime = creationTime;
    return this;
  }

  /**
   * Date + time the task was created, in RFC 3339 format. This is set by the system, not the client.
   * @return creationTime
  */
  @ApiModelProperty(example = "2020-10-02T10:00:00-05:00", readOnly = true, value = "Date + time the task was created, in RFC 3339 format. This is set by the system, not the client.")


  public String getCreationTime() {
    return creationTime;
  }

  public void setCreationTime(String creationTime) {
    this.creationTime = creationTime;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesTask tesTask = (TesTask) o;
    return Objects.equals(this.id, tesTask.id) &&
        Objects.equals(this.state, tesTask.state) &&
        Objects.equals(this.name, tesTask.name) &&
        Objects.equals(this.description, tesTask.description) &&
        Objects.equals(this.inputs, tesTask.inputs) &&
        Objects.equals(this.outputs, tesTask.outputs) &&
        Objects.equals(this.resources, tesTask.resources) &&
        Objects.equals(this.executors, tesTask.executors) &&
        Objects.equals(this.volumes, tesTask.volumes) &&
        Objects.equals(this.tags, tesTask.tags) &&
        Objects.equals(this.logs, tesTask.logs) &&
        Objects.equals(this.creationTime, tesTask.creationTime);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, state, name, description, inputs, outputs, resources, executors, volumes, tags, logs, creationTime);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesTask {\n");
    
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    state: ").append(toIndentedString(state)).append("\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    sb.append("    inputs: ").append(toIndentedString(inputs)).append("\n");
    sb.append("    outputs: ").append(toIndentedString(outputs)).append("\n");
    sb.append("    resources: ").append(toIndentedString(resources)).append("\n");
    sb.append("    executors: ").append(toIndentedString(executors)).append("\n");
    sb.append("    volumes: ").append(toIndentedString(volumes)).append("\n");
    sb.append("    tags: ").append(toIndentedString(tags)).append("\n");
    sb.append("    logs: ").append(toIndentedString(logs)).append("\n");
    sb.append("    creationTime: ").append(toIndentedString(creationTime)).append("\n");
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

