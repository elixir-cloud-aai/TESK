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
     * Delimiter of nested group names (:)
     */
    private String delimiter;
    /**
     * Top level group name (all groups will have be direct or indirect subgroups of the group)
     */
    private String parentGroup;
    /**
     * Environment subgroup name - subgroup of base group representing single installation of TESK (EBI, CSC)
     */
    private String envSubgroup;

    /**
     * Basic group required to perform any operation (parentGroup + envSubgroup)
     */
    private String baseGroup;
    /**
     * Base group name + delimiter (to use as a prefix to even more nested groups)
     */
    private String baseGroupPrefix;
    /**
     * Subgroup representing admins of its parent group
     */
    private String adminSubgroup;

    /**
     * Group representing admins of single installation of TESK
     */
    private String adminGroup;

    public String getDelimiter() {
        return delimiter;
    }

    public void setDelimiter(String delimiter) {
        this.delimiter = delimiter;
    }

    public String getParentGroup() {
        return parentGroup;
    }

    public void setParentGroup(String parentGroup) {
        this.parentGroup = parentGroup;
    }

    public String getEnvSubgroup() {
        return envSubgroup;
    }

    public void setEnvSubgroup(String envSubgroup) {
        this.envSubgroup = envSubgroup;
    }

    public String getBaseGroup() {
        return baseGroup;
    }

    public void setBaseGroup(String baseGroup) {
        this.baseGroup = baseGroup;
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

    public String getAdminGroup() {
        return adminGroup;
    }

    public void setAdminGroup(String adminGroup) {
        this.adminGroup = adminGroup;
    }
}
