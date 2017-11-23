package uk.ac.ebi.tsc.tesk.util;

import io.kubernetes.client.ApiException;
import io.kubernetes.client.apis.BatchV1Api;
import io.kubernetes.client.apis.CoreV1Api;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1JobList;
import io.kubernetes.client.models.V1PodList;
import org.springframework.stereotype.Component;
import uk.ac.ebi.tsc.tesk.exception.KubernetesException;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Component
public class KubernetesClientWrapper {

    private final BatchV1Api batchApi;

    private final CoreV1Api coreApi;

    public KubernetesClientWrapper(BatchV1Api batchApi, CoreV1Api coreApi) {
        this.batchApi = batchApi;
        this.coreApi = coreApi;
    }
    public V1Job createNamespacedJob(String namespace, V1Job job) {
        try {
            return this.batchApi.createNamespacedJob(namespace, job, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }
    public V1Job readNamespacedJob(String taskId, String namespace) {
        try {
            return this.batchApi.readNamespacedJob(taskId, namespace, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }
    public V1JobList listNamespacedJob(String namespace, String labelSelector) {
        try {
            return this.batchApi.listNamespacedJob(namespace, null, null, null, null, labelSelector, null, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }
    public V1PodList listNamespacedPod(String namespace, String labelSelector) {
        try {
            return this.coreApi.listNamespacedPod(namespace, null, null, null, null, labelSelector, null, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }
    public String readNamespacedPodLog(String name, String namespace) {
        try {
            return this.coreApi.readNamespacedPodLog(name, namespace, null, null, null, null, null, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }



}
