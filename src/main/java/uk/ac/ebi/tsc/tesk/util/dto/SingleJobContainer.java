package uk.ac.ebi.tsc.tesk.util.dto;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
public class SingleJobContainer extends AbstractJobContainer {

    private JobWithExecutors taskmasterJob;

    @Override
    protected void addTaskMasterJob(Job taskmasterJob) {
        this.taskmasterJob = new JobWithExecutors(taskmasterJob);
    }

    @Override
    protected void addExecutorJob(Job executorJob) {
        if (taskmasterJob != null) {
            taskmasterJob.addExecutor(executorJob);
        }
    }

    public JobWithExecutors getTaskMasterJob() {
        return taskmasterJob;
    }
}
