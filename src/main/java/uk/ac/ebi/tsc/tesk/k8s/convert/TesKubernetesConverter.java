package uk.ac.ebi.tsc.tesk.k8s.convert;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.gson.Gson;

import io.kubernetes.client.custom.Quantity;
import io.kubernetes.client.custom.QuantityFormatter;
import io.kubernetes.client.openapi.models.*;

import org.joda.time.format.DateTimeFormatter;
import org.joda.time.format.ISODateTimeFormat;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import uk.ac.ebi.tsc.tesk.config.security.User;
import uk.ac.ebi.tsc.tesk.tes.model.*;
import uk.ac.ebi.tsc.tesk.trs.TrsToolClient;
import uk.ac.ebi.tsc.tesk.k8s.constant.K8sConstants;
import uk.ac.ebi.tsc.tesk.k8s.convert.data.Job;
import uk.ac.ebi.tsc.tesk.k8s.convert.data.Task;

import java.io.IOException;
import java.util.*;
import java.util.function.Supplier;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.*;
import static uk.ac.ebi.tsc.tesk.k8s.constant.K8sConstants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Conversion of TES objects to and from Kubernetes Objects
 */
@Component
public class TesKubernetesConverter {

    private final static Logger logger = LoggerFactory.getLogger(TesKubernetesConverter.class);

    private final Supplier<V1Job> executorTemplateSupplier;

    private final Supplier<V1Job> taskmasterTemplateSupplier;

    private final ObjectMapper objectMapper;

    private final Gson gson;

    private final TrsToolClient trsClient;

    private enum JOB_STATUS {ACTIVE, SUCCEEDED, FAILED}

    private static final DateTimeFormatter DATE_FORMATTER = ISODateTimeFormat.dateTime().withZoneUTC();

    public TesKubernetesConverter(@Qualifier("executor") Supplier<V1Job> executorTemplateSupplier, @Qualifier("taskmaster")
            Supplier<V1Job> taskmasterTemplateSupplier, ObjectMapper objectMapper, Gson gson, TrsToolClient trsClient) {
        this.executorTemplateSupplier = executorTemplateSupplier;
        this.taskmasterTemplateSupplier = taskmasterTemplateSupplier;
        this.objectMapper = objectMapper;
        this.gson = gson;
        this.trsClient = trsClient;
    }

    /**
     * Converts TES task to new K8s Job object with random generated name
     *
     * @param task - TES Task input object
     * @return K8s Job Object
     */
    @SuppressWarnings("unchecked")
    public V1Job fromTesTaskToK8sJob(TesTask task, User user) {
        //get new Job template with random generated name;
        V1Job taskMasterJob = this.taskmasterTemplateSupplier.get();
        //put input task name as annotation
        taskMasterJob.getMetadata().putAnnotationsItem(ANN_TESTASK_NAME_KEY, task.getName());
        //creating user and owning group
        taskMasterJob.getMetadata().putLabelsItem(LABEL_USERID_KEY, user.getUsername());
        if (task.getTags() != null && task.getTags().containsKey("GROUP_NAME")) {
            taskMasterJob.getMetadata().putLabelsItem(LABEL_GROUPNAME_KEY, task.getTags().get("GROUP_NAME"));
        } else if (user.isMember()) {
            taskMasterJob.getMetadata().putLabelsItem(LABEL_GROUPNAME_KEY, user.getAnyGroup());
        }
        try {
            //in order to retrieve task details, when querying for task details, whole tesTask object is placed as taskMaster's annotation
            //Jackson for TES objects - because, we rely on auto-generated annotations for Json mapping
            taskMasterJob.getMetadata().putAnnotationsItem(ANN_JSON_INPUT_KEY, this.objectMapper.writeValueAsString(task));
        } catch (JsonProcessingException ex) {
            logger.info(String.format("Serializing task %s to JSON failed", taskMasterJob.getMetadata().getName()), ex);
        }
        //Converting executors to Kubernetes Job Objects
        List<V1Job> executorsAsJobs = IntStream.range(0, task.getExecutors().size()).
                mapToObj(i -> this.fromTesExecutorToK8sJob(taskMasterJob.getMetadata().getName(), task.getName(), task.getExecutors().get(i), i, task.getResources(), user)).
                collect(Collectors.toList());
        Map<String, Object> taskMasterInput = new HashMap<>();
        try {
            //converting original inputs, outputs, volumes and disk size back again to JSON (will be part of taskMaster's input parameter)
            //Jackson - for TES objects
            List<TesInput> inputs = task.getInputs() == null ? new ArrayList<>() : task.getInputs();
            List<TesOutput> outputs = task.getOutputs() == null ? new ArrayList<>() : task.getOutputs();
            List<String> volumes = task.getVolumes() == null ? new ArrayList<>() : task.getVolumes();
            String jobAsJson = this.objectMapper.writeValueAsString(new TesTask().inputs(inputs).outputs(outputs).volumes(volumes).
                    resources(new TesResources().diskGb(Optional.ofNullable(task.getResources()).map(TesResources::getDiskGb).orElse(RESOURCE_DISK_DEFAULT))));
            //merging 2 JSONs together into one map
            Map<String, Object> jobAsMap = gson.fromJson(jobAsJson, Map.class);
            taskMasterInput.putAll(jobAsMap);
        } catch (JsonProcessingException e) {
            logger.info(String.format("Serializing copy of task %s to JSON failed", taskMasterJob.getMetadata().getName()), e);
            //TODO throw
        }
        taskMasterInput.put(TASKMASTER_INPUT_EXEC_KEY, executorsAsJobs);
        String taskMasterInputAsJSON = this.gson.toJson(taskMasterInput);
        //placing taskmaster's parameter (JSONed map of: inputs, outputs, volumes, executors (as jobs) into ENV variable in taskmaster spec
        taskMasterJob.getSpec().getTemplate().getSpec().getContainers().get(0).getEnv().stream().filter(x -> x.getName().equals(TASKMASTER_INPUT)).forEach(x -> x.setValue(taskMasterInputAsJSON));
        return taskMasterJob;
    }

