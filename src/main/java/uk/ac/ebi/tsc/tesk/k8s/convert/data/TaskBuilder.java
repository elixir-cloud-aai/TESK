package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import com.google.common.collect.MapDifference;
import com.google.common.collect.Maps;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1Pod;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Part of the toolset aimed at building Kubernetes object structure of a task or a list of tasks,
 * by gradually adding to it objects returned by calls to Kubernetes API (jobs and pods).
 * This class takes care of matching jobs with corresponding pods and holds a flat collection (mapped by name)
 * of resulting {@link Job} objects (can be both taskmasters and executors belonging to the same or different task).
 * Accepts a BuildStrategy {@link BuildStrategy}, which implementing classes are responsible of creating,
 * storing and maintaining the actual {@link Task} object or {@link Task} object's list
 * by implementing {@link BuildStrategy#addTaskMasterJob(Job)} and {@link BuildStrategy#addExecutorJob(Job)}}.
 */
public class TaskBuilder {

    public static TaskBuilder newSingleTask() {
        return new TaskBuilder(new SingleTaskStrategy());
    }

    public static TaskBuilder newTaskList() {
        return new TaskBuilder(new TaskListStrategy());
    }

    private final BuildStrategy buildStrategy;

    TaskBuilder(BuildStrategy buildStrategy) {
        this.buildStrategy = buildStrategy;
    }

    /**
     * All jobs - both taskmasters and executors, can belong to different tasks, mapped by name.
     * Used internally by adding pods, to find a job-pod match.
     */
    private Map<String, Job> allJobsByName = new HashMap<>();

    /**
     * Adds single job to the composite. Recognizes the type (taskmaster/executor) by label
     * and calls appropriate storage method.
     */
    public TaskBuilder addJob(V1Job job) {
        Job wrappedJob = new Job(job);
        if (LABEL_JOBTYPE_VALUE_TASKM.equals(job.getMetadata().getLabels().get(LABEL_JOBTYPE_KEY))) {
            this.buildStrategy.addTaskMasterJob(wrappedJob);
        } else if (LABEL_JOBTYPE_VALUE_EXEC.equals(job.getMetadata().getLabels().get(LABEL_JOBTYPE_KEY))) {
            this.buildStrategy.addExecutorJob(wrappedJob);
        } else {
            this.buildStrategy.addOutputFilerJob(wrappedJob);
        }
        this.allJobsByName.putIfAbsent(job.getMetadata().getName(), wrappedJob);
        return this;
    }


    /**
     * Adds a list of jobs to the composite.
     */
    public TaskBuilder addJobList(List<V1Job> jobs) {
        for (V1Job job : jobs) {
            this.addJob(job);
        }
        return this;
    }

    /**
     * Adds a list of pods to the composite and
     * tries to find a matching job for each pod.
     * If there is a match, a pod is placed in the Job object.
     * Will accept a collection of any pods, the ones that don't match get discarded.
     */
    public TaskBuilder addPodList(List<V1Pod> pods) {
        for (V1Pod pod : pods) {
            this.addPod(pod);
        }
        return this;
    }

    /**
     * Adds a pod to the composite and
     * tries to find a matching job for it.
     * If there is a match, a pod is placed in the matching Job object.
     * Match is done by comparing match labels (only!! - match expressions are ignored)
     * of job's selector and comparing them with labels of the pod.
     * If all selectors of the job are present in pod's label set, match is detected
     * (first job-pod match stops search).
     * Will accept also unmatching pod, which won't get stored.
     */
    private void addPod(V1Pod pod) {
        for (Job job : allJobsByName.values()) {
            Map<String, String> selectors = job.getJob().getSpec().getSelector().getMatchLabels();
            Map<String, String> labels = pod.getMetadata().getLabels();
            MapDifference<String, String> diff = Maps.difference(selectors, labels);
            if (selectors.size() == diff.entriesInCommon().size()) {
                //found matching job (only matchLabels taken into account)
                job.addPod(pod);
                break;
            }
        }
    }

    public Task getTask() {
        return this.buildStrategy.getTask();
    }


    public List<Task> getTaskList() {
        return this.buildStrategy.getTaskList();
    }

    Map<String,Job> getAllJobsByName() {
        return this.allJobsByName;
    }

}


