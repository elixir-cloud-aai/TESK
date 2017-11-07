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
import uk.ac.ebi.tsc.tesk.model.TesExecutor;
import uk.ac.ebi.tsc.tesk.model.TesResources;
import uk.ac.ebi.tsc.tesk.model.TesState;
import uk.ac.ebi.tsc.tesk.model.TesTaskLog;
import uk.ac.ebi.tsc.tesk.model.TesTaskParameter;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * Task describes an instance of a task.
 */
@ApiModel(description = "Task describes an instance of a task.")
@javax.annotation.Generated(value = "io.swagger.codegen.languages.SpringCodegen", date = "2017-11-07T14:45:12.993Z")

public class TesTask   {
  @JsonProperty("id")
  private String id = null;

  @JsonProperty("state")
  private TesState state = null;

  @JsonProperty("name")
  private String name = null;

  @JsonProperty("project")
  private String project = null;

  @JsonProperty("description")
  private String description = null;

  @JsonProperty("inputs")
  private List<TesTaskParameter> inputs = null;

  @JsonProperty("outputs")
  private List<TesTaskParameter> outputs = null;

  @JsonProperty("resources")
  private TesResources resources = null;

  @JsonProperty("executors")
  private List<TesExecutor> executors = null;

  @JsonProperty("volumes")
  private List<String> volumes = null;

  @JsonProperty("tags")
  private Map<String, String> tags = null;

  @JsonProperty("logs")
  private List<TesTaskLog> logs = null;

  public TesTask id(String id) {
    this.id = id;
    return this;
  }

   /**
   * Task identifier assigned by the server.
   * @return id
  **/
  @ApiModelProperty(value = "Task identifier assigned by the server.")


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
  **/
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
   * Get name
   * @return name
  **/
  @ApiModelProperty(value = "")


  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public TesTask project(String project) {
    this.project = project;
    return this;
  }

   /**
   * Describes the project this task is associated with. Commonly used for billing on cloud providers (AWS, Google Cloud, etc).
   * @return project
  **/
  @ApiModelProperty(value = "Describes the project this task is associated with. Commonly used for billing on cloud providers (AWS, Google Cloud, etc).")


  public String getProject() {
    return project;
  }

  public void setProject(String project) {
    this.project = project;
  }

  public TesTask description(String description) {
    this.description = description;
    return this;
  }

   /**
   * Get description
   * @return description
  **/
  @ApiModelProperty(value = "")


  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public TesTask inputs(List<TesTaskParameter> inputs) {
    this.inputs = inputs;
    return this;
  }

  public TesTask addInputsItem(TesTaskParameter inputsItem) {
    if (this.inputs == null) {
      this.inputs = new ArrayList<TesTaskParameter>();
    }
    this.inputs.add(inputsItem);
    return this;
  }

   /**
   * Input files. Inputs will be downloaded and mounted into the executor container.
   * @return inputs
  **/
  @ApiModelProperty(value = "Input files. Inputs will be downloaded and mounted into the executor container.")

  @Valid

  public List<TesTaskParameter> getInputs() {
    return inputs;
  }

  public void setInputs(List<TesTaskParameter> inputs) {
    this.inputs = inputs;
  }

  public TesTask outputs(List<TesTaskParameter> outputs) {
    this.outputs = outputs;
    return this;
  }

  public TesTask addOutputsItem(TesTaskParameter outputsItem) {
    if (this.outputs == null) {
      this.outputs = new ArrayList<TesTaskParameter>();
    }
    this.outputs.add(outputsItem);
    return this;
  }

   /**
   * Output files. Outputs will be uploaded from the executor container to long-term storage.
   * @return outputs
  **/
  @ApiModelProperty(value = "Output files. Outputs will be uploaded from the executor container to long-term storage.")

  @Valid

  public List<TesTaskParameter> getOutputs() {
    return outputs;
  }

  public void setOutputs(List<TesTaskParameter> outputs) {
    this.outputs = outputs;
  }

  public TesTask resources(TesResources resources) {
    this.resources = resources;
    return this;
  }

   /**
   * Request that the task be run with these resources.
   * @return resources
  **/
  @ApiModelProperty(value = "Request that the task be run with these resources.")

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
      this.executors = new ArrayList<TesExecutor>();
    }
    this.executors.add(executorsItem);
    return this;
  }

   /**
   * A list of executors to be run, sequentially. Execution stops on the first error.
   * @return executors
  **/
  @ApiModelProperty(value = "A list of executors to be run, sequentially. Execution stops on the first error.")

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
      this.volumes = new ArrayList<String>();
    }
    this.volumes.add(volumesItem);
    return this;
  }

   /**
   * Declared volumes. Volumes are shared between executors. Volumes for inputs and outputs are  inferred and should not be declared here.
   * @return volumes
  **/
  @ApiModelProperty(value = "Declared volumes. Volumes are shared between executors. Volumes for inputs and outputs are  inferred and should not be declared here.")


  public List<String> getVolumes() {
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
      this.tags = new HashMap<String, String>();
    }
    this.tags.put(key, tagsItem);
    return this;
  }

   /**
   * A key-value map of arbitrary tags.
   * @return tags
  **/
  @ApiModelProperty(value = "A key-value map of arbitrary tags.")


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
      this.logs = new ArrayList<TesTaskLog>();
    }
    this.logs.add(logsItem);
    return this;
  }

   /**
   * Task logging information. Normally, this will contain only one entry, but in the case where a task fails and is retried, an entry will be appended to this list.
   * @return logs
  **/
  @ApiModelProperty(value = "Task logging information. Normally, this will contain only one entry, but in the case where a task fails and is retried, an entry will be appended to this list.")

  @Valid

  public List<TesTaskLog> getLogs() {
    return logs;
  }

  public void setLogs(List<TesTaskLog> logs) {
    this.logs = logs;
  }


  @Override
  public boolean equals(java.lang.Object o) {
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
        Objects.equals(this.project, tesTask.project) &&
        Objects.equals(this.description, tesTask.description) &&
        Objects.equals(this.inputs, tesTask.inputs) &&
        Objects.equals(this.outputs, tesTask.outputs) &&
        Objects.equals(this.resources, tesTask.resources) &&
        Objects.equals(this.executors, tesTask.executors) &&
        Objects.equals(this.volumes, tesTask.volumes) &&
        Objects.equals(this.tags, tesTask.tags) &&
        Objects.equals(this.logs, tesTask.logs);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, state, name, project, description, inputs, outputs, resources, executors, volumes, tags, logs);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesTask {\n");
    
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    state: ").append(toIndentedString(state)).append("\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    project: ").append(toIndentedString(project)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    sb.append("    inputs: ").append(toIndentedString(inputs)).append("\n");
    sb.append("    outputs: ").append(toIndentedString(outputs)).append("\n");
    sb.append("    resources: ").append(toIndentedString(resources)).append("\n");
    sb.append("    executors: ").append(toIndentedString(executors)).append("\n");
    sb.append("    volumes: ").append(toIndentedString(volumes)).append("\n");
    sb.append("    tags: ").append(toIndentedString(tags)).append("\n");
    sb.append("    logs: ").append(toIndentedString(logs)).append("\n");
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

