package uk.ac.ebi.tsc.tesk.config.security;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.util.StringUtils;
import uk.ac.ebi.tsc.tesk.util.constant.Constants;

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
    /**
     * Full list of elixir group full names, to which the user belongs
     */
    private Set<String> allGroups;
    /**
     * Is the user a TESK installation admin (belongs to a group with that meaning)
     */
    private boolean teskAdmin = false;

    /**
     * List of 'organisational' groups, to which the user belongs (last part of Elixir group names only
     * (see {@link ElixirPrincipalExtractor} to see, how that information is retrieved from allGroups)
     * TES task will be 'owned' by one of the groups, to which the creating user belongs (or by no group, if the user does not belong to any)
     */
    private Set<String> teskMemberedGroups;

    /**
     * List of 'organisational' groups, where the user is an admin (see {@link ElixirPrincipalExtractor} to see, how that information is retrieved from allGroups)
     * TES task will be 'owned' by one of the groups, to which the creating user belongs (or by no group, if the user does not belong to any)
     */
    private Set<String> teskManagedGroups;

    public User() {
    }

    public String getName() {
        return name;
    }

    public boolean isTeskAdmin() {
        return teskAdmin;
    }

    public boolean isGroupMember(String groupName) {
        return teskMemberedGroups != null && teskMemberedGroups.contains(groupName);
    }

    public boolean isMember() {
        return teskMemberedGroups != null && teskMemberedGroups.size() > 0;
    }

    public String getAnyGroup() {
        if (!isMember())
            return null;
        return teskMemberedGroups.iterator().next();
    }

    public boolean isGroupManager(String groupName) {
        return teskManagedGroups != null && teskManagedGroups.contains(groupName);
    }

    public boolean isManager() {
        return teskManagedGroups != null && teskManagedGroups.size() > 0;
    }

    public boolean isMemberInNonManagedGroups() {
        if (!isTeskAdmin() && isMember() && isManager()) {
            Set<String> difference = new HashSet<>();
            difference.addAll(this.teskMemberedGroups);
            difference.removeAll(this.teskManagedGroups);
            return difference.size() > 0;
        }
        return false;
    }

    public String getLabelSelector() {
        Set<String> allTeskGroups = new HashSet<>();
        if (this.teskMemberedGroups != null) {
            allTeskGroups.addAll(this.teskMemberedGroups);
        }
        if (this.teskManagedGroups != null) {
            allTeskGroups.addAll(this.teskManagedGroups);
        }
        if (isTeskAdmin()) {
            return null;
        }
        if (isMember() || isManager()) {
            StringBuilder sb = new StringBuilder();
            sb.append(Constants.LABEL_GROUPNAME_KEY).append(" in (").append(StringUtils.collectionToCommaDelimitedString(allTeskGroups)).append(")");
            if (!isManager()) {
                sb.append(",").append(Constants.LABEL_USERID_KEY).append("=").append(getUsername());
            }
            return sb.toString();
        }
        return null;
    }

    User(String userId, String preferredUsername, String name, String givenName, String familyName, String email,
         Set<String> allGroups, Set<String> teskMemberedGroups, Set<String> teskManagedGroups, boolean teskAdmin) {
        this.userId = userId;
        this.preferredUsername = preferredUsername;
        this.name = name;
        this.givenName = givenName;
        this.familyName = familyName;
        this.email = email;
        this.allGroups = allGroups;
        this.teskMemberedGroups = teskMemberedGroups;
        this.teskManagedGroups = teskManagedGroups;
        this.teskAdmin = teskAdmin;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return AuthorityUtils.createAuthorityList(StringUtils.collectionToCommaDelimitedString(this.allGroups));
    }

    @Override
    public String getPassword() {
        return null;
    }

    @Override
    public String getUsername() {
        return userId.replaceAll("@", "_");
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
                ", allGroups=(" + StringUtils.collectionToCommaDelimitedString(allGroups) +
                ")}";
    }

    public static class UserBuilder {
        private String userId;
        private String preferredUsername;
        private String name;
        private String givenName;
        private String familyName;
        private String email;
        private Set<String> allGroups;
        private Set<String> teskMemberedGroups;
        private Set<String> teskManagedGroups;
        private boolean teskAdmin = false;

        UserBuilder(String userId) {
            this.userId = userId;
            this.teskMemberedGroups = new HashSet<>();
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

        public UserBuilder allGroups(Collection<String> allGroups) {
            this.allGroups = new HashSet<>();
            this.allGroups.addAll(allGroups);
            return this;
        }

        public UserBuilder teskMemberedGroups(Collection<String> teskMemberedGroups) {
            this.teskMemberedGroups = new HashSet<>();
            this.teskMemberedGroups.addAll(teskMemberedGroups);
            return this;
        }

        public UserBuilder teskManagedGroups(Collection<String> teskManagedGroups) {
            this.teskManagedGroups = new HashSet<>();
            this.teskManagedGroups.addAll(teskManagedGroups);
            return this;
        }

        public UserBuilder teskAdmin(boolean teskAdmin) {
            this.teskAdmin = teskAdmin;
            return this;
        }

        public User build() {
            return new User(userId, preferredUsername, name, givenName, familyName, email,
                    allGroups, teskMemberedGroups, teskManagedGroups, teskAdmin);
        }
    }

}


