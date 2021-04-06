package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import com.google.common.base.Strings;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1ObjectMeta;

import java.util.*;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.JOB_NAME_EXEC_NO_LENGTH;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.JOB_NAME_EXEC_PREFIX;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * A composite that represents Kubernetes object's graph of a single TES task:
 * taskmaster job with its pods
 * and executor jobs with its pods
 */
public class Task {
    /**
     * Taskmaster job (with corresponding pods)
     */
    private Job taskmaster;
    /**
     * All executor objects (each with corresponding pods)
     * mapped by their K8s job object name
     * (Random order -> sorting in getExecutors)
     */
    private Map<String, Job> executorsByName = new HashMap<>();
    /**
     * Outputs filer job (with corresponding pods) - used to capture failure of handling outputs
     */
    private Job outputFiler;


    public Task(Job taskmaster) {
        this.taskmaster = taskmaster;
    }

    public Task(String taskmasterName) {
        V1Job job = new V1Job();
        job.metadata(new V1ObjectMeta().name(taskmasterName));
        this.taskmaster = new Job(job);
    }

    /**
     * Adds new executor object to Task
     *
     * @param executor - executor job with corresponsing pods
     */
    public void addExecutor(Job executor) {
        this.executorsByName.putIfAbsent(executor.getJob().getMetadata().getName(), executor);
    }

    public void setOutputFiler(Job filer) {
        this.outputFiler = filer;
    }

    /**
     * Returns taskmaster's object
     */
    public Job getTaskmaster() {
        return this.taskmaster;
    }

    /**
     * Returns a shallow copy of executor's list
     * sorted by executor number or empty list, if no executors.
     */
    public List<Job> getExecutors() {
        List<Job> executors = new ArrayList<>();
        executors.addAll(this.executorsByName.values().stream().sorted(Comparator.comparing(
                job -> this.extractExecutorNumber(job))).collect(Collectors.toList()));
        return executors;
    }

    /**
     * Returns last executor from executor's list
     * sorted by executor number or empty Optional, if no executors.
     */
    public Optional<Job> getLastExecutor() {
        if (this.executorsByName.values().isEmpty())
            return Optional.empty();
        List<Job> executors = this.getExecutors();
        return Optional.of(executors.get(executors.size() - 1));
    }

    public Optional<Job> getOutputFiler() {
        return Optional.ofNullable(this.outputFiler);
    }


    private int extractExecutorNumber(Job executor) {
        String taskmasterName = this.taskmaster.getJobName();
        String prefix = taskmasterName + JOB_NAME_EXEC_PREFIX;
        if (executor.getJobName().startsWith(prefix)) {
            return Integer.parseInt(executor.getJobName().substring(prefix.length()));
        }
        return Integer.MAX_VALUE;
    }

    public String getExecutorName(int executorIndex) {
        String taskmasterName = this.taskmaster.getJobName();
        return new StringBuilder(taskmasterName).append(JOB_NAME_EXEC_PREFIX).
                append(Strings.padStart(String.valueOf(executorIndex), JOB_NAME_EXEC_NO_LENGTH, '0')).toString();
    }

}
