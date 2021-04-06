package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;

import javax.validation.Valid;
import javax.validation.constraints.*;

import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.ABSOLUTE_PATH_MESSAGE;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.ABSOLUTE_PATH_REGEXP;

/**
 * Output describes Task output files.
 */
@ApiModel(description = "Output describes Task output files.")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesOutput   {
  @JsonProperty("name")
  private String name;

  @JsonProperty("description")
  private String description;

  @JsonProperty("url")
  private String url;

  @JsonProperty("path")
  private String path;

  @JsonProperty("type")
  private TesFileType type = TesFileType.FILE;

  public TesOutput name(String name) {
    this.name = name;
    return this;
  }

  /**
   * User-provided name of output file
   * @return name
  */
  @ApiModelProperty(value = "User-provided name of output file")


  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public TesOutput description(String description) {
    this.description = description;
    return this;
  }

  /**
   * Optional users provided description field, can be used for documentation.
   * @return description
  */
  @ApiModelProperty(value = "Optional users provided description field, can be used for documentation.")


  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public TesOutput url(String url) {
    this.url = url;
    return this;
  }

  /**
   * URL for the file to be copied by the TES server after the task is complete. For Example:  - `s3://my-object-store/file1`  - `gs://my-bucket/file2`  - `file:///path/to/my/file`
   * @return url
  */
  @ApiModelProperty(required = true, value = "URL for the file to be copied by the TES server after the task is complete. For Example:  - `s3://my-object-store/file1`  - `gs://my-bucket/file2`  - `file:///path/to/my/file`")
  @NotNull
  @NotBlank

  public String getUrl() {
    return url;
  }

  public void setUrl(String url) {
    this.url = url;
  }

  public TesOutput path(String path) {
    this.path = path;
    return this;
  }

  /**
   * Path of the file inside the container. Must be an absolute path.
   * @return path
  */
  @ApiModelProperty(required = true, value = "Path of the file inside the container. Must be an absolute path.")
  @NotNull
  @Pattern(regexp = ABSOLUTE_PATH_REGEXP, message = ABSOLUTE_PATH_MESSAGE)
  @NotBlank
  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public TesOutput type(TesFileType type) {
    this.type = type;
    return this;
  }

  /**
   * Get type
   * @return type
  */
  @ApiModelProperty(required = true, value = "")
  @NotNull

  @Valid

  public TesFileType getType() {
    return type;
  }

  public void setType(TesFileType type) {
    this.type = type;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesOutput tesOutput = (TesOutput) o;
    return Objects.equals(this.name, tesOutput.name) &&
        Objects.equals(this.description, tesOutput.description) &&
        Objects.equals(this.url, tesOutput.url) &&
        Objects.equals(this.path, tesOutput.path) &&
        Objects.equals(this.type, tesOutput.type);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name, description, url, path, type);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesOutput {\n");
    
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    sb.append("    url: ").append(toIndentedString(url)).append("\n");
    sb.append("    path: ").append(toIndentedString(path)).append("\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
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

