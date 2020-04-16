package uk.ac.ebi.tsc.tesk.config.security;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Map;

import org.springframework.boot.autoconfigure.security.oauth2.resource.AuthoritiesExtractor;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.util.ObjectUtils;
import org.springframework.util.StringUtils;
import org.springframework.boot.autoconfigure.security.oauth2.resource.FixedAuthoritiesExtractor;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Custom authorities extractor, that looks for groups element and transforms it into authorities.
 * Heavily inspired by {@link FixedAuthoritiesExtractor)
 */
public class GroupNamesSecurityExtractor implements AuthoritiesExtractor {

    public GroupNamesSecurityExtractor(String authoritiesClaim, String groupPrefix) {
        this.authoritiesClaim = authoritiesClaim;
        this.groupPrefix = groupPrefix;
    }
    private final String authoritiesClaim;
    private final String groupPrefix;

    @Override
    public List<GrantedAuthority> extractAuthorities(Map<String, Object> map) {
        String authorities = this.groupPrefix + ":USER";
        if (map.containsKey(this.authoritiesClaim)) {
            authorities = asAuthorities(map.get(this.authoritiesClaim));
        }
        return AuthorityUtils.commaSeparatedStringToAuthorityList(authorities);
    }

    private String asAuthorities(Object object) {
        List<Object> authorities = new ArrayList<>();
        if (object instanceof Collection) {
            Collection<?> collection = (Collection<?>) object;
            object = collection.toArray(new Object[0]);
        }
        if (ObjectUtils.isArray(object)) {
            Object[] array = (Object[]) object;
            for (Object value : array) {
                if (value instanceof String) {
                    authorities.add(value);
                } else {
                    authorities.add(value);
                }
            }
        } else {
            authorities.add(object);
        }
        return StringUtils.collectionToCommaDelimitedString(authorities);

    }

}
