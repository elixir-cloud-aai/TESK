package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.util.ArrayList;
import java.util.List;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * ListTasksResponse describes a response from the ListTasks endpoint.
 */
@ApiModel(description = "ListTasksResponse describes a response from the ListTasks endpoint.")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesListTasksResponse   {
  @JsonProperty("tasks")
  @Valid
  private List<TesTask> tasks = new ArrayList<>();

  @JsonProperty("next_page_token")
  private String nextPageToken;

  public TesListTasksResponse tasks(List<TesTask> tasks) {
    this.tasks = tasks;
    return this;
  }

  public TesListTasksResponse addTasksItem(TesTask tasksItem) {
    if (this.tasks == null) {
      this.tasks = new ArrayList<>();
    }
    this.tasks.add(tasksItem);
    return this;
  }

  /**
   * List of tasks. These tasks will be based on the original submitted task document, but with other fields, such as the job state and logging info, added/changed as the job progresses.
   * @return tasks
  */
  @ApiModelProperty(required = true, value = "List of tasks. These tasks will be based on the original submitted task document, but with other fields, such as the job state and logging info, added/changed as the job progresses.")
  @NotNull

  @Valid

  public List<TesTask> getTasks() {
    return tasks;
  }

  public void setTasks(List<TesTask> tasks) {
    this.tasks = tasks;
  }

  public TesListTasksResponse nextPageToken(String nextPageToken) {
    this.nextPageToken = nextPageToken;
    return this;
  }

  /**
   * Token used to return the next page of results. This value can be used in the `page_token` field of the next ListTasks request.
   * @return nextPageToken
  */
  @ApiModelProperty(value = "Token used to return the next page of results. This value can be used in the `page_token` field of the next ListTasks request.")


  public String getNextPageToken() {
    return nextPageToken;
  }

  public void setNextPageToken(String nextPageToken) {
    this.nextPageToken = nextPageToken;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesListTasksResponse tesListTasksResponse = (TesListTasksResponse) o;
    return Objects.equals(this.tasks, tesListTasksResponse.tasks) &&
        Objects.equals(this.nextPageToken, tesListTasksResponse.nextPageToken);
  }

  @Override
  public int hashCode() {
    return Objects.hash(tasks, nextPageToken);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesListTasksResponse {\n");
    
    sb.append("    tasks: ").append(toIndentedString(tasks)).append("\n");
    sb.append("    nextPageToken: ").append(toIndentedString(nextPageToken)).append("\n");
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

