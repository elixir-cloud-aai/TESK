package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonCreator;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import java.time.OffsetDateTime;
import uk.ac.ebi.tsc.tesk.tes.model.ServiceOrganization;
import uk.ac.ebi.tsc.tesk.tes.model.ServiceType;
import javax.validation.Valid;
import javax.validation.constraints.*;

/**
 * GA4GH service
 */
@ApiModel(description = "GA4GH service")
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-04-12T17:49:13.631+01:00[Europe/London]")
public class Service   {
  @JsonProperty("id")
  private String id;

  @JsonProperty("name")
  private String name;

  @JsonProperty("type")
  private ServiceType type;

  @JsonProperty("description")
  private String description;

  @JsonProperty("organization")
  private ServiceOrganization organization;

  @JsonProperty("contactUrl")
  private String contactUrl;

  @JsonProperty("documentationUrl")
  private String documentationUrl;

  @JsonProperty("createdAt")
  @org.springframework.format.annotation.DateTimeFormat(iso = org.springframework.format.annotation.DateTimeFormat.ISO.DATE_TIME)
  private OffsetDateTime createdAt;

  @JsonProperty("updatedAt")
  @org.springframework.format.annotation.DateTimeFormat(iso = org.springframework.format.annotation.DateTimeFormat.ISO.DATE_TIME)
  private OffsetDateTime updatedAt;

  @JsonProperty("environment")
  private String environment;

  @JsonProperty("version")
  private String version;

  public Service id(String id) {
    this.id = id;
    return this;
  }

  /**
   * Unique ID of this service. Reverse domain name notation is recommended, though not required. The identifier should attempt to be globally unique so it can be used in downstream aggregator services e.g. Service Registry.
   * @return id
  */
  @ApiModelProperty(example = "org.ga4gh.myservice", required = true, value = "Unique ID of this service. Reverse domain name notation is recommended, though not required. The identifier should attempt to be globally unique so it can be used in downstream aggregator services e.g. Service Registry.")
  @NotNull


  public String getId() {
    return id;
  }

  public void setId(String id) {
    this.id = id;
  }

  public Service name(String name) {
    this.name = name;
    return this;
  }

