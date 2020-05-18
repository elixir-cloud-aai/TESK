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

    private ElixirPrincipalExtractor extractorNoSuffix;
    private ElixirPrincipalExtractor extractorSuffix;

    @Before
    public void setUp() {
        AuthorisationProperties properties = new AuthorisationProperties();
        properties.setBaseGroupPrefix("BASE_GROUP:");
        properties.setAdminSubgroup("ADMIN");
        properties.setAdminGroupFull("BASE_GROUP:ADMIN");
        extractorNoSuffix = new ElixirPrincipalExtractor(new GroupNamesSecurityExtractor("groupNames", "whatever"), properties);
        AuthorisationProperties propertiesSuffix = new AuthorisationProperties();
        propertiesSuffix.setBaseGroupPrefix("prefix:BASE_GROUP:");
        propertiesSuffix.setAdminSubgroup("ADMIN");
        propertiesSuffix.setAdminGroupFull("prefix:BASE_GROUP:ADMIN#suffix");
        propertiesSuffix.setGroupSuffix("#suffix");
        extractorNoSuffix = new ElixirPrincipalExtractor(new GroupNamesSecurityExtractor("groupNames", "whatever"), properties);
        extractorSuffix = new ElixirPrincipalExtractor(new GroupNamesSecurityExtractor("groupNames", "whatever"), propertiesSuffix);
    }

    @Test
    public void extractPrincipal() {
        User modelUser = User.builder("123").preferredUsername("user_123").email("jodo@yahoo.com")
                .name("Jo Do").givenName("Jo").familyName("Do").teskAdmin(false)
                .teskMemberedGroups(new HashSet<>()).teskManagedGroups(new HashSet<>()).allGroups(StringUtils.commaDelimitedListToSet("whatever:USER")).build();
        Map<String, Object> map = new HashMap<>();
        map.put("sub", "123");
        map.put("preferred_username", "user_123");
        map.put("name", "Jo Do");
        map.put("given_name", "Jo");
        map.put("family_name", "Do");
        map.put("email", "jodo@yahoo.com");
        Object result1 = extractorNoSuffix.extractPrincipal(map);
        Object result2 = extractorSuffix.extractPrincipal(map);
        User user1 = (User) result1;
        User user2 = (User) result2;
        assertThat(user1, is(modelUser));
        assertThat(user2, is(modelUser));
    }

    @Test
    public void extractPrincipalWithGroups() {
        User modelUser = User.builder("123").teskAdmin(true)
                .teskMemberedGroups(StringUtils.commaDelimitedListToSet("TEST,ABC")).teskManagedGroups(StringUtils.commaDelimitedListToSet("XYZ"))
                .allGroups(StringUtils.commaDelimitedListToSet("OTHER,BASE_GROUP:ADMIN,BASE_GROUP:TEST,BASE_GROUP:ABC,BASE_GROUP:XYZ:ADMIN")).build();
        Map<String, Object> map = new HashMap<>();
        map.put("sub", "123");
        map.put("groupNames", Arrays.asList("OTHER", "BASE_GROUP:ADMIN", "BASE_GROUP:TEST", "BASE_GROUP:ABC", "BASE_GROUP:XYZ:ADMIN"));
        Object result = extractorNoSuffix.extractPrincipal(map);
        User user = (User) result;
        assertThat(user, is(modelUser));
    }
    @Test
    public void extractPrincipalWithGroupsSuffixes() {
        User modelUser = User.builder("123").teskAdmin(true)
                .teskMemberedGroups(StringUtils.commaDelimitedListToSet("TEST,ABC")).teskManagedGroups(StringUtils.commaDelimitedListToSet("XYZ"))
                .allGroups(StringUtils.commaDelimitedListToSet("prefix:OTHER#suffix,prefix:BASE_GROUP:ADMIN#suffix,prefix:BASE_GROUP:TEST#suffix,prefix:BASE_GROUP:ABC#suffix,prefix:BASE_GROUP:XYZ:ADMIN#suffix")).build();
        Map<String, Object> map = new HashMap<>();
        map.put("sub", "123");
        map.put("groupNames", Arrays.asList("prefix:OTHER#suffix", "prefix:BASE_GROUP:ADMIN#suffix", "prefix:BASE_GROUP:TEST#suffix", "prefix:BASE_GROUP:ABC#suffix", "prefix:BASE_GROUP:XYZ:ADMIN#suffix"));
        Object result = extractorSuffix.extractPrincipal(map);
        User user = (User) result;
        assertThat(user, is(modelUser));
    }
}