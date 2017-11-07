package uk.ac.ebi.tsc.tesk.config;

import io.kubernetes.client.ApiClient;
import io.kubernetes.client.apis.BatchV1Api;
import io.kubernetes.client.util.Config;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.io.IOException;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Configuration
public class KubernetesClientConfig {

    @Bean
    public ApiClient kubernetesApiClient() throws IOException {

        return Config.defaultClient();

    }

    @Bean
    public BatchV1Api batchApi(ApiClient apiClient) {

        return new BatchV1Api(apiClient);

    }
}
