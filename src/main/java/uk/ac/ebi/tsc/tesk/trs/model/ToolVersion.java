package uk.ac.ebi.tsc.tesk.trs.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

/**
 * @author aniewielska
 * @since 22/09/2020
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class ToolVersion {
    private String id;
    private String url;
    private List<ImageData> images = new ArrayList<>();
}
