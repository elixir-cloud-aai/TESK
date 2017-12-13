package uk.ac.ebi.tsc.tesk.util.dto;

import com.google.common.collect.MapDifference;
import com.google.common.collect.Maps;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1Pod;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.LABEL_JOBTYPE_KEY;
import static uk.ac.ebi.tsc.tesk.util.constant.Constants.LABEL_JOBTYPE_VALUE_TASKM;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
public abstract class AbstractJobContainer {


    private Map<String, Job> allJobsByName = new HashMap<>();

    public void addJob(V1Job job) {
        Job wrappedJob = new Job(job);
        if (LABEL_JOBTYPE_VALUE_TASKM.equals(job.getMetadata().getLabels().get(LABEL_JOBTYPE_KEY))) {
            this.addTaskMasterJob(wrappedJob);
        } else {
            this.addExecutorJob(wrappedJob);
        }
        this.allJobsByName.putIfAbsent(job.getMetadata().getName(), wrappedJob);
    }

    protected abstract void addTaskMasterJob(Job taskmasterJob);

    protected abstract void addExecutorJob(Job executorJob);

    public void addJobList(List<V1Job> jobs) {
        for (V1Job job : jobs) {
            this.addJob(job);
        }
    }

    public void addPodList(List<V1Pod> pods) {
        for (V1Pod pod : pods) {
            this.addPod(pod);
        }
    }

    private void addPod(V1Pod pod) {
        for (Job job : allJobsByName.values()) {
            Map<String, String> selectors = job.getJob().getSpec().getSelector().getMatchLabels();
            Map<String, String> labels = pod.getMetadata().getLabels();
            MapDifference<String, String> diff = Maps.difference(selectors, labels);
            if (selectors.size() == diff.entriesInCommon().size()) {
                //found matching job (only matchLabels taken into account)
                job.addPod(pod);
            }
        }
    }

}