    /**
     * Converts TES executor to new K8s Job object, that is passed to taskMaster
     * as part of input parameters
     * Name of executor job relies on taskMaster job's name (taskmaster's jobs name + constant suffix)
     *
     * @param generatedTaskId - random generated job's name == task id
     * @param tesTaskName     - input task name
     * @param executor        - TES executor input object
     * @param executorIndex   - ordinal number of executor
     * @param resources       - input task resources
     * @param user            - creator of the task
     * @return - executor K8s job object. To be placed in taskMaster input JSON map in the list of executors
     */
    public V1Job fromTesExecutorToK8sJob(String generatedTaskId, String tesTaskName, TesExecutor executor, int executorIndex, TesResources resources, User user) {
        //get new template executor Job object
        V1Job job = executorTemplateSupplier.get();
        //set executors name based on taskmaster's job name
        new Job(job).changeJobName(new Task(generatedTaskId).getExecutorName(executorIndex));
        //put arbitrary labels and annotations:
        //the important one --> taskId - to search for executors of a given task
        job.getMetadata().putLabelsItem(LABEL_TESTASK_ID_KEY, generatedTaskId);
        job.getMetadata().putLabelsItem(LABEL_EXECNO_KEY, Integer.valueOf(executorIndex).toString());
        job.getMetadata().putAnnotationsItem(ANN_TESTASK_NAME_KEY, tesTaskName);
        job.getMetadata().putLabelsItem(LABEL_USERID_KEY, user.getUsername());
        V1Container container = job.getSpec().getTemplate().getSpec().getContainers().get(0);
        //Tries to convert potential TRS URI into docker image. If conversion unsuccessful -> leaves the original image value.
        container.image(this.trsClient.getDockerImageForToolVersionURI(executor.getImage()));
        //Should we map executor's command to job container's command (==ENTRYPOINT) or job container's args (==CMD)?
        //It will be command == ENTRYPOINT, because of shell requirement and no custom entrypoints in bio tools.
        new ExecutorCommandWrapper(executor).getCommandsWithStreamRedirects().forEach(container::addCommandItem);
        if (executor.getEnv() != null) {
            executor.getEnv().forEach((key, value) -> container.addEnvItem(new V1EnvVar().name(key).value(value)));
        }
        container.setWorkingDir(executor.getWorkdir());
        Optional.ofNullable(resources).map(TesResources::getCpuCores).ifPresent(cpuCores -> container.getResources().putRequestsItem(RESOURCE_CPU_KEY, new QuantityFormatter().parse(cpuCores.toString())));
	// Limit number of decimals to 6
	Optional.ofNullable(resources).map(TesResources::getRamGb).ifPresent(ramGb -> container.getResources().putRequestsItem(RESOURCE_MEM_KEY, new QuantityFormatter().parse(String.format("%.6f",ramGb)+RESOURCE_MEM_UNIT)));

        return job;
    }

    /**
     * Retrieves TesCreateTaskResponse from K8s job
     * At the moment - only wraps job's name/task's id
     *
     * @param job - K8s taskMaster job
     * @return - TesCreateTaskResponse wrapping task ID
     */
    public TesCreateTaskResponse fromK8sJobToTesCreateTaskResponse(V1Job job) {
        return new TesCreateTaskResponse().id(job.getMetadata().getName());
    }

