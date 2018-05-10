package uk.ac.ebi.tsc.tesk.config.security;

import org.junit.Before;
import org.junit.Test;
import org.springframework.util.StringUtils;

import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;

public class ElixirPrincipalExtractorTest {

    private ElixirPrincipalExtractor extractor;

    @Before
    public void setUp() {
        AuthorisationProperties properties = new AuthorisationProperties();
        properties.setBaseGroupPrefix("BASE_GROUP:");
        properties.setAdminSubgroup("ADMIN");
        properties.setAdminGroup("BASE_GROUP:ADMIN");
        extractor = new ElixirPrincipalExtractor(new GroupNamesSecurityExtractor(), properties);
    }

    @Test
    public void extractPrincipal() {
        User modelUser = User.builder("123").preferredUsername("user_123").email("jodo@yahoo.com")
                .name("Jo Do").givenName("Jo").familyName("Do").teskAdmin(false)
                .teskMemberedGroups(new HashSet<>()).teskManagedGroups(new HashSet<>()).allGroups(StringUtils.commaDelimitedListToSet("elixir:USER")).build();
        Map<String, Object> map = new HashMap<>();
        map.put("sub", "123");
        map.put("preferred_username", "user_123");
        map.put("name", "Jo Do");
        map.put("given_name", "Jo");
        map.put("family_name", "Do");
        map.put("email", "jodo@yahoo.com");
        Object result = extractor.extractPrincipal(map);
        User user = (User) result;
        assertThat(user, is(modelUser));
    }

    @Test
    public void extractPrincipalWithGroups() {
        User modelUser = User.builder("123").teskAdmin(true)
                .teskMemberedGroups(StringUtils.commaDelimitedListToSet("TEST,ABC")).teskManagedGroups(StringUtils.commaDelimitedListToSet("XYZ"))
                .allGroups(StringUtils.commaDelimitedListToSet("OTHER,BASE_GROUP:ADMIN,BASE_GROUP:TEST,BASE_GROUP:ABC,BASE_GROUP:XYZ:ADMIN")).build();
        Map<String, Object> map = new HashMap<>();
        map.put("sub", "123");
        map.put("groupNames", Arrays.asList("OTHER", "BASE_GROUP:ADMIN", "BASE_GROUP:TEST", "BASE_GROUP:ABC", "BASE_GROUP:XYZ:ADMIN"));
        Object result = extractor.extractPrincipal(map);
        User user = (User) result;
        assertThat(user, is(modelUser));
    }
}