  /**
   * Name of this service. Should be human readable.
   * @return name
  */
  @ApiModelProperty(example = "My project", required = true, value = "Name of this service. Should be human readable.")
  @NotNull


  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public Service type(ServiceType type) {
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

  public ServiceType getType() {
    return type;
  }

  public void setType(ServiceType type) {
    this.type = type;
  }

  public Service description(String description) {
    this.description = description;
    return this;
  }

  /**
   * Description of the service. Should be human readable and provide information about the service.
   * @return description
  */
  @ApiModelProperty(example = "This service provides...", value = "Description of the service. Should be human readable and provide information about the service.")


  public String getDescription() {
    return description;
  }

  public void setDescription(String description) {
    this.description = description;
  }

  public Service organization(ServiceOrganization organization) {
    this.organization = organization;
    return this;
  }

  /**
   * Get organization
   * @return organization
  */
  @ApiModelProperty(required = true, value = "")
  @NotNull

  @Valid

  public ServiceOrganization getOrganization() {
    return organization;
  }

  public void setOrganization(ServiceOrganization organization) {
    this.organization = organization;
  }

  public Service contactUrl(String contactUrl) {
    this.contactUrl = contactUrl;
    return this;
  }

  /**
   * URL of the contact for the provider of this service, e.g. a link to a contact form (RFC 3986 format), or an email (RFC 2368 format).
   * @return contactUrl
  */
  @ApiModelProperty(example = "mailto:support@example.com", value = "URL of the contact for the provider of this service, e.g. a link to a contact form (RFC 3986 format), or an email (RFC 2368 format).")


  public String getContactUrl() {
    return contactUrl;
  }

  public void setContactUrl(String contactUrl) {
    this.contactUrl = contactUrl;
  }

  public Service documentationUrl(String documentationUrl) {
    this.documentationUrl = documentationUrl;
    return this;
  }

  /**
   * URL of the documentation of this service (RFC 3986 format). This should help someone learn how to use your service, including any specifics required to access data, e.g. authentication.
   * @return documentationUrl
  */
  @ApiModelProperty(example = "https://docs.myservice.example.com", value = "URL of the documentation of this service (RFC 3986 format). This should help someone learn how to use your service, including any specifics required to access data, e.g. authentication.")


  public String getDocumentationUrl() {
    return documentationUrl;
  }

  public void setDocumentationUrl(String documentationUrl) {
    this.documentationUrl = documentationUrl;
  }

  public Service createdAt(OffsetDateTime createdAt) {
    this.createdAt = createdAt;
    return this;
  }

  /**
   * Timestamp describing when the service was first deployed and available (RFC 3339 format)
   * @return createdAt
  */
  @ApiModelProperty(example = "2019-06-04T12:58:19Z", value = "Timestamp describing when the service was first deployed and available (RFC 3339 format)")

  @Valid

  public OffsetDateTime getCreatedAt() {
    return createdAt;
  }

  public void setCreatedAt(OffsetDateTime createdAt) {
    this.createdAt = createdAt;
  }

  public Service updatedAt(OffsetDateTime updatedAt) {
    this.updatedAt = updatedAt;
    return this;
  }

  /**
   * Timestamp describing when the service was last updated (RFC 3339 format)
   * @return updatedAt
  */
  @ApiModelProperty(example = "2019-06-04T12:58:19Z", value = "Timestamp describing when the service was last updated (RFC 3339 format)")

  @Valid

  public OffsetDateTime getUpdatedAt() {
    return updatedAt;
  }

  public void setUpdatedAt(OffsetDateTime updatedAt) {
    this.updatedAt = updatedAt;
  }

  public Service environment(String environment) {
    this.environment = environment;
    return this;
  }

  /**
   * Environment the service is running in. Use this to distinguish between production, development and testing/staging deployments. Suggested values are prod, test, dev, staging. However this is advised and not enforced.
   * @return environment
  */
  @ApiModelProperty(example = "test", value = "Environment the service is running in. Use this to distinguish between production, development and testing/staging deployments. Suggested values are prod, test, dev, staging. However this is advised and not enforced.")


  public String getEnvironment() {
    return environment;
  }

  public void setEnvironment(String environment) {
    this.environment = environment;
  }

  public Service version(String version) {
    this.version = version;
    return this;
  }

  /**
   * Version of the service being described. Semantic versioning is recommended, but other identifiers, such as dates or commit hashes, are also allowed. The version should be changed whenever the service is updated.
   * @return version
  */
  @ApiModelProperty(example = "1.0.0", required = true, value = "Version of the service being described. Semantic versioning is recommended, but other identifiers, such as dates or commit hashes, are also allowed. The version should be changed whenever the service is updated.")
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
    Service service = (Service) o;
    return Objects.equals(this.id, service.id) &&
        Objects.equals(this.name, service.name) &&
        Objects.equals(this.type, service.type) &&
        Objects.equals(this.description, service.description) &&
        Objects.equals(this.organization, service.organization) &&
        Objects.equals(this.contactUrl, service.contactUrl) &&
        Objects.equals(this.documentationUrl, service.documentationUrl) &&
        Objects.equals(this.createdAt, service.createdAt) &&
        Objects.equals(this.updatedAt, service.updatedAt) &&
        Objects.equals(this.environment, service.environment) &&
        Objects.equals(this.version, service.version);
  }

  @Override
  public int hashCode() {
    return Objects.hash(id, name, type, description, organization, contactUrl, documentationUrl, createdAt, updatedAt, environment, version);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class Service {\n");
    
    sb.append("    id: ").append(toIndentedString(id)).append("\n");
    sb.append("    name: ").append(toIndentedString(name)).append("\n");
    sb.append("    type: ").append(toIndentedString(type)).append("\n");
    sb.append("    description: ").append(toIndentedString(description)).append("\n");
    sb.append("    organization: ").append(toIndentedString(organization)).append("\n");
    sb.append("    contactUrl: ").append(toIndentedString(contactUrl)).append("\n");
    sb.append("    documentationUrl: ").append(toIndentedString(documentationUrl)).append("\n");
    sb.append("    createdAt: ").append(toIndentedString(createdAt)).append("\n");
    sb.append("    updatedAt: ").append(toIndentedString(updatedAt)).append("\n");
    sb.append("    environment: ").append(toIndentedString(environment)).append("\n");
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

