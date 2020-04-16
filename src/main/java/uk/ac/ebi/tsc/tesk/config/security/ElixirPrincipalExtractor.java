package uk.ac.ebi.tsc.tesk.config.security;

import org.springframework.boot.autoconfigure.security.oauth2.resource.AuthoritiesExtractor;
import org.springframework.boot.autoconfigure.security.oauth2.resource.PrincipalExtractor;
import org.springframework.security.core.GrantedAuthority;

import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;


/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Custom principal extractor (puts all of the info from userinfo to custom {@link User} object)
 */
public class ElixirPrincipalExtractor implements PrincipalExtractor {

    private final AuthoritiesExtractor groupsExtractor;
    private final AuthorisationProperties authorisationProperties;
    private final Pattern MEMBERED_GROUP;
    private final Pattern MANAGED_GROUP;

    ElixirPrincipalExtractor(AuthoritiesExtractor groupsExtractor, AuthorisationProperties authorisationProperties) {
        this.groupsExtractor = groupsExtractor;
        this.authorisationProperties = authorisationProperties;
        MEMBERED_GROUP = Pattern.compile("^" + authorisationProperties.getBaseGroupPrefix() + "([^:]+)" + authorisationProperties.getGroupSuffix());
        MANAGED_GROUP = Pattern.compile("^" + authorisationProperties.getBaseGroupPrefix() + "([^:]+):" + authorisationProperties.getAdminSubgroup() + authorisationProperties.getGroupSuffix());
    }


    @Override
    public Object extractPrincipal(Map<String, Object> map) {
        User.UserBuilder builder = User.builder(map.get("sub").toString())
                .preferredUsername(Optional.ofNullable(map.get("preferred_username")).map(Object::toString).orElse(null))
                .name(Optional.ofNullable(map.get("name")).map(Object::toString).orElse(null))
                .email(Optional.ofNullable(map.get("email")).map(Object::toString).orElse(null))
                .givenName(Optional.ofNullable(map.get("given_name")).map(Object::toString).orElse(null))
                .familyName(Optional.ofNullable(map.get("family_name")).map(Object::toString).orElse(null));

        Set<String> allGroups = this.groupsExtractor.extractAuthorities(map).stream().map(GrantedAuthority::getAuthority).collect(Collectors.toSet());
        Set<String> memberedGroups = allGroups.stream().filter(name -> MEMBERED_GROUP.matcher(name).matches() && !authorisationProperties.getAdminGroupFull().equals(name)).
                map(name -> {
                    Matcher matcher = MEMBERED_GROUP.matcher(name);
                    matcher.matches();
                    return matcher.group(1);
                }).collect(Collectors.toSet());
        Set<String> managedGroups = allGroups.stream().filter(name -> MANAGED_GROUP.matcher(name).matches() && !authorisationProperties.getAdminGroupFull().equals(name)).
                map(name -> {
                    Matcher matcher = MANAGED_GROUP.matcher(name);
                    matcher.matches();
                    return matcher.group(1);
                }).collect(Collectors.toSet());
        boolean isAdmin = allGroups.stream().anyMatch(name -> authorisationProperties.getAdminGroupFull().equals(name));
        return builder.allGroups(allGroups).teskMemberedGroups(memberedGroups).teskManagedGroups(managedGroups).teskAdmin(isAdmin).build();
    }
}
