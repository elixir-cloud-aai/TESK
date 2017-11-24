package uk.ac.ebi.tsc.tesk.service;

import com.google.gson.Gson;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1JobList;
import io.kubernetes.client.models.V1PodList;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;
import uk.ac.ebi.tsc.tesk.exception.KubernetesException;
import uk.ac.ebi.tsc.tesk.model.TesCreateTaskResponse;
import uk.ac.ebi.tsc.tesk.model.TesExecutorLog;
import uk.ac.ebi.tsc.tesk.model.TesListTasksResponse;
import uk.ac.ebi.tsc.tesk.model.TesTask;
import uk.ac.ebi.tsc.tesk.util.JobNameGenerator;
import uk.ac.ebi.tsc.tesk.util.KubernetesClientWrapper;
import uk.ac.ebi.tsc.tesk.util.TaskView;
import uk.ac.ebi.tsc.tesk.util.TesKubernetesConverter;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Supplier;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static uk.ac.ebi.tsc.tesk.util.KubernetesConstants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Service
public class TesService {


    @Autowired
    private Gson gson;

    @Autowired
    private KubernetesClientWrapper kubernetesClientWrapper;

    @Autowired
    @Qualifier("taskmaster")
    private Supplier<V1Job> jobTemplateSupplier;

    @Autowired
    private TesKubernetesConverter converter;

    @Autowired
    private JobNameGenerator nameGenerator;

    public TesCreateTaskResponse createTask(TesTask task) {

        V1Job taskMasterJob = this.jobTemplateSupplier.get();
        taskMasterJob.getMetadata().putAnnotationsItem(ANN_TESTASK_NAME_KEY, task.getName());
        List<V1Job> executorsAsJobs = IntStream.range(0, task.getExecutors().size()).
                mapToObj(i -> this.converter.fromTesExecutorToK8sJob(taskMasterJob.getMetadata().getName(), task.getName(), task.getExecutors().get(i), i, task.getResources())).
                collect(Collectors.toList());
        Map<String, List<V1Job>> taskMasterInput = new HashMap<>();
        taskMasterInput.put(TASKMASTER_INPUT_EXEC_KEY, executorsAsJobs);
        String taskMasterInputAsJSON = this.gson.toJson(taskMasterInput);
        taskMasterJob.getSpec().getTemplate().getSpec().getContainers().get(0).getEnv().stream().filter(x -> x.getName().equals(TASKMASTER_INPUT)).forEach(x -> x.setValue(taskMasterInputAsJSON));
        int attemptsNo = 0;
        while (true) {
            try {
                V1Job createdJob = this.kubernetesClientWrapper.createNamespacedJob(DEFAULT_NAMESPACE, taskMasterJob);
                return this.converter.fromK8sJobToTesCreateTaskResponse(createdJob);
            } catch (KubernetesException e) {
                if (!e.isObjectNameDuplicated() || ++attemptsNo >= JOB_CREATE_ATTEMPTS_NO) {
                    throw e;
                }
                this.converter.changeJobName(taskMasterJob, this.nameGenerator.getTaskMasterName());
            }
        }
    }

    public TesTask getTask(String taskId, TaskView view) {
        V1Job taskMasterJob = this.kubernetesClientWrapper.readNamespacedJob(taskId, DEFAULT_NAMESPACE);
        return this.getTask(taskMasterJob, view);
    }

    public TesTask getTask(V1Job taskMasterJob, TaskView view) {

        V1JobList executorJobs = this.kubernetesClientWrapper.listTaskExecutorJobs(DEFAULT_NAMESPACE, taskMasterJob.getMetadata().getName());
        if (view == TaskView.MINIMAL)
            return this.converter.fromK8sJobsToTesTaskMinimal(taskMasterJob, executorJobs.getItems());

        TesTask task = this.converter.fromK8sJobsToTesTask(taskMasterJob, executorJobs.getItems());
        for (V1Job executorJob : executorJobs.getItems()) {
            V1PodList executorJobPods = this.kubernetesClientWrapper.listNamespacedPod(DEFAULT_NAMESPACE, this.converter.getPodsSelectorFromJob(executorJob));
            if (!CollectionUtils.isEmpty(executorJobPods.getItems())) {
                TesExecutorLog executorLog = this.converter.extractExecutorLogFromK8sJobAndPod(executorJob, executorJobPods.getItems().get(0));
                if (view == TaskView.FULL) {
                    String executorPodLog = this.kubernetesClientWrapper.readNamespacedPodLog(executorJobPods.getItems().get(0).getMetadata().getName(), DEFAULT_NAMESPACE);
                    executorLog.setStdout(executorPodLog);
                }
                task.getLogs().get(0).addLogsItem(executorLog);
            }
        }
        if (view == TaskView.BASIC) return task;

        V1PodList taskMasterPods = this.kubernetesClientWrapper.listNamespacedPod(DEFAULT_NAMESPACE, this.converter.getPodsSelectorFromJob(taskMasterJob));
        if (!CollectionUtils.isEmpty(taskMasterPods.getItems())) {
            String taskMasterPodLog = this.kubernetesClientWrapper.readNamespacedPodLog(taskMasterPods.getItems().get(0).getMetadata().getName(), DEFAULT_NAMESPACE);
            task.getLogs().get(0).addSystemLogsItem(taskMasterPodLog);
        }
        return task;


    }


    public TesListTasksResponse listTasks(String namePrefix,
                                          Long pageSize,
                                          String pageToken,
                                          TaskView view) {

        V1JobList taskmasterJobs = this.kubernetesClientWrapper.listTaskmasterJobs(DEFAULT_NAMESPACE, pageToken, Optional.ofNullable(pageSize).map(Long::intValue).orElse(null));
        List<TesTask> tasks = taskmasterJobs.getItems().stream().map(job->this.getTask(job, view)).collect(Collectors.toList());
        TesListTasksResponse response = new TesListTasksResponse();
        response.tasks(tasks).nextPageToken(taskmasterJobs.getMetadata().getContinue());

        return response;

    }


}
