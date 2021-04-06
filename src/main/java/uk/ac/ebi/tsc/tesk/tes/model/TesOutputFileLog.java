package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;

import javax.validation.constraints.*;

/**
 * OutputFileLog describes a single output file. This describes file details after the task has completed successfully, for logging purposes.
 */
@ApiModel(description = "OutputFileLog describes a single output file. This describes file details after the task has completed successfully, for logging purposes.")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesOutputFileLog   {
  @JsonProperty("url")
  private String url;

  @JsonProperty("path")
  private String path;

  @JsonProperty("size_bytes")
  private String sizeBytes;

  public TesOutputFileLog url(String url) {
    this.url = url;
    return this;
  }

  /**
   * URL of the file in storage, e.g. s3://bucket/file.txt
   * @return url
  */
  @ApiModelProperty(required = true, value = "URL of the file in storage, e.g. s3://bucket/file.txt")
  @NotNull


  public String getUrl() {
    return url;
  }

  public void setUrl(String url) {
    this.url = url;
  }

  public TesOutputFileLog path(String path) {
    this.path = path;
    return this;
  }

  /**
   * Path of the file inside the container. Must be an absolute path.
   * @return path
  */
  @ApiModelProperty(required = true, value = "Path of the file inside the container. Must be an absolute path.")
  @NotNull


  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public TesOutputFileLog sizeBytes(String sizeBytes) {
    this.sizeBytes = sizeBytes;
    return this;
  }

  /**
   * Size of the file in bytes. Note, this is currently coded as a string because official JSON doesn't support int64 numbers.
   * @return sizeBytes
  */
  @ApiModelProperty(example = "[\"1024\"]", required = true, value = "Size of the file in bytes. Note, this is currently coded as a string because official JSON doesn't support int64 numbers.")
  @NotNull


  public String getSizeBytes() {
    return sizeBytes;
  }

  public void setSizeBytes(String sizeBytes) {
    this.sizeBytes = sizeBytes;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesOutputFileLog tesOutputFileLog = (TesOutputFileLog) o;
    return Objects.equals(this.url, tesOutputFileLog.url) &&
        Objects.equals(this.path, tesOutputFileLog.path) &&
        Objects.equals(this.sizeBytes, tesOutputFileLog.sizeBytes);
  }

  @Override
  public int hashCode() {
    return Objects.hash(url, path, sizeBytes);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesOutputFileLog {\n");
    
    sb.append("    url: ").append(toIndentedString(url)).append("\n");
    sb.append("    path: ").append(toIndentedString(path)).append("\n");
    sb.append("    sizeBytes: ").append(toIndentedString(sizeBytes)).append("\n");
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

