package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import java.util.List;

/**
 * Part of the toolset aimed at building Kubernetes object structure of a task or a list of tasks,
 * by gradually adding to it objects returned by calls to Kubernetes API (jobs and pods).
 * Implementing classes are responsible of creating,
 * storing and maintaining the actual {@link Task} object or {@link Task} object's list
 */
public interface BuildStrategy {
    /**
     * Implementing method should optionally filter and than place
     * the passed taskmaster's job object in the resulting structure.
     */
    void addTaskMasterJob(Job taskmasterJob);

    /**
     * Implementing method should optionally filter and than place
     * the passed executor's job object in the resulting structure
     * (and match it to appropriate taskmaster)
     */
    void addExecutorJob(Job executorJob);

    /**
     * Implementing method should filter and than place
     * the passed filer's job object in the resulting structure
     * (and match it to appropriate taskmaster)
     */
    void addOutputFilerJob(Job filerJob);

    /**
     * Return single Task composite object
     */
    Task getTask();

    /**
     * Return list of Task composite objects
     */
    List<Task> getTaskList();

}
