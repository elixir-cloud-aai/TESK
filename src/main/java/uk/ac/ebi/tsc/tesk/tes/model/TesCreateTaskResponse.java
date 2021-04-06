package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;

import javax.validation.constraints.*;

/**
 * CreateTaskResponse describes a response from the CreateTask endpoint. It will include the task ID that can be used to look up the status of the job.
 */
@ApiModel(description = "CreateTaskResponse describes a response from the CreateTask endpoint. It will include the task ID that can be used to look up the status of the job.")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesCreateTaskResponse   {
  @JsonProperty("id")
  private String id;

  public TesCreateTaskResponse id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Task identifier assigned by the server.
   * @return id
  */
  @ApiModelProperty(required = true, value = "Task identifier assigned by the server.")
  @NotNull


  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesCreateTaskResponse tesCreateTaskResponse = (TesCreateTaskResponse) o;
    return Objects.equals(this.id, tesCreateTaskResponse.id);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesCreateTaskResponse {\n");
    
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
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

