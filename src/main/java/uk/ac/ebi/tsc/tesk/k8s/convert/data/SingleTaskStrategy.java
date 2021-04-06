package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import com.google.common.collect.Lists;
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
 * 1) taskmaster {@link TaskBuilder#addJobList(List)} or {@link TaskBuilder#addJob(V1Job)}
 * 2) executors and outputFiler {@link TaskBuilder#addJobList(List)} or {@link TaskBuilder#addJob(V1Job)}
 * 3) pods by {@link TaskBuilder#addPodList(List)}
 */
public class SingleTaskStrategy implements BuildStrategy {

    private Task task;

    @Override
    public void addTaskMasterJob(Job taskmasterJob) {
        this.task = new Task(taskmasterJob);
    }

    @Override
    public void addExecutorJob(Job executorJob) {
        if (task != null) {
            task.addExecutor(executorJob);
        }
    }
    @Override
    public void addOutputFilerJob(Job executorJob) {
        if (task != null) {
            task.setOutputFiler(executorJob);
        }
    }

    @Override
    public Task getTask() {
        return task;
    }

    @Override
    public List<Task> getTaskList() {
        return Lists.newArrayList(task);
    }
}
