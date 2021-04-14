package uk.ac.ebi.tsc.tesk.config.swagger;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.RequestMapping;
import springfox.documentation.builders.OAuthBuilder;
import springfox.documentation.builders.PathSelectors;
import springfox.documentation.builders.RequestHandlerSelectors;
import springfox.documentation.service.*;
import springfox.documentation.spi.DocumentationType;
import springfox.documentation.spi.service.contexts.SecurityContext;
import springfox.documentation.spring.web.plugins.Docket;
import springfox.documentation.swagger.web.SecurityConfiguration;
import springfox.documentation.swagger.web.SecurityConfigurationBuilder;
import springfox.documentation.swagger2.annotations.EnableSwagger2;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * Swagger Configuration
 * Configures securing all endpoints with OAuth2 (swaggerUI acts as OAuh2 client)
 *
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Configuration
@EnableSwagger2
@Profile("auth")
public class SwaggerConfigAuth {

    @Autowired
    private OAuth2ClientProperties properties;

    @Bean
    public Docket api() {
        return new Docket(DocumentationType.SWAGGER_2)
                .select()
                .apis(RequestHandlerSelectors.basePackage("uk.ac.ebi.tsc.tesk.tes.api"))
                .apis(RequestHandlerSelectors.withClassAnnotation(RequestMapping.class))
                .paths(PathSelectors.any())
                .build()
                .securitySchemes(Collections.singletonList(oauth()))
                .securityContexts(Arrays.asList(securityContext()));
    }

    @Bean
    protected List<GrantType> grantTypes() {
        List<GrantType> grantTypes = new ArrayList<>();
        if (Boolean.TRUE.equals(properties.getImplicit())) {
            LoginEndpoint loginEndpoint = new LoginEndpoint(properties.getAuthorizationEndpoint());
            grantTypes.add(new ImplicitGrant(loginEndpoint, "access_token"));
        } else {
            TokenRequestEndpoint tokenRequestEndpoint = new TokenRequestEndpoint(properties.getAuthorizationEndpoint(), properties.getClientId(), properties.getClientSecret());
            TokenEndpoint tokenEndpoint = new TokenEndpoint(properties.getTokenEndpoint(), "access_token");
            grantTypes.add(new AuthorizationCodeGrant(tokenRequestEndpoint, tokenEndpoint));
        }
        return grantTypes;
    }

    private SecurityContext securityContext() {
        return SecurityContext.builder()
                .securityReferences(defaultAuth())
                .forPaths(PathSelectors.any())
                .build();
    }

    private List<SecurityReference> defaultAuth() {
        AuthorizationScope authorizationScope = new AuthorizationScope("global", "accessEverything");
        AuthorizationScope[] authorizationScopes = new AuthorizationScope[1];
        authorizationScopes[0] = authorizationScope;
        return Arrays.asList(new SecurityReference("oauth2", authorizationScopes));
    }

    @Bean
    SecurityScheme oauth() {
        return new OAuthBuilder()
                .name("oauth2")
                .scopes(scopes())
                .grantTypes(grantTypes())
                .build();
    }

    private List<AuthorizationScope> scopes() {
        List<AuthorizationScope> list = new ArrayList<>();
        properties.getScopesAsMap().forEach((name, description) -> list.add(new AuthorizationScope(name, description)));
        return list;
    }

    @Bean
    public SecurityConfiguration securityInfo() {
        return SecurityConfigurationBuilder.builder()
                .clientId(properties.getClientId())
                .clientSecret(properties.getClientSecret())
                .scopeSeparator("")
                .build();
    }

}
