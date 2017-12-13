package uk.ac.ebi.tsc.tesk.service;

import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1JobList;
import io.kubernetes.client.models.V1PodList;
import org.springframework.stereotype.Service;
import uk.ac.ebi.tsc.tesk.exception.KubernetesException;
import uk.ac.ebi.tsc.tesk.model.TesCreateTaskResponse;
import uk.ac.ebi.tsc.tesk.model.TesExecutorLog;
import uk.ac.ebi.tsc.tesk.model.TesListTasksResponse;
import uk.ac.ebi.tsc.tesk.model.TesTask;
import uk.ac.ebi.tsc.tesk.util.TaskView;
import uk.ac.ebi.tsc.tesk.util.component.KubernetesClientWrapper;
import uk.ac.ebi.tsc.tesk.util.component.TesKubernetesConverter;
import uk.ac.ebi.tsc.tesk.util.dto.Job;
import uk.ac.ebi.tsc.tesk.util.dto.JobListContainer;
import uk.ac.ebi.tsc.tesk.util.dto.JobWithExecutors;
import uk.ac.ebi.tsc.tesk.util.dto.SingleJobContainer;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.JOB_CREATE_ATTEMPTS_NO;

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
        SingleJobContainer jobContainer = new SingleJobContainer();
        V1Job taskMasterJob = this.kubernetesClientWrapper.readTaskmasterJob(taskId);
        jobContainer.addJob(taskMasterJob);
        V1JobList executorJobs = this.kubernetesClientWrapper.listSingleTaskExecutorJobs(taskMasterJob.getMetadata().getName());
        jobContainer.addJobList(executorJobs.getItems());
        V1PodList taskMasterPods = this.kubernetesClientWrapper.listSingleJobPods(taskMasterJob);
        jobContainer.addPodList(taskMasterPods.getItems());
        for (V1Job executorJob : executorJobs.getItems()) {
            V1PodList executorJobPods = this.kubernetesClientWrapper.listSingleJobPods(executorJob);
            jobContainer.addPodList(executorJobPods.getItems());
        }
        return this.getTask(jobContainer.getTaskMasterJob(), view);
    }

    private TesTask getTask(JobWithExecutors taskmasterWithExecutors, TaskView view) {

        if (view == TaskView.MINIMAL)
            return this.converter.fromK8sJobsToTesTaskMinimal(taskmasterWithExecutors);

        TesTask task = this.converter.fromK8sJobsToTesTaskBasic(taskmasterWithExecutors, view == TaskView.BASIC);

        if (view == TaskView.BASIC) return task;

        for (int i = 0; i < taskmasterWithExecutors.getExecutors().size(); i++) {
            Job executorJob = taskmasterWithExecutors.getExecutors().get(i);
            if (executorJob.hasPods()) {
                TesExecutorLog executorLog = task.getLogs().get(0).getLogs().get(i);
                if (view == TaskView.FULL) {
                    String executorPodLog = this.kubernetesClientWrapper.readPodLog(executorJob.getFirstPod().getMetadata().getName());
                    executorLog.setStdout(executorPodLog);
                }
            }
        }

        if (taskmasterWithExecutors.getTaskmaster().hasPods()) {
            String taskMasterPodLog = this.kubernetesClientWrapper.readPodLog(taskmasterWithExecutors.getTaskmaster().getFirstPod().getMetadata().getName());
            task.getLogs().get(0).addSystemLogsItem(taskMasterPodLog);
        }
        return task;


    }


    public TesListTasksResponse listTasks(String namePrefix,
                                          Long pageSize,
                                          String pageToken,
                                          TaskView view) {
        JobListContainer jobContainer = new JobListContainer();
        V1JobList taskmasterJobs = this.kubernetesClientWrapper.listAllTaskmasterJobs(pageToken, Optional.ofNullable(pageSize).map(Long::intValue).orElse(null));
        jobContainer.addJobList(taskmasterJobs.getItems());
        V1JobList executorJobs = this.kubernetesClientWrapper.listAllTaskExecutorJobs();
        jobContainer.addJobList(executorJobs.getItems());
        V1PodList taskMasterPods = this.kubernetesClientWrapper.listAllJobPods();
        jobContainer.addPodList(taskMasterPods.getItems());

        List<TesTask> tasks = jobContainer.getTaskMasterJobs().stream().map(job -> this.getTask(job, view)).collect(Collectors.toList());
        TesListTasksResponse response = new TesListTasksResponse();
        response.tasks(tasks).nextPageToken(taskmasterJobs.getMetadata().getContinue());

        return response;

    }


}