    /**
     * Resolver of K8s V1JobStatus object.
     * Tests if job is in a given state
     *
     * @param testedObject  - V1JobStatus of a job
     * @param testObjective - status to be checked against
     * @return - if Job is in the given status
     */
    private boolean isJobInStatus(V1JobStatus testedObject, JOB_STATUS testObjective) {
        Integer noOfPodsInState = null;
        switch (testObjective) {
            case ACTIVE:
                noOfPodsInState = testedObject.getActive();
                break;
            case SUCCEEDED:
                noOfPodsInState = testedObject.getSucceeded();
                break;
            case FAILED:
                if (Optional.ofNullable(testedObject.getSucceeded()).map(no -> no > 0).orElse(false)) {
                    //if there are any successful - the job has not FAILED
                    return false;
                }
                noOfPodsInState = testedObject.getFailed();
                break;
        }
        return Optional.ofNullable(noOfPodsInState).map(no -> no > 0).orElse(false);
    }

    /**
     * Derives TES task's status from task's object graph (packed into {@link Task} object)
     * Uses status of taskmaster's and executor's jobs and taskmaster's and executor's pods
     *
     * @param taskmasterWithExecutors - taskMaster's  full object graph
     * @return TES task status
     */
    public TesState extractStateFromK8sJobs(Task taskmasterWithExecutors) {
        V1Job taskMasterJob = taskmasterWithExecutors.getTaskmaster().getJob();
        Optional<Job> lastExecutor = taskmasterWithExecutors.getLastExecutor();
        Optional<Job> outputFiler = taskmasterWithExecutors.getOutputFiler();
        boolean taskMasterCancelled = LABEL_TASKSTATE_VALUE_CANC.equals(taskMasterJob.getMetadata().getLabels().get(LABEL_TASKSTATE_KEY));
        boolean taskMasterRunning = this.isJobInStatus(taskMasterJob.getStatus(), JOB_STATUS.ACTIVE);
        boolean taskMasterCompleted = this.isJobInStatus(taskMasterJob.getStatus(), JOB_STATUS.SUCCEEDED);
        boolean executorPresent = lastExecutor.isPresent();
        boolean lastExecutorFailed = executorPresent && this.isJobInStatus(lastExecutor.get().getJob().getStatus(), JOB_STATUS.FAILED);
        boolean lastExecutorCompleted = executorPresent && this.isJobInStatus(lastExecutor.get().getJob().getStatus(), JOB_STATUS.SUCCEEDED);
        boolean outputFilerFailed = outputFiler.isPresent() && this.isJobInStatus(outputFiler.get().getJob().getStatus(), JOB_STATUS.FAILED);
        String pending = K8sConstants.PodPhase.PENDING.getCode();
        boolean taskMasterPending = taskmasterWithExecutors.getTaskmaster().getPods().stream().anyMatch(pod -> pending.equals(pod.getStatus().getPhase()));
        boolean lastExecutorPending = executorPresent && lastExecutor.get().getPods().stream().anyMatch(pod -> pending.equals(pod.getStatus().getPhase()));

        if (taskMasterCancelled) return TesState.CANCELED;
        if (taskMasterCompleted && outputFilerFailed) return TesState.SYSTEM_ERROR;
        if (taskMasterCompleted && lastExecutorCompleted) return TesState.COMPLETE;
        if (taskMasterCompleted && lastExecutorFailed) return TesState.EXECUTOR_ERROR;
        if (taskMasterPending) return TesState.QUEUED;
        if (taskMasterRunning && !executorPresent) return TesState.INITIALIZING;
        //each executor job's pod can wait for execution as Pending
        // --> Job status can change from Queued to Running and back again to Queued, if more than one executor.
        if (lastExecutorPending) return TesState.QUEUED;
        if (taskMasterRunning) return TesState.RUNNING;
        return TesState.SYSTEM_ERROR;
    }

