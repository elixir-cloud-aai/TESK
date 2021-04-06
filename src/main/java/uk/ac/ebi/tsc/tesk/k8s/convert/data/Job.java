package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1Pod;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * A container for a single Kubernetes job object (can be both a taskmaster and an executor)
 * and its list of worker pods (Kubernetes Pod objects)
 */
public class Job {
    /**
     * Kubernetes job object
     */
    private V1Job job;

    /**
     * The list of Kubernetes pod objects created by the job
     */
    private List<V1Pod> pods;

    public Job(V1Job job) {
        this.job = job;
    }

    public V1Job getJob() {
        return this.job;
    }

    /**
     * Adds a single pod to a list (without any duplication checks)
     */
    public void addPod(V1Pod pod) {
        if (this.pods == null) {
            this.pods = new ArrayList<>();
        }
        this.pods.add(pod);
    }

    public boolean hasPods() {
        return this.pods != null && this.pods.size() > 0;
    }

    /**
     * Returns arbitrarily chosen pod from the list (currently the first one added)
     * or null, if job has no pods.
     */
    public V1Pod getFirstPod() {
        if (!hasPods()) return null;
        return this.pods.get(0);
    }

    /**
     * Returns the list of job pods in the order of addition to the list
     * or empty list, if no pods.
     */
    public List<V1Pod> getPods() {
        if (!hasPods()) return new ArrayList<>();
        return this.pods;
    }
    public void changeJobName(String newName) {
        this.job.getMetadata().name(newName);
        this.job.getSpec().getTemplate().getMetadata().name(newName);
        this.job.getSpec().getTemplate().getSpec().getContainers().get(0).setName(newName);
    }
    public String getJobName() {
        return this.job.getMetadata().getName();
    }

}
