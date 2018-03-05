package uk.ac.ebi.tsc.tesk.util.data;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.JOB_NAME_FILER_SUF;
import static uk.ac.ebi.tsc.tesk.util.constant.Constants.LABEL_TESTASK_ID_KEY;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Tool aimed at building Kubernetes object structure of a list of tasks,
 * by passing to it results of Kubernetes batch method calls.
 * All taskmaster jobs with unique names passed to it will get stored.
 * Only those executor jobs that match already stored taskmaster jobs will be stored
 * (filtering done by taskmaster's name and corresponding executor's label).
 * Pods must be added, when all jobs have already been added.
 * Thus, correct order of calls:
 * 1) taskmasters by {@link AbstractTaskBuilder#addJobList(List)}
 * 2) executors and outputFilers by {@link AbstractTaskBuilder#addJobList(List)}
 * 3) pods by {@link AbstractTaskBuilder#addPodList(List)}
 */
public class TaskListBuilder extends AbstractTaskBuilder {

    private Map<String, Task> tasksById = new LinkedHashMap<>();

    @Override
    protected void addTaskMasterJob(Job taskmasterJob) {
        this.tasksById.putIfAbsent(taskmasterJob.getJob().getMetadata().getName(), new Task(taskmasterJob));
    }

    @Override
    protected void addExecutorJob(Job executorJob) {
        String taskmasterName = executorJob.getJob().getMetadata().getLabels().get(LABEL_TESTASK_ID_KEY);
        Task taskmaster = this.tasksById.get(taskmasterName);
        if (taskmaster != null) {
            taskmaster.addExecutor(executorJob);
        }
    }

    @Override
    protected void addOutputFilerJob(Job executorJob) {
        int outputFilerSuffix = executorJob.getJobName().indexOf(JOB_NAME_FILER_SUF);
        if (outputFilerSuffix <= -1) return;
        String taskmasterName = executorJob.getJobName().substring(0, outputFilerSuffix);
        Task taskmaster = this.tasksById.get(taskmasterName);
        if (taskmaster != null) {
            taskmaster.setOutputFiler(executorJob);
        }
    }

    @Override
    public Task getTask() {
        throw new UnsupportedOperationException();
    }

    @Override
    public List<Task> getTaskList() {
        List<Task> result = new ArrayList<>();
        result.addAll(this.tasksById.values());
        return result;
    }
}
