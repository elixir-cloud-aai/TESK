package uk.ac.ebi.tsc.tesk.config.swagger;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

/**
 * Swagger Configuration for version without authentication
 *
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Configuration
@EnableSwagger2
@Profile("noauth")
public class SwaggerConfigNoAuth {
    @Bean
    public Docket api() {
        return new Docket(DocumentationType.SWAGGER_2)
                .select()
                .apis(RequestHandlerSelectors.basePackage("uk.ac.ebi.tsc.tesk.api"))
                .paths(PathSelectors.any())
                .build();

    }
}
