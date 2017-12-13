package uk.ac.ebi.tsc.tesk.util.dto;

import java.util.*;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.JOB_NAME_EXEC_NO_LENGTH;
import static uk.ac.ebi.tsc.tesk.util.constant.Constants.JOB_NAME_EXEC_PREFIX;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
public class JobWithExecutors {

    private Job taskmaster;
    private Map<String, Job> executorsByName = new HashMap<>();


    public JobWithExecutors(Job taskmaster) {
        this.taskmaster = taskmaster;
    }

    public void addExecutor(Job executor) {
        this.executorsByName.putIfAbsent(executor.getJob().getMetadata().getName(), executor);
    }

    public Job getTaskmaster() {
        return this.taskmaster;
    }

    public List<Job> getExecutors() {
        List<Job> executors = new ArrayList<>();
        executors.addAll(this.executorsByName.values().stream().sorted(Comparator.comparing(
                job -> extractExecutorNumber(job))).collect(Collectors.toList()));
        return executors;
    }

    public Optional<Job> getLastExecutor() {
        if (this.executorsByName.values().isEmpty())
            return Optional.empty();
        List<Job> executors = this.getExecutors();
        return Optional.of(executors.get(executors.size() - 1));
    }


    private int extractExecutorNumber(Job executor) {
        String taskmasterName = this.taskmaster.getJob().getMetadata().getName();
        return Integer.parseInt(executor.getJob().getMetadata().getName().substring(taskmasterName.length() + JOB_NAME_EXEC_PREFIX.length()), JOB_NAME_EXEC_NO_LENGTH);
    }
}
