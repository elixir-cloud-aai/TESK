package uk.ac.ebi.tsc.tesk.config.security;

import org.springframework.boot.autoconfigure.security.oauth2.resource.AuthoritiesExtractor;
import org.springframework.boot.autoconfigure.security.oauth2.resource.PrincipalExtractor;
import org.springframework.security.core.GrantedAuthority;

import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;


/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * Custom principal extractor (puts all of the info from userinfo to custom {@link User} object)
 */
public class ElixirPrincipalExtractor implements PrincipalExtractor {

    ElixirPrincipalExtractor(AuthoritiesExtractor groupsExtractor) {
        this.groupsExtractor = groupsExtractor;
    }
    private AuthoritiesExtractor groupsExtractor;

    @Override
    public Object extractPrincipal(Map<String, Object> map) {
        return User.builder(map.get("sub").toString())
                .preferredUsername(Optional.ofNullable(map.get("preferred_username")).map(Object::toString).orElse(null))
                .name(Optional.ofNullable(map.get("name")).map(Object::toString).orElse(null))
                .email(Optional.ofNullable(map.get("email")).map(Object::toString).orElse(null))
                .givenName(Optional.ofNullable(map.get("given_name")).map(Object::toString).orElse(null))
                .familyName(Optional.ofNullable(map.get("family_name")).map(Object::toString).orElse(null))
                .groups(this.groupsExtractor.extractAuthorities(map).stream().map(GrantedAuthority::getAuthority).collect(Collectors.toSet()))
                .build();
    }
}
