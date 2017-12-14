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
import uk.ac.ebi.tsc.tesk.util.component.KubernetesClientWrapper;
import uk.ac.ebi.tsc.tesk.util.component.TesKubernetesConverter;
import uk.ac.ebi.tsc.tesk.util.constant.TaskView;
import uk.ac.ebi.tsc.tesk.util.data.*;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.JOB_CREATE_ATTEMPTS_NO;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Implementation of controller endpoints.
 * Orchestrates all kubernetes client calls (via wrapper)
 * and converting inputs and outputs with the help of the converter.
 */
@Service
public class TesService {

    private final KubernetesClientWrapper kubernetesClientWrapper;

    private final TesKubernetesConverter converter;

    public TesService(KubernetesClientWrapper kubernetesClientWrapper, TesKubernetesConverter converter) {
        this.kubernetesClientWrapper = kubernetesClientWrapper;
        this.converter = converter;
    }

    /**
     * Creates new TES task, by converting input and calling create method.
     * In case of detecting duplicated task ID, retries with new generated ID (up to a limit of retries)
     */
    public TesCreateTaskResponse createTask(TesTask task) {

        int attemptsNo = 0;
        while (true) {
            try {
                V1Job taskMasterJob = this.converter.fromTesTaskToK8sJob(task);
                V1Job createdJob = this.kubernetesClientWrapper.createJob(taskMasterJob);
                return this.converter.fromK8sJobToTesCreateTaskResponse(createdJob);
            } catch (KubernetesException e) {
                //in case of job name collision retry converting task to job (with new generated name) and creating the job
                if (!e.isObjectNameDuplicated() || ++attemptsNo >= JOB_CREATE_ATTEMPTS_NO) {
                    throw e;
                }
            }
        }
    }

    /**
     * Gets single task's details based on ID.
     * Performs a series of kubernetes API calls and converts results with means of the converter.
     *
     * @param taskId - TES task ID (==taskmaster's job name)
     * @param view   - one of {@link TaskView} values, decides on how much detail is put in results
     * @return - TES task details
     */
    public TesTask getTask(String taskId, TaskView view) {

        V1Job taskMasterJob = this.kubernetesClientWrapper.readTaskmasterJob(taskId);
        V1JobList executorJobs = this.kubernetesClientWrapper.listSingleTaskExecutorJobs(taskMasterJob.getMetadata().getName());
        V1PodList taskMasterPods = this.kubernetesClientWrapper.listSingleJobPods(taskMasterJob);
        AbstractTaskBuilder taskBuilder = new SingleTaskBuilder().addJob(taskMasterJob).addJobList(executorJobs.getItems()).addPodList(taskMasterPods.getItems());
        for (V1Job executorJob : executorJobs.getItems()) {
            V1PodList executorJobPods = this.kubernetesClientWrapper.listSingleJobPods(executorJob);
            taskBuilder.addPodList(executorJobPods.getItems());
        }
        return this.getTask(taskBuilder.getTask(), view);
    }

    /**
     * Common part of task's details retrieval for both single task and each of a list of tasks
     */
    private TesTask getTask(Task taskObjects, TaskView view) {

        if (view == TaskView.MINIMAL)
            return this.converter.fromK8sJobsToTesTaskMinimal(taskObjects);

        TesTask task = this.converter.fromK8sJobsToTesTaskBasic(taskObjects, view == TaskView.BASIC);

        if (view == TaskView.BASIC) return task;

        for (int i = 0; i < taskObjects.getExecutors().size(); i++) {
            Job executorJob = taskObjects.getExecutors().get(i);
            if (executorJob.hasPods()) {
                TesExecutorLog executorLog = task.getLogs().get(0).getLogs().get(i);
                if (view == TaskView.FULL) {
                    String executorPodLog = this.kubernetesClientWrapper.readPodLog(executorJob.getFirstPod().getMetadata().getName());
                    executorLog.setStdout(executorPodLog);
                }
            }
        }

        if (taskObjects.getTaskmaster().hasPods()) {
            String taskMasterPodLog = this.kubernetesClientWrapper.readPodLog(taskObjects.getTaskmaster().getFirstPod().getMetadata().getName());
            task.getLogs().get(0).addSystemLogsItem(taskMasterPodLog);
        }
        return task;


    }

    /**
     * Gets a full list of tasks. Performs Kubernetes API batch calls (all taskmasters, all executors, all pods),
     * combines them together into valid {@link Task} objects and converts to result with means of the converter.
     *
     * @param namePrefix - Unsupported
     * @param pageSize   - Unsupported, in future releases should enable list chunking
     * @param pageToken  - Unsupported, in future releases should enable list chunking
     * @param view       - one of {@link TaskView} values, decides on how much detail is put in each resulting task
     * @return - resulting list of tasks plus paging token (when supported)
     */
    public TesListTasksResponse listTasks(String namePrefix,
                                          Long pageSize,
                                          String pageToken,
                                          TaskView view) {

        V1JobList taskmasterJobs = this.kubernetesClientWrapper.listAllTaskmasterJobs(pageToken, Optional.ofNullable(pageSize).map(Long::intValue).orElse(null));
        V1JobList executorJobs = this.kubernetesClientWrapper.listAllTaskExecutorJobs();
        V1PodList taskMasterPods = this.kubernetesClientWrapper.listAllJobPods();
        AbstractTaskBuilder taskListBuilder = new TaskListBuilder().addJobList(taskmasterJobs.getItems()).addJobList(executorJobs.getItems()).addPodList(taskMasterPods.getItems());
        List<TesTask> tasks = taskListBuilder.getTaskList().stream().map(task -> this.getTask(task, view)).collect(Collectors.toList());
        TesListTasksResponse response = new TesListTasksResponse();
        response.tasks(tasks).nextPageToken(taskmasterJobs.getMetadata().getContinue());

        return response;

    }


}