    /**
     * Extracts TesExecutorLog from executor job and pod objects
     * !! does not contain stdout (which needs access to pod log)
     *
     * @param executor - executor job and pods object
     * @return - TesExecutorLog object (part of the BASIC/FULL output)
     */
    public TesExecutorLog extractExecutorLogFromK8sJobAndPod(Job executor) {
        TesExecutorLog log = new TesExecutorLog();
        V1Job executorJob = executor.getJob();
        //TODO - better return controller startTime, when possible (now it behaves as if started, even if it is pending)
        log.setStartTime(Optional.ofNullable(executorJob.getStatus().getStartTime()).map(DATE_FORMATTER::print).orElse(null));
        log.setEndTime(Optional.ofNullable(executorJob.getStatus().getCompletionTime()).map(DATE_FORMATTER::print).orElse(null));
        //workaround for py-tes compatibility. py-tes breaks for ExecutorLogs that can unmarshal to TaskLogs. Non-null stdout prevents that.
        log.setStdout("");
        if (executor.hasPods()) {
            log.setExitCode(Optional.ofNullable(executor.getFirstPod().getStatus()).
                    map(V1PodStatus::getContainerStatuses).
                    map(list -> list.size() > 0 ? list.get(0) : null).
                    map(V1ContainerStatus::getState).
                    map(V1ContainerState::getTerminated).
                    map(V1ContainerStateTerminated::getExitCode).
                    orElse(null));
        }
        return log;
    }

    /**
     * Extracts minimal view of TesTask from taskMaster's and executors' job and pod objects
     */
    public TesTask fromK8sJobsToTesTaskMinimal(Task taskmasterWithExecutors, boolean isList) {
        TesTask task = new TesTask();
        V1ObjectMeta metadata = taskmasterWithExecutors.getTaskmaster().getJob().getMetadata();
        task.setId(metadata.getName());
        task.setState(this.extractStateFromK8sJobs(taskmasterWithExecutors));
        //we need that info only for postAuthorization of a getTask; for list auth is handled at the query level
        if (!isList) {
            TesTaskLog log = new TesTaskLog();
            task.addLogsItem(log);
            log.putMetadataItem("USER_ID", metadata.getLabels().get(LABEL_USERID_KEY));
            if (metadata.getLabels().containsKey(LABEL_GROUPNAME_KEY)) {
                log.putMetadataItem("GROUP_NAME", metadata.getLabels().get(LABEL_GROUPNAME_KEY));
            }
        }
        return task;
    }

    /**
     * Extracts basic view of TesTask from taskMaster's and executors' job and pod objects
     *
     * @param nullifyInputContent - true, if input.content has to be removed from the result (in BASIC view)
     */
    public TesTask fromK8sJobsToTesTaskBasic(Task taskmasterWithExecutors, boolean nullifyInputContent) {
        TesTask task = new TesTask();
        V1Job taskMasterJob = taskmasterWithExecutors.getTaskmaster().getJob();
        V1ObjectMeta taskMasterJobMetadata = taskMasterJob.getMetadata();
        String inputJson = Optional.ofNullable(taskMasterJobMetadata.getAnnotations()).map(ann -> ann.get(ANN_JSON_INPUT_KEY)).orElse("");
        try {
            task = this.objectMapper.readValue(inputJson, TesTask.class);
            if (nullifyInputContent && task.getInputs() != null) {
                task.getInputs().forEach(input -> input.setContent(null));
            }
        } catch (IOException ex) {
            logger.info("Deserializing task {} from JSON failed; {}", taskMasterJobMetadata.getName(), ex.getMessage());
        }
        task.setId(taskMasterJobMetadata.getName());
        task.setState(this.extractStateFromK8sJobs(taskmasterWithExecutors));
        task.setCreationTime(DATE_FORMATTER.print(taskMasterJobMetadata.getCreationTimestamp()));
        TesTaskLog log = new TesTaskLog();
        task.addLogsItem(log);
        log.putMetadataItem("USER_ID", taskMasterJobMetadata.getLabels().get(LABEL_USERID_KEY));
        if (taskMasterJobMetadata.getLabels().containsKey(LABEL_GROUPNAME_KEY)) {
            log.putMetadataItem("GROUP_NAME", taskMasterJobMetadata.getLabels().get(LABEL_GROUPNAME_KEY));
        }
        log.setStartTime(Optional.ofNullable(taskMasterJob.getStatus().getStartTime()).map(DATE_FORMATTER::print).orElse(null));
        log.setEndTime(Optional.ofNullable(taskMasterJob.getStatus().getCompletionTime()).map(DATE_FORMATTER::print).orElse(null));
        for (Job executorJob : taskmasterWithExecutors.getExecutors()) {
            TesExecutorLog executorLog = this.extractExecutorLogFromK8sJobAndPod(executorJob);
            task.getLogs().get(0).addLogsItem(executorLog);
        }
        return task;
    }

    public Optional<String> getNameOfFirstRunningPod(V1PodList podList) {
        return podList.getItems().stream().filter(pod -> "Running".equals(pod.getStatus().getPhase())).findFirst().map(pod -> pod.getMetadata().getName());
    }

}
