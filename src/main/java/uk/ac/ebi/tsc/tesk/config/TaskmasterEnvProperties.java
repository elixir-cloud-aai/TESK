package uk.ac.ebi.tsc.tesk.config;

import org.apache.commons.lang.StringUtils;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * Properties affecting taskmaster's job template
 */
@Configuration
@ConfigurationProperties(prefix = "tesk.api.taskmaster")
public class TaskmasterEnvProperties {
    /**
     * Taskmaster image name
     */
    private String imageName;
    /**
     * Taskmaster image version
     */
    private String imageVersion;
    /**
     * Test FTP account settings
     */
    private Ftp ftp;

    /**
     * Service Account name for taskmaster
     */
    private String serviceAccountName;


    public Ftp getFtp() {
        return ftp;
    }

    public void setFtp(Ftp ftp) {
        this.ftp = ftp;
    }

    public String getImageName() {
        return imageName;
    }

    public void setImageName(String imageName) {
        this.imageName = imageName;
    }

    public String getImageVersion() {
        return imageVersion;
    }

    public void setImageVersion(String imageVersion) {
        this.imageVersion = imageVersion;
    }

    public String getServiceAccountName() {
        return serviceAccountName;
    }

    public void setServiceAccountName(String serviceAccountName) {
        this.serviceAccountName = serviceAccountName;
    }

    /**
     * Test FTP account settings
     */
    public static class Ftp {
        /**
         * Name of the secret with FTP acoount credentials
         */
        private String secretName;
        /**
         * If FTP account enabled (based on non-emptiness of secretName)
         * Does not check the existence of real secret via API
         */
        private boolean enabled;

        public String getSecretName() {
            return secretName;
        }

        public void setSecretName(String secretName)
        {
            this.secretName = secretName;
            if (!StringUtils.isEmpty(this.secretName)) {
                this.enabled = true;
            }
        }

        public boolean isEnabled() {
            return enabled;
        }


    }
}
