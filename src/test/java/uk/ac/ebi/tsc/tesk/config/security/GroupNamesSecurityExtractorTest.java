package uk.ac.ebi.tsc.tesk.config.security;

import org.junit.Test;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.hamcrest.Matchers.containsInAnyOrder;
import static org.junit.Assert.assertThat;

public class GroupNamesSecurityExtractorTest {

    @Test
    public void extractAuthorities_array() {
        GroupNamesSecurityExtractor extractor = new GroupNamesSecurityExtractor("groupNames", "whatever");
        Map<String, Object> authorities = new HashMap<>();
        authorities.put("groupNames", new String[]{"abc", "xyz"});
        List<GrantedAuthority> result = extractor.extractAuthorities(authorities);
        assertThat(result, containsInAnyOrder(new SimpleGrantedAuthority("abc"), new SimpleGrantedAuthority("xyz")));
    }

    @Test
    public void extractAuthorities_collection() {
        GroupNamesSecurityExtractor extractor = new GroupNamesSecurityExtractor("entitlement", "whatever");
        Map<String, Object> authorities = new HashMap<>();
        authorities.put("entitlement", Arrays.asList("abc", "xyz"));
        List<GrantedAuthority> result = extractor.extractAuthorities(authorities);
        assertThat(result, containsInAnyOrder(new SimpleGrantedAuthority("abc"), new SimpleGrantedAuthority("xyz")));
    }

    @Test
    public void extractAuthorities_noGroups() {
        GroupNamesSecurityExtractor extractor = new GroupNamesSecurityExtractor("groupNames", "prefix");
        Map<String, Object> authorities = new HashMap<>();
        authorities.put("sthElse", new String[]{"abc", "xyz"});
        List<GrantedAuthority> result = extractor.extractAuthorities(authorities);
        assertThat(result, containsInAnyOrder(new SimpleGrantedAuthority("prefix:USER")));
    }
}