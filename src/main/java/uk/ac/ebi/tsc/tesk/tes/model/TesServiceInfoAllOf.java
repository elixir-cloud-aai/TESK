package uk.ac.ebi.tsc.tesk.tes.model;

import java.util.Objects;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.annotations.ApiModelProperty;
import java.util.ArrayList;
import java.util.List;
import javax.validation.Valid;

/**
 * TesServiceInfoAllOf
 */
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
public class TesServiceInfoAllOf   {
  @JsonProperty("storage")
  @Valid
  private List<String> storage = null;

  @JsonProperty("type")
  private TesServiceType type = null;

  public TesServiceInfoAllOf storage(List<String> storage) {
    this.storage = storage;
    return this;
  }

  public TesServiceInfoAllOf addStorageItem(String storageItem) {
    if (this.storage == null) {
      this.storage = new ArrayList<>();
    }
    this.storage.add(storageItem);
    return this;
  }

  /**
   * Lists some, but not necessarily all, storage locations supported by the service.
   * @return storage
  */
  @ApiModelProperty(example = "[\"file:///path/to/local/funnel-storage\",\"s3://ohsu-compbio-funnel/storage\"]", value = "Lists some, but not necessarily all, storage locations supported by the service.")


  public List<String> getStorage() {
    return storage;
  }

  public void setStorage(List<String> storage) {
    this.storage = storage;
  }

  public TesServiceInfoAllOf type(TesServiceType type) {
    this.type = type;
    return this;
  }

  /**
   * Get type
   * @return type
  */
  @ApiModelProperty(value = "")

  @Valid

  public TesServiceType getType() {
    return type;
  }

  public void setType(TesServiceType type) {
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
    TesServiceInfoAllOf tesServiceInfoAllOf = (TesServiceInfoAllOf) o;
    return Objects.equals(this.storage, tesServiceInfoAllOf.storage) &&
        Objects.equals(this.type, tesServiceInfoAllOf.type);
  }

  @Override
  public int hashCode() {
    return Objects.hash(storage, type);
  }

  @Override
  public String toString() {
    StringBuilder sb = new StringBuilder();
    sb.append("class TesServiceInfoAllOf {\n");
    
    sb.append("    storage: ").append(toIndentedString(storage)).append("\n");
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

