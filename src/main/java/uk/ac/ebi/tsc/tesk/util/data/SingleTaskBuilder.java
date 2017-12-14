package uk.ac.ebi.tsc.tesk.util.data;

import io.kubernetes.client.models.V1Job;

import java.util.List;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * Tool aimed at building Kubernetes object structure of a single task.
 * Job objects passed to its methods must be prefiltered and belong to a single task
 * (the class does not perform job objects filtering itself).
 * Pods must be added, when all jobs have already been added.
 * Thus, correct order of calls:
 * 1) taskmaster and executors (any order) by
 * {@link AbstractTaskBuilder#addJobList(List)} or {@link AbstractTaskBuilder#addJob(V1Job)}
 * 2) pods by {@link AbstractTaskBuilder#addPodList(List)}
 */
public class SingleTaskBuilder extends AbstractTaskBuilder {

    private Task task;

    @Override
    protected void addTaskMasterJob(Job taskmasterJob) {
        this.task = new Task(taskmasterJob);
    }

    @Override
    protected void addExecutorJob(Job executorJob) {
        if (task != null) {
            task.addExecutor(executorJob);
        }
    }

    @Override
    public Task getTask() {
        return task;
    }

    @Override
    public List<Task> getTaskList() {
        throw new UnsupportedOperationException();
    }
}
