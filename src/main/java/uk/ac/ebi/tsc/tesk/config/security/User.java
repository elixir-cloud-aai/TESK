package uk.ac.ebi.tsc.tesk.config.security;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.util.StringUtils;

import java.io.Serializable;
import java.security.Principal;
import java.util.Collection;
import java.util.HashSet;
import java.util.Set;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * POJO for auhenticated user's data
 */

public class User implements Serializable, UserDetails, Principal {

    private static final long serialVersionUID = 1L;

    private String userId;
    private String preferredUsername;
    private String name;
    private String givenName;
    private String familyName;
    private String email;
    private Set<String> groups;

    public User() {
    }

    public String getUserId() {
        return userId;
    }

    public String getPreferredUsername() {
        return preferredUsername;
    }

    public String getName() {
        return name;
    }

    public String getGivenName() {
        return givenName;
    }

    public String getFamilyName() {
        return familyName;
    }

    public String getEmail() {
        return email;
    }

    public Set<String> getGroups() {
        return groups;
    }

    User(String userId, String preferredUsername, String name, String givenName, String familyName, String email, Set<String> groups) {
        this.userId = userId;
        this.preferredUsername = preferredUsername;
        this.name = name;
        this.givenName = givenName;
        this.familyName = familyName;
        this.email = email;
        this.groups = groups;

    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return AuthorityUtils.createAuthorityList(StringUtils.collectionToCommaDelimitedString(this.groups));
    }

    @Override
    public String getPassword() {
        return null;
    }

    @Override
    public String getUsername() {
        return userId;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return true;
    }

    public static User.UserBuilder builder(String userId) {
        return new User.UserBuilder(userId);
    }

    @Override
    public String toString() {
        return "User{" +
                "userId='" + userId + '\'' +
                ", preferredUsername='" + preferredUsername + '\'' +
                ", name='" + name + '\'' +
                ", givenName='" + givenName + '\'' +
                ", familyName='" + familyName + '\'' +
                ", email='" + email + '\'' +
                ", groups=(" + StringUtils.collectionToCommaDelimitedString(groups) +
                ")}";
    }

    public static class UserBuilder {
        private String userId;
        private String preferredUsername;
        private String name;
        private String givenName;
        private String familyName;
        private String email;
        private Set<String> groups;

        UserBuilder(String userId) {
            this.userId = userId;
        }


        public UserBuilder preferredUsername(String preferredUsername) {
            this.preferredUsername = preferredUsername;
            return this;
        }

        public UserBuilder name(String name) {
            this.name = name;
            return this;
        }

        public UserBuilder givenName(String givenName) {
            this.givenName = givenName;
            return this;
        }

        public UserBuilder familyName(String familyName) {
            this.familyName = familyName;
            return this;
        }

        public UserBuilder email(String email) {
            this.email = email;
            return this;
        }

        public UserBuilder groups(Collection<String> groups) {
            this.groups = new HashSet<>();
            this.groups.addAll(groups);
            return this;
        }

        public User build() {
            return new User(userId, preferredUsername, name, givenName, familyName, email, groups);
        }
    }

}


