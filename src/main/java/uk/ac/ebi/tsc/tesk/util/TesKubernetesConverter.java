package uk.ac.ebi.tsc.tesk.util;

import io.kubernetes.client.models.*;
import org.joda.time.format.ISODateTimeFormat;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import uk.ac.ebi.tsc.tesk.model.*;

import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.function.Supplier;

import static uk.ac.ebi.tsc.tesk.util.KubernetesConstants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Component
public class TesKubernetesConverter {

    private static final Integer TRUE = 1;

    @Autowired
    @Qualifier("executor")
    private Supplier<V1Job> executorTemplateSupplier;

    @Autowired
    private JobNameGenerator jobNameGenerator;

    public void changeJobName(V1Job job, String newName) {
        job.getMetadata().name(newName);
        job.getSpec().getTemplate().getMetadata().name(newName);
        job.getSpec().getTemplate().getSpec().getContainers().get(0).setName(newName);
    }

    public V1Job fromTesExecutorToK8sJob(String generatedTaskId, String tesTaskName, TesExecutor executor, int executorIndex, TesResources resources) {
        V1Job job = executorTemplateSupplier.get();
        this.changeJobName(job, this.jobNameGenerator.getExecutorName(generatedTaskId, executorIndex));
        job.getMetadata().putLabelsItem(LABEL_TESTASK_ID_KEY, generatedTaskId);
        job.getMetadata().putLabelsItem(LABEL_EXECNO_KEY, Integer.valueOf(executorIndex).toString());
        job.getMetadata().putAnnotationsItem(ANN_TESTASK_NAME_KEY, tesTaskName);
        V1Container container = job.getSpec().getTemplate().getSpec().getContainers().get(0);
        container.image(executor.getImage());
        executor.getCommand().stream().forEach(container::addCommandItem);
        container.getResources().
                putRequestsItem(RESOURCE_CPU_KEY, resources.getCpuCores().toString()).
                putRequestsItem(RESOURCE_MEM_KEY, resources.getRamGb().toString() + RESOURCE_MEM_UNIT);
        return job;
    }

    public TesCreateTaskResponse fromK8sJobToTesCreateTaskResponse(V1Job job) {
        return new TesCreateTaskResponse().id(job.getMetadata().getName());
    }

    public TesState extractStateFromK8sJobs(V1Job taskMasterJob, List<V1Job> executorJobs) {
        String taskMasterJobName = taskMasterJob.getMetadata().getName();
        Optional<V1Job> lastExecutor = executorJobs.stream().max(Comparator.comparing(
                job->this.jobNameGenerator.extractExecutorNumberFromName(taskMasterJobName, job.getMetadata().getName())));
        boolean taskMasterRunning = TRUE.equals(taskMasterJob.getStatus().getActive());
        //boolean taskMasterFailed = TRUE.equals(taskMasterJob.getStatus().getFailed());
        boolean taskMasterCompleted = TRUE.equals(taskMasterJob.getStatus().getSucceeded());
        boolean executorPresent = lastExecutor.isPresent();
        //boolean lastExecutorRunning = executorPresent && TRUE.equals(lastExecutor.get().getStatus().getActive());
        boolean lastExecutorFailed = executorPresent && TRUE.equals(lastExecutor.get().getStatus().getFailed());
        boolean lastExecutorCompleted = executorPresent && TRUE.equals(lastExecutor.get().getStatus().getSucceeded());

        if (taskMasterRunning) return TesState.RUNNING;
        if (taskMasterCompleted && lastExecutorCompleted) return TesState.COMPLETE;
        if (taskMasterCompleted && lastExecutorFailed) return TesState.EXECUTOR_ERROR;
        return TesState.SYSTEM_ERROR;
    }
    public TesExecutorLog extractExecutorLogFromK8sJobAndPod(V1Job executorJob, V1Pod executorPod) {
        TesExecutorLog log = new TesExecutorLog();
        log.setStartTime(Optional.ofNullable(executorJob.getStatus().getStartTime()).map(time -> ISODateTimeFormat.dateTime().print(time)).orElse(null));
        log.setEndTime(Optional.ofNullable(executorJob.getStatus().getCompletionTime()).map(time -> ISODateTimeFormat.dateTime().print(time)).orElse(null));
        log.setExitCode(Optional.ofNullable(executorPod.getStatus()).
                map(status -> status.getContainerStatuses()).
                map(list -> list.size() > 0 ? list.get(0): null).
                map(V1ContainerStatus::getState).
                map(V1ContainerState::getTerminated).
                map(V1ContainerStateTerminated::getExitCode).
                orElse(null));
        return log;
    }

    public TesTask fromK8sJobsToTesTaskMinimal(V1Job taskMasterJob, List<V1Job> executorJobs) {
        TesTask task = new TesTask();
        task.setId(taskMasterJob.getMetadata().getName());
        task.setState(this.extractStateFromK8sJobs(taskMasterJob, executorJobs));
        return task;
    }

    public TesTask fromK8sJobsToTesTask(V1Job taskMasterJob, List<V1Job> executorJobs) {
        TesTask task = this.fromK8sJobsToTesTaskMinimal(taskMasterJob, executorJobs);
        task.setCreationTime(ISODateTimeFormat.dateTime().print(taskMasterJob.getMetadata().getCreationTimestamp()));
        TesTaskLog log = new TesTaskLog();
        task.addLogsItem(log);
        log.setStartTime(Optional.ofNullable(taskMasterJob.getStatus().getStartTime()).map(time -> ISODateTimeFormat.dateTime().print(time)).orElse(null));
        log.setEndTime(Optional.ofNullable(taskMasterJob.getStatus().getCompletionTime()).map(time -> ISODateTimeFormat.dateTime().print(time)).orElse(null));
        return task;
    }


}
