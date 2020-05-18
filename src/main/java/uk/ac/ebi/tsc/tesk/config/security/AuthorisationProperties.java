package uk.ac.ebi.tsc.tesk.config.security;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Configuration of group based authorisation
 */
@Configuration
@ConfigurationProperties(prefix = "tesk.api.authorisation")
public class AuthorisationProperties {
    /**
     * The name of the claim in userInfo that contains user's group membership
     */
    private String groupsClaim;

    /**
     * The prefix before actual group name
     */
    private String groupPrefix;
    /**
     * The suffix after actual group name
     */
    private String groupSuffix = "";

    /**
     * Full name of base group required to perform any operation (prefix + parentGroup + envSubgroup + suffix)
     */
    private String baseGroupFull;
    /**
     * (Prefix) + Base group name + delimiter (to use as a prefix to even more nested groups)
     */
    private String baseGroupPrefix;
    /**
     * Subgroup representing admins of its parent group
     */
    private String adminSubgroup;

    /**
     * Full name of a group representing admins of a single installation of TESK
     */
    private String adminGroupFull;

    public String getGroupsClaim() {
        return groupsClaim;
    }

    public void setGroupsClaim(String groupsClaim) {
        this.groupsClaim = groupsClaim;
    }

    public String getGroupPrefix() {
        return groupPrefix;
    }

    public void setGroupPrefix(String groupPrefix) {
        this.groupPrefix = groupPrefix;
    }

    public String getGroupSuffix() {
        return groupSuffix;
    }

    public void setGroupSuffix(String groupSuffix) {
        this.groupSuffix = groupSuffix;
    }

    public String getBaseGroupFull() {
        return baseGroupFull;
    }

    public void setBaseGroupFull(String baseGroupFull) {
        this.baseGroupFull = baseGroupFull;
    }

    public String getAdminSubgroup() {
        return adminSubgroup;
    }

    public void setAdminSubgroup(String adminSubgroup) {
        this.adminSubgroup = adminSubgroup;
    }

    public String getBaseGroupPrefix() {
        return baseGroupPrefix;
    }

    public void setBaseGroupPrefix(String baseGroupPrefix) {
        this.baseGroupPrefix = baseGroupPrefix;
    }

    public String getAdminGroupFull() {
        return adminGroupFull;
    }

    public void setAdminGroupFull(String adminGroupFull) {
        this.adminGroupFull = adminGroupFull;
    }
}
