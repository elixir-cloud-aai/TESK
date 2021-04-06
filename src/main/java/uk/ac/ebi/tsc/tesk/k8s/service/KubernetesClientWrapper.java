package uk.ac.ebi.tsc.tesk.k8s.service;

import io.kubernetes.client.ApiException;
import io.kubernetes.client.apis.BatchV1Api;
import io.kubernetes.client.apis.CoreV1Api;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1JobList;
import io.kubernetes.client.models.V1PodList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import uk.ac.ebi.tsc.tesk.config.security.User;
import uk.ac.ebi.tsc.tesk.k8s.exception.KubernetesException;
import uk.ac.ebi.tsc.tesk.tes.exception.TaskNotFoundException;

import java.util.List;
import java.util.Optional;
import java.util.StringJoiner;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Component
public class KubernetesClientWrapper {

    private static Logger logger = LoggerFactory.getLogger(KubernetesClientWrapper.class);

    private final BatchV1Api batchApi;

    private final BatchV1Api patchBatchApi;

    private final CoreV1Api coreApi;

    private final CoreV1Api patchCoreApi;

    private final String namespace;

    public KubernetesClientWrapper(BatchV1Api batchApi, @Qualifier("patchBatchApi") BatchV1Api patchBatchApi,
                                   CoreV1Api coreApi, @Qualifier("patchCoreApi") CoreV1Api patchCoreApi,
                                   @Value("${tesk.api.k8s.namespace}") String namespace) {
        this.batchApi = batchApi;
        this.patchBatchApi = patchBatchApi;
        this.coreApi = coreApi;
        this.patchCoreApi = patchCoreApi;
        this.namespace = namespace;
    }

    public V1Job createJob(V1Job job) {
        try {
            return this.batchApi.createNamespacedJob(namespace, job, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

    public V1Job readTaskmasterJob(String taskId) {
        try {
            V1Job job = this.batchApi.readNamespacedJob(taskId, namespace, null, null, null);
            if (job.getMetadata().getLabels().entrySet().stream().anyMatch(entry -> LABEL_JOBTYPE_KEY.equals(entry.getKey()) && LABEL_JOBTYPE_VALUE_TASKM.equals(entry.getValue())))
                return job;
        } catch (ApiException e) {
            if (e.getCode() != HttpStatus.NOT_FOUND.value())
                throw KubernetesException.fromApiException(e);
        }
        throw new TaskNotFoundException(taskId);
    }

    private V1JobList listJobs(String _continue, String labelSelector, Integer limit) {
        try {
            return this.batchApi.listNamespacedJob(namespace, null, _continue, null, null, labelSelector, limit, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

    /**
     * Gets all Taskmaster job objects, a User is allowed to see
     * @param pageToken - pageToken supplied by user (from previous result; points to next page of results)
     * @param itemsPerPage - value submitted by user, limiting number of results
     * @param user - authenticated user
     * @return all Taskmaster job objects, a User is allowed to see in V1JobList
     */
    public V1JobList listAllTaskmasterJobsForUser(String pageToken, Integer itemsPerPage, User user) {
        //Jobs of taskmaster type
        String labelSelector = new StringJoiner("=").add(LABEL_JOBTYPE_KEY).add(LABEL_JOBTYPE_VALUE_TASKM).toString();
        if (user.getLabelSelector() != null) {
            //additional label selectors; limiting results to jobs belonging to chosen groups (where the user is member and/or manager)
            // and optionally also to only those jobs, which were created bu the user
            labelSelector += "," + user.getLabelSelector();
        }
        V1JobList result = this.listJobs(pageToken, labelSelector, itemsPerPage);
        if (user.isMemberInNonManagedGroups()) {
            //if there are groups, where user is a manager and other groups, where user is only a member
            //filter the results (as it was not handled by label selector)
            List<V1Job> filteredJobList = result.getItems();
            filteredJobList = filteredJobList.stream().filter(job ->
                    user.isGroupManager(job.getMetadata().getLabels().get(LABEL_GROUPNAME_KEY))
                            || user.getUsername().equals(job.getMetadata().getLabels().get(LABEL_USERID_KEY))).collect(Collectors.toList());
            result.setItems(filteredJobList);
        }
        return result;
    }

    public V1JobList listSingleTaskExecutorJobs(String taskId) {
        String labelSelector = new StringJoiner("=").add(LABEL_TESTASK_ID_KEY).add(taskId).toString();
        return this.listJobs(null, labelSelector, null);
    }

    public Optional<V1Job> getSingleTaskOutputFilerJob(String taskId) {
        try {
            V1Job job = this.batchApi.readNamespacedJob(taskId + JOB_NAME_FILER_SUF, namespace, null, null, null);
            return Optional.of(job);
        } catch (ApiException e) {
            if (e.getCode() != HttpStatus.NOT_FOUND.value()) {
                throw KubernetesException.fromApiException(e);
            }
        }
        return Optional.empty();
    }

    public V1JobList listAllTaskExecutorJobs() {
        String labelSelector = new StringJoiner("=").add(LABEL_JOBTYPE_KEY).add(LABEL_JOBTYPE_VALUE_EXEC).toString();
        return this.listJobs(null, labelSelector, null);
    }

    public V1JobList listAllFilerJobs() {
        String labelSelector = "!" + LABEL_JOBTYPE_KEY;
        return this.listJobs(null, labelSelector, null);
    }

    public V1PodList listSingleJobPods(V1Job job) {
        String labelSelector = job.getSpec().getSelector().getMatchLabels().entrySet().stream().map(entry -> entry.getKey() + "=" + entry.getValue()).collect(Collectors.joining(","));
        try {
            return this.coreApi.listNamespacedPod(namespace, null, null, null, null, labelSelector, null, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

    public V1PodList listAllJobPods() {
        String labelSelector = "job-name";
        try {
            return this.coreApi.listNamespacedPod(namespace, null, null, null, null, labelSelector, null, null, null, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

    public String readPodLog(String podName) {
        try {
            return this.coreApi.readNamespacedPodLog(podName, namespace, null, null, null, null, null, null, null, null);
        } catch (ApiException e) {
            logger.info("Getting logs for pod " + podName + " failed.", e);
        }
        return null;
    }


    public void labelJobAsCancelled(String taskId) {
        try {
            this.patchBatchApi.patchNamespacedJob(taskId, namespace, JOB_CANCEL_PATCH, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

    public void labelPodAsCancelled(String podName) {
        try {
            this.patchCoreApi.patchNamespacedPod(podName, namespace, POD_CANCEL_PATCH, null);
        } catch (ApiException e) {
            throw KubernetesException.fromApiException(e);
        }
    }

}
