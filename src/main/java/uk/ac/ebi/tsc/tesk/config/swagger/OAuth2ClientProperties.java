package uk.ac.ebi.tsc.tesk.config.swagger;

import org.apache.commons.lang.StringUtils;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * Properties for SwaggerUI acting as OAuth2 client
 */
@Configuration
@ConfigurationProperties(prefix = "tesk.api.swagger-oauth")
public class OAuth2ClientProperties {
    /**
     * Authorisation server authorisation endpoint
     */
    private String authorizationEndpoint;

    /**
     * Authorisation server token endpoint
     */
    private String tokenEndpoint;
    /**
     * OAuth2 Client ID
     */
    private String clientId;

    /**
     * OAuth2 Client Secret
     */
    private String clientSecret;

    /**
     * List of Scopes, a client will request (a list of entries: scope name: description)
     */
    private List<String> scopes;
    /**
     * Whether implicit (true) or auth code flow (false)
     */
    private Boolean implicit;


    public String getAuthorizationEndpoint() {
        return authorizationEndpoint;
    }

    public void setAuthorizationEndpoint(String authorizationEndpoint) {
        this.authorizationEndpoint = authorizationEndpoint;
    }

    public String getTokenEndpoint() {
        return tokenEndpoint;
    }

    public void setTokenEndpoint(String tokenEndpoint) {
        this.tokenEndpoint = tokenEndpoint;
    }

    public String getClientId() {
        return clientId;
    }

    public void setClientId(String clientId) {
        this.clientId = clientId;
    }

    public String getClientSecret() {
        return clientSecret;
    }

    public void setClientSecret(String clientSecret) {
        this.clientSecret = clientSecret;
    }

    public List<String> getScopes() {
        return scopes;
    }
    public Map<String, String> getScopesAsMap() {
        Map<String, String> map = new LinkedHashMap<>();
        if (scopes == null)
            return map;
        for (String scope: scopes) {
            String[] pair = StringUtils.split(scope, ":");
            map.put(pair[0], pair[1]);
        }
        return map;
    }

    public void setScopes(List<String> scopes) {
        this.scopes = scopes;
    }

    public Boolean getImplicit() {
        return implicit;
    }

    public void setImplicit(Boolean implicit) {
        this.implicit = implicit;
    }
}
