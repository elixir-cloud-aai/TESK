package uk.ac.ebi.tsc.tesk.service;

import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1JobList;
import io.kubernetes.client.models.V1PodList;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;
import uk.ac.ebi.tsc.tesk.exception.KubernetesException;
import uk.ac.ebi.tsc.tesk.model.TesCreateTaskResponse;
import uk.ac.ebi.tsc.tesk.model.TesExecutorLog;
import uk.ac.ebi.tsc.tesk.model.TesListTasksResponse;
import uk.ac.ebi.tsc.tesk.model.TesTask;
import uk.ac.ebi.tsc.tesk.util.KubernetesClientWrapper;
import uk.ac.ebi.tsc.tesk.util.TaskView;
import uk.ac.ebi.tsc.tesk.util.TesKubernetesConverter;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.util.KubernetesConstants.JOB_CREATE_ATTEMPTS_NO;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Service
public class TesService {


    private final KubernetesClientWrapper kubernetesClientWrapper;

    private final TesKubernetesConverter converter;

    public TesService(KubernetesClientWrapper kubernetesClientWrapper, TesKubernetesConverter converter) {
        this.kubernetesClientWrapper = kubernetesClientWrapper;
        this.converter = converter;
    }

    public TesCreateTaskResponse createTask(TesTask task) {

        int attemptsNo = 0;
        while (true) {
            try {
                V1Job taskMasterJob = this.converter.fromTesTaskToK8sJob(task);
                V1Job createdJob = this.kubernetesClientWrapper.createJob(taskMasterJob);
                return this.converter.fromK8sJobToTesCreateTaskResponse(createdJob);
            } catch (KubernetesException e) {
                //in case of job name collision retry converting task to job (with new name) and creating the job
                if (!e.isObjectNameDuplicated() || ++attemptsNo >= JOB_CREATE_ATTEMPTS_NO) {
                    throw e;
                }
            }
        }
    }

    public TesTask getTask(String taskId, TaskView view) {
        V1Job taskMasterJob = this.kubernetesClientWrapper.readTaskmasterJob(taskId);
        return this.getTask(taskMasterJob, view);
    }

    private TesTask getTask(V1Job taskMasterJob, TaskView view) {

        V1JobList executorJobs = this.kubernetesClientWrapper.listTaskExecutorJobs(taskMasterJob.getMetadata().getName());
        if (view == TaskView.MINIMAL)
            return this.converter.fromK8sJobsToTesTaskMinimal(taskMasterJob, executorJobs.getItems());

        TesTask task = this.converter.fromK8sJobsToTesTask(taskMasterJob, executorJobs.getItems(), view == TaskView.BASIC);
        for (V1Job executorJob : executorJobs.getItems()) {
            V1PodList executorJobPods = this.kubernetesClientWrapper.listJobPods(executorJob);
            if (!CollectionUtils.isEmpty(executorJobPods.getItems())) {
                TesExecutorLog executorLog = this.converter.extractExecutorLogFromK8sJobAndPod(executorJob, executorJobPods.getItems().get(0));
                if (view == TaskView.FULL) {
                    String executorPodLog = this.kubernetesClientWrapper.readPodLog(executorJobPods.getItems().get(0).getMetadata().getName());
                    executorLog.setStdout(executorPodLog);
                }
                task.getLogs().get(0).addLogsItem(executorLog);
            }
        }
        if (view == TaskView.BASIC) return task;

        V1PodList taskMasterPods = this.kubernetesClientWrapper.listJobPods(taskMasterJob);
        if (!CollectionUtils.isEmpty(taskMasterPods.getItems())) {
            String taskMasterPodLog = this.kubernetesClientWrapper.readPodLog(taskMasterPods.getItems().get(0).getMetadata().getName());
            task.getLogs().get(0).addSystemLogsItem(taskMasterPodLog);
        }
        return task;


    }


    public TesListTasksResponse listTasks(String namePrefix,
                                          Long pageSize,
                                          String pageToken,
                                          TaskView view) {

        V1JobList taskmasterJobs = this.kubernetesClientWrapper.listTaskmasterJobs(pageToken, Optional.ofNullable(pageSize).map(Long::intValue).orElse(null));
        List<TesTask> tasks = taskmasterJobs.getItems().stream().map(job -> this.getTask(job, view)).collect(Collectors.toList());
        TesListTasksResponse response = new TesListTasksResponse();
        response.tasks(tasks).nextPageToken(taskmasterJobs.getMetadata().getContinue());

        return response;

    }


}
