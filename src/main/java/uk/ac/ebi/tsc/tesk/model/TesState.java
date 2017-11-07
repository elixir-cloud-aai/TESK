package uk.ac.ebi.tsc.tesk.model;

import java.util.Objects;
import io.swagger.annotations.ApiModel;
import com.fasterxml.jackson.annotation.JsonValue;
import javax.validation.Valid;
import javax.validation.constraints.*;

import com.fasterxml.jackson.annotation.JsonCreator;

/**
 * Task states.   - PAUSED: An implementation *may* have the ability to pause a task, but this is not required.
 */
public enum TesState {
  
  UNKNOWN("UNKNOWN"),
  
  QUEUED("QUEUED"),
  
  INITIALIZING("INITIALIZING"),
  
  RUNNING("RUNNING"),
  
  PAUSED("PAUSED"),
  
  COMPLETE("COMPLETE"),
  
  ERROR("ERROR"),
  
  SYSTEM_ERROR("SYSTEM_ERROR"),
  
  CANCELED("CANCELED");

  private String value;

  TesState(String value) {
    this.value = value;
  }

  @Override
  @JsonValue
  public String toString() {
    return String.valueOf(value);
  }

  @JsonCreator
  public static TesState fromValue(String text) {
    for (TesState b : TesState.values()) {
      if (String.valueOf(b.value).equals(text)) {
        return b;
      }
    }
    return null;
  }
}

