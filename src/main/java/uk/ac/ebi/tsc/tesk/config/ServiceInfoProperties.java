package uk.ac.ebi.tsc.tesk.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * @author aniewielska
 * @since 03/06/2020
 */
@Configuration
@ConfigurationProperties(prefix = "tesk.api.service-info")
@Data
public class ServiceInfoProperties {
    private String name;
    private String documentation;
}
