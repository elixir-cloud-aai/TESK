package uk.ac.ebi.tsc.tesk.config.security;


import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.http.HttpMessageConverters;
import org.springframework.boot.autoconfigure.security.oauth2.resource.AuthoritiesExtractor;
import org.springframework.boot.autoconfigure.security.oauth2.resource.PrincipalExtractor;
import org.springframework.boot.web.servlet.error.ErrorAttributes;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.access.expression.SecurityExpressionHandler;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.core.GrantedAuthorityDefaults;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.oauth2.config.annotation.web.configuration.EnableResourceServer;
import org.springframework.security.oauth2.config.annotation.web.configuration.ResourceServerConfigurerAdapter;
import org.springframework.security.oauth2.config.annotation.web.configurers.ResourceServerSecurityConfigurer;
import org.springframework.security.oauth2.provider.expression.OAuth2WebSecurityExpressionHandler;
import org.springframework.security.web.FilterInvocation;
import org.springframework.util.ObjectUtils;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * This class (specifically the @EnableResourceServer annotation)
 * + 2 dependencies: spring-boot-starter-security + spring-security-oauth2-autoconfigure
 * + security.oauth2.resource.user-info-uri property (which points to user info endpoint of the authorisation server)
 * switch on protection of (all minus Swagger) the endpoints via OAuth2 token
 */
@Configuration
@EnableResourceServer
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class ResourceServerConfiguration extends ResourceServerConfigurerAdapter {


    private final ErrorAttributes errorAttributes;
    private final HttpMessageConverters messageConverters;

    public ResourceServerConfiguration(ErrorAttributes errorAttributes, HttpMessageConverters messageConverters) {
        this.errorAttributes = errorAttributes;
        this.messageConverters = messageConverters;
    }


    /**
     * We leave the sensible defaults only letting swagger UI requests in
     */
    @Override
    public void configure(HttpSecurity http) throws Exception {
        http
                .authorizeRequests()
                .antMatchers(HttpMethod.GET, "/", "/v2/api-docs", "/configuration/ui", "/swagger-resources/**", "/configuration/**", "/swagger-ui.html", "/webjars/**").permitAll()
                .anyRequest().authenticated();
    }

    /**
     * Sets a custom entryPoint that returns json in our usual error format with the use of standard Boot's errorAttributes and
     * autoconfigured messageConverters (specifically with autoconfigured objectMapper for JacksonConverter)
     */
    @Override
    public void configure(ResourceServerSecurityConfigurer resources) {
        resources.authenticationEntryPoint(new CustomAuthenticationEntryPoint(errorAttributes, messageConverters));
    }

    /**
     * Magic, that changes default role prefix from ROLE_ to elixir:
     *
     */
    @Bean
    public GrantedAuthorityDefaults grantedAuthorityDefaults() {
        return new GrantedAuthorityDefaults("elixir:");
    }

    /**
     * Custom authorities extractor (we use Elixir roles as authorities)
     *
     */
    @Bean
    public AuthoritiesExtractor authoritiesExtractor() {
        return new GroupNamesSecurityExtractor();
    }

    /**
     * Custom principal extractor (we use the whole userinfo response object as Principal
     *
     */
    @Bean
    public PrincipalExtractor principalExtractor() {
        return new ElixirPrincipalExtractor(authoritiesExtractor());
    }

}
