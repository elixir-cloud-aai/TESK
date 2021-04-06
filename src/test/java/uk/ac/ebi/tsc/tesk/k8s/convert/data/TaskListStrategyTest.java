package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1ObjectMeta;
import org.junit.Test;

import static org.hamcrest.CoreMatchers.is;
import static org.junit.Assert.*;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.LABEL_TESTASK_ID_KEY;

public class TaskListStrategyTest {

    @Test
    public void addTaskMasterJob() {
        BuildStrategy taskListMaker = new TaskListStrategy();
        Job job = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything")));
        taskListMaker.addTaskMasterJob(job);
        assertThat(taskListMaker.getTaskList().get(0).getTaskmaster().getJobName(), is("anything"));
    }

    @Test
    public void addExecutorJob_no_taskmaster_link() {
        BuildStrategy taskListMaker = new TaskListStrategy();
        Job taskmaster = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything1")));
        Job executor = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything2").putLabelsItem("aa", "nn")));
        taskListMaker.addTaskMasterJob(taskmaster);
        taskListMaker.addExecutorJob(executor);
        assertThat(taskListMaker.getTaskList().get(0).getExecutors().size(), is(0));
    }

    @Test
    public void addExecutorJob() {
        BuildStrategy taskListMaker = new TaskListStrategy();
        Job taskmaster1 = new Job(new V1Job().metadata(new V1ObjectMeta().name("tm1")));
        Job taskmaster2 = new Job(new V1Job().metadata(new V1ObjectMeta().name("tm2")));
        Job executor = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything").putLabelsItem(LABEL_TESTASK_ID_KEY, "tm2")));
        taskListMaker.addTaskMasterJob(taskmaster1);
        taskListMaker.addTaskMasterJob(taskmaster2);
        taskListMaker.addExecutorJob(executor);
        assertThat(taskListMaker.getTaskList().stream().
                filter(task -> task.getTaskmaster().getJobName().equals("tm1")).findFirst().get().getExecutors().size(), is(0));
        assertThat(taskListMaker.getTaskList().stream().
                filter(task -> task.getTaskmaster().getJobName().equals("tm2")).findFirst().get().getExecutors().get(0).getJobName(), is("anything"));
    }

    @Test
    public void addOutputFilerJob() {
        BuildStrategy taskListMaker = new TaskListStrategy();
        Job taskmaster1 = new Job(new V1Job().metadata(new V1ObjectMeta().name("tm1")));
        Job taskmaster2 = new Job(new V1Job().metadata(new V1ObjectMeta().name("tm2")));
        Job wrong_filer = new Job(new V1Job().metadata(new V1ObjectMeta().name("tm1-filer-outputs")));
        Job correct_filer = new Job(new V1Job().metadata(new V1ObjectMeta().name("tm2-outputs-filer")));
        taskListMaker.addTaskMasterJob(taskmaster1);
        taskListMaker.addTaskMasterJob(taskmaster2);
        taskListMaker.addOutputFilerJob(wrong_filer);
        taskListMaker.addOutputFilerJob(correct_filer);
        assertThat(taskListMaker.getTaskList().stream().
                filter(task -> task.getTaskmaster().getJobName().equals("tm1")).findFirst().get().getOutputFiler().isPresent(), is(false));
        assertThat(taskListMaker.getTaskList().stream().
                filter(task -> task.getTaskmaster().getJobName().equals("tm2")).findFirst().get().getOutputFiler().isPresent(), is(true));
    }

    @Test(expected = UnsupportedOperationException.class)
    public void getTask_unsupported() {
        BuildStrategy taskListMaker = new TaskListStrategy();
        taskListMaker.getTask();
    }
}