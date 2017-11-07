package uk.ac.ebi.tsc.tesk.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * Ports describes the port binding between the container and host. For example, a Docker implementation might map this to &#x60;docker run -p host:container&#x60;.
 */
@ApiModel(description = "Ports describes the port binding between the container and host. For example, a Docker implementation might map this to `docker run -p host:container`.")
@javax.annotation.Generated(value = "io.swagger.codegen.languages.SpringCodegen", date = "2017-11-07T14:45:12.993Z")

public class TesPorts   {
  @JsonProperty("container")
  private Long container = null;

  @JsonProperty("host")
  private Long host = null;

  public TesPorts container(Long container) {
    this.container = container;
    return this;
  }

   /**
   * Port number opened inside the container.
   * @return container
  **/
  @ApiModelProperty(value = "Port number opened inside the container.")


  public Long getContainer() {
    return container;
  }

  public void setContainer(Long container) {
    this.container = container;
  }

  public TesPorts host(Long host) {
    this.host = host;
    return this;
  }

   /**
   * Port number opened on the host. Defaults to 0, which assigns a random port on the host.
   * @return host
  **/
  @ApiModelProperty(value = "Port number opened on the host. Defaults to 0, which assigns a random port on the host.")


  public Long getHost() {
    return host;
  }

  public void setHost(Long host) {
    this.host = host;
  }


  @Override
  public boolean equals(java.lang.Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesPorts tesPorts = (TesPorts) o;
    return Objects.equals(this.container, tesPorts.container) &&
        Objects.equals(this.host, tesPorts.host);
  }

  @Override
  public int hashCode() {
    return Objects.hash(container, host);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesPorts {\n");
    
    sb.append("    container: ").append(toIndentedString(container)).append("\n");
    sb.append("    host: ").append(toIndentedString(host)).append("\n");
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

