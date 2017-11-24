package uk.ac.ebi.tsc.tesk.util;

import io.kubernetes.client.ApiException;
import io.kubernetes.client.apis.BatchV1Api;
import io.kubernetes.client.apis.CoreV1Api;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1JobList;
import io.kubernetes.client.models.V1PodList;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import uk.ac.ebi.tsc.tesk.exception.KubernetesException;
import uk.ac.ebi.tsc.tesk.exception.TaskNotFoundException;

import java.util.StringJoiner;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.util.KubernetesConstants.*;

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

    public V1Job createJob(V1Job job) {
        try {
            return this.batchApi.createNamespacedJob(DEFAULT_NAMESPACE, job, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

    public V1Job readTaskmasterJob(String taskId) {
        try {
            V1Job job = this.batchApi.readNamespacedJob(taskId, DEFAULT_NAMESPACE, null, null, null);
            if (job.getMetadata().getLabels().entrySet().stream().anyMatch(entry -> LABEL_JOBTYPE_KEY.equals(entry.getKey()) && LABEL_JOBTYPE_VALUE_TASKM.equals(entry.getValue())))
                return job;
        } catch (ApiException e) {
            if (e.getCode() != HttpStatus.NOT_FOUND.value())
                throw KubernetesException.fromApiException(e);
        }
        throw new TaskNotFoundException(taskId);
    }

    public V1JobList listJobs(String _continue, String labelSelector, Integer limit) {
        try {
            return this.batchApi.listNamespacedJob(DEFAULT_NAMESPACE, null, _continue, null, null, labelSelector, limit, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

    public V1JobList listTaskExecutorJobs(String taskId) {
        String labelSelector = new StringJoiner("=").add(LABEL_TESTASK_ID_KEY).add(taskId).toString();
        return this.listJobs(null, labelSelector, null);
    }

    public V1JobList listTaskmasterJobs(String pageToken, Integer itemsPerPage) {
        String labelSelector = new StringJoiner("=").add(LABEL_JOBTYPE_KEY).add(LABEL_JOBTYPE_VALUE_TASKM).toString();
        return this.listJobs(pageToken, labelSelector, itemsPerPage);
    }

    public V1PodList listJobPods(V1Job job) {
        String labelSelector = job.getSpec().getSelector().getMatchLabels().entrySet().stream().map(entry -> entry.getKey() + "=" + entry.getValue()).collect(Collectors.joining(","));
        try {
            return this.coreApi.listNamespacedPod(DEFAULT_NAMESPACE, null, null, null, null, labelSelector, null, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

    public String readPodLog(String podName) {
        try {
            return this.coreApi.readNamespacedPodLog(podName, DEFAULT_NAMESPACE, null, null, null, null, null, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }


}
