package uk.ac.ebi.tsc.tesk.k8s.config;

import io.kubernetes.client.ApiClient;
import io.kubernetes.client.apis.BatchV1Api;
import io.kubernetes.client.apis.CoreV1Api;
import io.kubernetes.client.auth.ApiKeyAuth;
import io.kubernetes.client.util.Config;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import java.io.IOException;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Configuration
public class KubernetesClientConfig {

    @Bean
    @Primary
    public ApiClient kubernetesApiClient() throws IOException {

        return Config.defaultClient();

    }

    @Bean
    @Primary
    public BatchV1Api batchApi(ApiClient apiClient) {

        return new BatchV1Api(apiClient);

    }

    @Bean
    @Primary
    public CoreV1Api coreApi(ApiClient apiClient) {

        return new CoreV1Api(apiClient);

    }

    /**
     * Workaround to enable merge patching (Kube client does JSON patch only - headers hardcoded)
     * Separate instance of ApiClient only for running PATCH calls
     */
    @Bean(name = "patchApiClient")
    public ApiClient patchApiClient() throws IOException {

        ApiClient defaultClient = Config.defaultClient();
        return new ApiClientWithMergePatching(defaultClient);

    }

    /**
     * Separate object to perform merge-patching of Jobs
     */
    @Bean(name = "patchBatchApi")
    public BatchV1Api patchBatchApi(@Qualifier("patchApiClient") ApiClient patchApiClient) {

        return new BatchV1Api(patchApiClient);

    }

    /**
     * Separate object to perform merge-patching of JPods
     */
    @Bean(name = "patchCoreApi")
    public CoreV1Api patchCoreApi(@Qualifier("patchApiClient") ApiClient patchApiClient) {

        return new CoreV1Api(patchApiClient);

    }

    /**
     * This client should in theory work exactly as the original one, just always use application/merge-patch header
     * Accepts auto-configured instance as parameter of a constructor and - hopefully - initializes accordingly
     */
    private static class ApiClientWithMergePatching extends ApiClient {

        ApiClientWithMergePatching(ApiClient apiClient) {
            this.setBasePath(apiClient.getBasePath());
            this.setHttpClient(apiClient.getHttpClient());
            this.setApiKey(((ApiKeyAuth) apiClient.getAuthentication("BearerToken")).getApiKey());
        }

        @Override
        public String selectHeaderContentType(String[] contentTypes) {
            return "application/merge-patch+json";
        }
    }

}
