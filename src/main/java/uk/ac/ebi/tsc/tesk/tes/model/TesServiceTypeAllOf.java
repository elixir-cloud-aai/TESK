package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import io.swagger.annotations.ApiModelProperty;

import javax.validation.constraints.*;

/**
 * TesServiceTypeAllOf
 */
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesServiceTypeAllOf   {
  /**
   * Gets or Sets artifact
   */
  public enum ArtifactEnum {
    TES("tes");

    private String value;

    ArtifactEnum(String value) {
      this.value = value;
    }

    @JsonValue
    public String getValue() {
      return value;
    }

    @Override
    public String toString() {
      return String.valueOf(value);
    }

    @JsonCreator
    public static ArtifactEnum fromValue(String value) {
      for (ArtifactEnum b : ArtifactEnum.values()) {
        if (b.value.equals(value)) {
          return b;
        }
      }
      throw new IllegalArgumentException("Unexpected value '" + value + "'");
    }
  }

  @JsonProperty("artifact")
  private ArtifactEnum artifact;

  public TesServiceTypeAllOf artifact(ArtifactEnum artifact) {
    this.artifact = artifact;
    return this;
  }

  /**
   * Get artifact
   * @return artifact
  */
  @ApiModelProperty(example = "tes", required = true, value = "")
  @NotNull


  public ArtifactEnum getArtifact() {
    return artifact;
  }

  public void setArtifact(ArtifactEnum artifact) {
    this.artifact = artifact;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesServiceTypeAllOf tesServiceTypeAllOf = (TesServiceTypeAllOf) o;
    return Objects.equals(this.artifact, tesServiceTypeAllOf.artifact);
  }

  @Override
  public int hashCode() {
    return Objects.hash(artifact);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesServiceTypeAllOf {\n");
    
    sb.append("    artifact: ").append(toIndentedString(artifact)).append("\n");
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

