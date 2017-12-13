package uk.ac.ebi.tsc.tesk.util.dto;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.LABEL_TESTASK_ID_KEY;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
public class JobListContainer extends AbstractJobContainer {

    private Map<String, JobWithExecutors> taskmasterJobsByName = new LinkedHashMap<>();

    @Override
    protected void addTaskMasterJob(Job taskmasterJob) {
        this.taskmasterJobsByName.putIfAbsent(taskmasterJob.getJob().getMetadata().getName(), new JobWithExecutors(taskmasterJob));
    }

    @Override
    protected void addExecutorJob(Job executorJob) {
        String taskmasterName = executorJob.getJob().getMetadata().getLabels().get(LABEL_TESTASK_ID_KEY);
        JobWithExecutors taskmaster = this.taskmasterJobsByName.get(taskmasterName);
        if (taskmaster != null) {
            taskmaster.addExecutor(executorJob);
        }
    }

    public List<JobWithExecutors> getTaskMasterJobs() {
        List<JobWithExecutors> result = new ArrayList<>();
        result.addAll(this.taskmasterJobsByName.values());
        return result;
    }
}
