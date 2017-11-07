package uk.ac.ebi.tsc.tesk.model;

import java.util.Objects;
import io.swagger.annotations.ApiModel;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * CancelTaskResponse describes a response from the CancelTask endpoint.
 */
@ApiModel(description = "CancelTaskResponse describes a response from the CancelTask endpoint.")
@javax.annotation.Generated(value = "io.swagger.codegen.languages.SpringCodegen", date = "2017-11-07T14:45:12.993Z")

public class TesCancelTaskResponse   {

  @Override
  public boolean equals(java.lang.Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    return true;
  }

  @Override
  public int hashCode() {
    return Objects.hash();
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesCancelTaskResponse {\n");
    
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

