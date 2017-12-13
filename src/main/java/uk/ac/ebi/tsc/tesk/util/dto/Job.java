package uk.ac.ebi.tsc.tesk.util.dto;

import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1Pod;

import java.util.ArrayList;
import java.util.List;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * Container for Kubernetes job object
 * and a list of Kubernetes Pod objects
 */
public class Job {

    private V1Job job;

    private List<V1Pod> pods;

    public Job(V1Job job) {
        this.job = job;
    }

    public V1Job getJob() {
        return this.job;
    }

    public void addPod(V1Pod pod) {
        if (this.pods == null) {
            this.pods = new ArrayList<>();
        }
        this.pods.add(pod);
    }

    public boolean hasPods() {
        return this.pods != null && this.pods.size() > 0;
    }

    public V1Pod getFirstPod() {
        if (!hasPods()) return null;
        return this.pods.get(0);
    }
    public List<V1Pod> getPods() {
        if (!hasPods()) return new ArrayList<>();
        return this.pods;
    }

}
