package uk.ac.ebi.tsc.tesk.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import uk.ac.ebi.tsc.tesk.model.TesFileType;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * TaskParameter describes input and output files for a Task.
 */
@ApiModel(description = "TaskParameter describes input and output files for a Task.")
@javax.annotation.Generated(value = "io.swagger.codegen.languages.SpringCodegen", date = "2017-11-07T14:45:12.993Z")

public class TesTaskParameter   {
  @JsonProperty("name")
  private String name = null;

  @JsonProperty("description")
  private String description = null;

  @JsonProperty("url")
  private String url = null;

  @JsonProperty("path")
  private String path = null;

  @JsonProperty("type")
  private TesFileType type = null;

  @JsonProperty("contents")
  private String contents = null;

  public TesTaskParameter name(String name) {
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

  public TesTaskParameter description(String description) {
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

  public TesTaskParameter url(String url) {
    this.url = url;
    return this;
  }

   /**
   * REQUIRED, unless \"contents\" is set.  URL in long term storage, for example: s3://my-object-store/file1 gs://my-bucket/file2 file:///path/to/my/file /path/to/my/file etc...
   * @return url
  **/
  @ApiModelProperty(value = "REQUIRED, unless \"contents\" is set.  URL in long term storage, for example: s3://my-object-store/file1 gs://my-bucket/file2 file:///path/to/my/file /path/to/my/file etc...")


  public String getUrl() {
    return url;
  }

  public void setUrl(String url) {
    this.url = url;
  }

  public TesTaskParameter path(String path) {
    this.path = path;
    return this;
  }

   /**
   * Path of the file inside the container. Must be an absolute path.
   * @return path
  **/
  @ApiModelProperty(value = "Path of the file inside the container. Must be an absolute path.")


  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public TesTaskParameter type(TesFileType type) {
    this.type = type;
    return this;
  }

   /**
   * Type of the file, FILE or DIRECTORY
   * @return type
  **/
  @ApiModelProperty(value = "Type of the file, FILE or DIRECTORY")

  @Valid

  public TesFileType getType() {
    return type;
  }

  public void setType(TesFileType type) {
    this.type = type;
  }

  public TesTaskParameter contents(String contents) {
    this.contents = contents;
    return this;
  }

   /**
   * File contents literal.  Implementations should support a minimum of 128 KiB in this field and may define its own maximum. UTF-8 encoded  If contents is not empty, \"url\" must be ignored.
   * @return contents
  **/
  @ApiModelProperty(value = "File contents literal.  Implementations should support a minimum of 128 KiB in this field and may define its own maximum. UTF-8 encoded  If contents is not empty, \"url\" must be ignored.")


  public String getContents() {
    return contents;
  }

  public void setContents(String contents) {
    this.contents = contents;
  }


  @Override
  public boolean equals(java.lang.Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesTaskParameter tesTaskParameter = (TesTaskParameter) o;
    return Objects.equals(this.name, tesTaskParameter.name) &&
        Objects.equals(this.description, tesTaskParameter.description) &&
        Objects.equals(this.url, tesTaskParameter.url) &&
        Objects.equals(this.path, tesTaskParameter.path) &&
        Objects.equals(this.type, tesTaskParameter.type) &&
        Objects.equals(this.contents, tesTaskParameter.contents);
  }

  @Override
  public int hashCode() {
    return Objects.hash(name, description, url, path, type, contents);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesTaskParameter {\n");
    
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    sb.append("    url: ").append(toIndentedString(url)).append("\n");
    sb.append("    path: ").append(toIndentedString(path)).append("\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    contents: ").append(toIndentedString(contents)).append("\n");
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

