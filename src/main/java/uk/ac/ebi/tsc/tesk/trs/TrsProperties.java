package uk.ac.ebi.tsc.tesk.trs;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * @author aniewielska
 * @since 22/09/2020
 */
@Configuration
@ConfigurationProperties(prefix = "tesk.api.trs")
@Data
public class TrsProperties {
    private String uriPattern;
    private String urlPattern;
}

