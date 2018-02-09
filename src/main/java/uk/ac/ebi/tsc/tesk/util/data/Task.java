package uk.ac.ebi.tsc.tesk.util.data;

import com.google.common.base.Strings;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1ObjectMeta;

import java.util.*;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.JOB_NAME_EXEC_NO_LENGTH;
import static uk.ac.ebi.tsc.tesk.util.constant.Constants.JOB_NAME_EXEC_PREFIX;

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


    private int extractExecutorNumber(Job executor) {
        String taskmasterName = this.taskmaster.getJobName();
        return Integer.parseInt(executor.getJobName().substring(taskmasterName.length() + JOB_NAME_EXEC_PREFIX.length(), taskmasterName.length() + JOB_NAME_EXEC_PREFIX.length() + JOB_NAME_EXEC_NO_LENGTH));
    }

    public String getExecutorName(int executorIndex) {
        String taskmasterName = this.taskmaster.getJob().getMetadata().getName();
        return new StringBuilder(taskmasterName).append(JOB_NAME_EXEC_PREFIX).
                append(Strings.padStart(String.valueOf(executorIndex), JOB_NAME_EXEC_NO_LENGTH, '0')).toString();
    }
}
