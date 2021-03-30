package uk.ac.ebi.tsc.tesk.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.net.URI;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * Organization providing the service
 */
@ApiModel(description = "Organization providing the service")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class ServiceOrganization   {
  @JsonProperty("name")
  private String name;

  @JsonProperty("url")
  private URI url;

  public ServiceOrganization name(String name) {
    this.name = name;
    return this;
  }

  /**
   * Name of the organization responsible for the service
   * @return name
  */
  @ApiModelProperty(example = "My organization", required = true, value = "Name of the organization responsible for the service")
  @NotNull


  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public ServiceOrganization url(URI url) {
    this.url = url;
    return this;
  }

  /**
   * URL of the website of the organization (RFC 3986 format)
   * @return url
  */
  @ApiModelProperty(example = "https://example.com", required = true, value = "URL of the website of the organization (RFC 3986 format)")
  @NotNull

  @Valid

  public URI getUrl() {
    return url;
  }

  public void setUrl(URI url) {
    this.url = url;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    ServiceOrganization serviceOrganization = (ServiceOrganization) o;
    return Objects.equals(this.name, serviceOrganization.name) &&
        Objects.equals(this.url, serviceOrganization.url);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name, url);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class ServiceOrganization {\n");
    
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    url: ").append(toIndentedString(url)).append("\n");
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

