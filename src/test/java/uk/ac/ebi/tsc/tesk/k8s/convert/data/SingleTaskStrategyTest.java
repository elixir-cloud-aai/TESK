package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1ObjectMeta;
import org.junit.Test;

import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.CoreMatchers.nullValue;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertThat;

public class SingleTaskStrategyTest {

    @Test
    public void addTaskMasterJob() {
        BuildStrategy taskMaker = new SingleTaskStrategy();
        Job job = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything")));
        taskMaker.addTaskMasterJob(job);
        assertSame(taskMaker.getTask().getTaskmaster(), job);
        assertThat(taskMaker.getTask().getTaskmaster().getJobName(), is("anything"));
    }

    @Test
    public void addExecutorJob_no_taskmaster() {
        BuildStrategy taskMaker = new SingleTaskStrategy();
        Job job = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything")));
        taskMaker.addExecutorJob(job);
        assertThat(taskMaker.getTask(), is(nullValue()));
    }

    @Test
    public void addExecutorJob() {
        BuildStrategy taskMaker = new SingleTaskStrategy();
        Job taskmaster = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything1")));
        Job exec = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything2")));
        taskMaker.addTaskMasterJob(taskmaster);
        taskMaker.addExecutorJob(exec);
        assertSame(taskMaker.getTask().getExecutors().get(0), exec);
        assertThat(taskMaker.getTask().getExecutors().get(0).getJobName(), is("anything2"));
    }

    @Test
    public void addOutputFilerJob_no_taskmaster() {
        BuildStrategy taskMaker = new SingleTaskStrategy();
        Job job = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything")));
        taskMaker.addOutputFilerJob(job);
        assertThat(taskMaker.getTask(), is(nullValue()));
    }

    @Test
    public void addOutputFilerJob() {
        BuildStrategy taskMaker = new SingleTaskStrategy();
        Job taskmaster = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything1")));
        Job output = new Job(new V1Job().metadata(new V1ObjectMeta().name("anything2")));
        taskMaker.addTaskMasterJob(taskmaster);
        taskMaker.addOutputFilerJob(output);
        assertSame(taskMaker.getTask().getOutputFiler().get(), output);
        assertThat(taskMaker.getTask().getOutputFiler().get().getJobName(), is("anything2"));
    }

}