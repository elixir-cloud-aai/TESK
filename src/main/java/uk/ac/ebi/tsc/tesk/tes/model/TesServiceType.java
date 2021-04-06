package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;
import io.swagger.annotations.ApiModelProperty;

import javax.validation.constraints.*;

/**
 * TesServiceType
 */
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesServiceType   {
  @JsonProperty("group")
  private String group;

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

  @JsonProperty("version")
  private String version;

  public TesServiceType group(String group) {
    this.group = group;
    return this;
  }

  /**
   * Namespace in reverse domain name format. Use `org.ga4gh` for implementations compliant with official GA4GH specifications. For services with custom APIs not standardized by GA4GH, or implementations diverging from official GA4GH specifications, use a different namespace (e.g. your organization's reverse domain name).
   * @return group
  */
  @ApiModelProperty(example = "org.ga4gh", required = true, value = "Namespace in reverse domain name format. Use `org.ga4gh` for implementations compliant with official GA4GH specifications. For services with custom APIs not standardized by GA4GH, or implementations diverging from official GA4GH specifications, use a different namespace (e.g. your organization's reverse domain name).")
  @NotNull


  public String getGroup() {
    return group;
  }

  public void setGroup(String group) {
    this.group = group;
  }

  public TesServiceType artifact(ArtifactEnum artifact) {
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

  public TesServiceType version(String version) {
    this.version = version;
    return this;
  }

  /**
   * Version of the API or specification. GA4GH specifications use semantic versioning.
   * @return version
  */
  @ApiModelProperty(example = "1.0.0", required = true, value = "Version of the API or specification. GA4GH specifications use semantic versioning.")
  @NotNull


  public String getVersion() {
    return version;
  }

  public void setVersion(String version) {
    this.version = version;
  }


  @Override
  public boolean equals(Object o) {
    if (this == o) {
      return true;
    }
    if (o == null || getClass() != o.getClass()) {
      return false;
    }
    TesServiceType tesServiceType = (TesServiceType) o;
    return Objects.equals(this.group, tesServiceType.group) &&
        Objects.equals(this.artifact, tesServiceType.artifact) &&
        Objects.equals(this.version, tesServiceType.version);
  }

  @Override
  public int hashCode() {
    return Objects.hash(group, artifact, version);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesServiceType {\n");
    
    sb.append("    group: ").append(toIndentedString(group)).append("\n");
    sb.append("    artifact: ").append(toIndentedString(artifact)).append("\n");
    sb.append("    version: ").append(toIndentedString(version)).append("\n");
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

