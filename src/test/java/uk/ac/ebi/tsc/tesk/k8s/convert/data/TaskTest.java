package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1ObjectMeta;
import org.junit.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.hamcrest.CoreMatchers.is;
import static org.hamcrest.collection.IsEmptyCollection.empty;
import static org.junit.Assert.assertThat;

public class TaskTest {

    private List<Job> prepareExecutors() {
        List<Job> list = new ArrayList<>();
        list.add(new Job(new V1Job().metadata(new V1ObjectMeta().name("123-ex-115"))));
        list.add(new Job(new V1Job().metadata(new V1ObjectMeta().name("123-ex-02"))));
        list.add(new Job(new V1Job().metadata(new V1ObjectMeta().name("123-ex-01"))));
        list.add(new Job(new V1Job().metadata(new V1ObjectMeta().name("123-ex-12"))));
        return list;
    }

    @Test
    public void getExecutors() {
        Task task = new Task("123");
        for (Job exec : prepareExecutors()) {
            task.addExecutor(exec);
        }
        List<Job> executors = task.getExecutors();
        assertThat(executors.get(0).getJobName(), is("123-ex-01"));
        assertThat(executors.get(1).getJobName(), is("123-ex-02"));
        assertThat(executors.get(2).getJobName(), is("123-ex-12"));
        assertThat(executors.get(3).getJobName(), is("123-ex-115"));
    }

    @Test
    public void getExecutors_no() {
        Task task = new Task("123");
        assertThat(task.getExecutors(), empty());
    }

    @Test
    public void getLastExecutor() {
        Task task = new Task("123");
        for (Job exec : prepareExecutors()) {
            task.addExecutor(exec);
        }
        assertThat(task.getLastExecutor().get().getJobName(), is("123-ex-115"));
    }

    @Test
    public void getLastExecutor_no() {
        Task task = new Task("123");
        assertThat(task.getLastExecutor(), is(Optional.empty()));
    }

    @Test
    public void getExecutorName() {
        Task task = new Task("123");
        assertThat(task.getExecutorName(5), is("123-ex-05"));
        assertThat(task.getExecutorName(125), is("123-ex-125"));
    }
}