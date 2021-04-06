package uk.ac.ebi.tsc.tesk.k8s.convert.data;

import com.google.common.collect.Lists;
import io.kubernetes.client.models.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.MockitoJUnitRunner;

import java.util.List;
import java.util.stream.Collectors;

import static org.hamcrest.Matchers.*;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.*;

@RunWith(MockitoJUnitRunner.class)
public class TaskBuilderTest {

    @Mock
    private BuildStrategy buildStrategy;

    @Test
    public void addJob_taskmaster() {
        TaskBuilder taskBuilder = new TaskBuilder(buildStrategy);
        V1Job taskmaster = new V1Job().metadata(new V1ObjectMeta().name("task_123").putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_TASKM));
        ArgumentCaptor<Job> argument = ArgumentCaptor.forClass(Job.class);
        taskBuilder.addJob(taskmaster);
        verify(buildStrategy).addTaskMasterJob(argument.capture());
        Job jobPassedToStrategy = argument.getValue();
        assertThat(jobPassedToStrategy.getJob(), is(taskmaster));
        assertThat(taskBuilder.getAllJobsByName().keySet(), contains("task_123"));
        assertSame(taskBuilder.getAllJobsByName().get("task_123"), jobPassedToStrategy);
    }

    @Test
    public void addJob_taskmaster_more() {
        TaskBuilder taskBuilder = new TaskBuilder(buildStrategy);
        V1Job taskmaster = new V1Job().metadata(new V1ObjectMeta().name("task_123").putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_TASKM));
        V1Job taskmaster2 = new V1Job().metadata(new V1ObjectMeta().name("task_124").putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_TASKM));
        taskBuilder.addJob(taskmaster);
        taskBuilder.addJob(taskmaster2);
        assertThat(taskBuilder.getAllJobsByName().values().stream().map(Job::getJob).collect(Collectors.toSet()), containsInAnyOrder(taskmaster, taskmaster2));
    }

    @Test
    public void addJob_executor() {
        TaskBuilder taskBuilder = new TaskBuilder(buildStrategy);
        V1Job executor = new V1Job().metadata(new V1ObjectMeta().name("task_123").putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_EXEC));
        ArgumentCaptor<Job> argument = ArgumentCaptor.forClass(Job.class);
        taskBuilder.addJob(executor);
        verify(buildStrategy).addExecutorJob(argument.capture());
        Job jobPassedToStrategy = argument.getValue();
        assertThat(jobPassedToStrategy.getJob(), is(executor));
        assertThat(taskBuilder.getAllJobsByName().keySet(), contains("task_123"));
        assertSame(taskBuilder.getAllJobsByName().get("task_123"), jobPassedToStrategy);
    }

    @Test
    public void addJob_anything_works_as_filer() {
        TaskBuilder taskBuilder = new TaskBuilder(buildStrategy);
        V1Job anything = new V1Job().metadata(new V1ObjectMeta().name("task_123").putLabelsItem("anything", ""));
        ArgumentCaptor<Job> argument = ArgumentCaptor.forClass(Job.class);
        taskBuilder.addJob(anything);
        verify(buildStrategy).addOutputFilerJob(argument.capture());
        Job jobPassedToStrategy = argument.getValue();
        assertThat(jobPassedToStrategy.getJob(), is(anything));
        assertThat(taskBuilder.getAllJobsByName().keySet(), contains("task_123"));
        assertSame(taskBuilder.getAllJobsByName().get("task_123"), jobPassedToStrategy);
    }

    @Test
    public void addJobList() {
        TaskBuilder taskBuilder = new TaskBuilder(buildStrategy);
        V1Job taskmaster = new V1Job().metadata(new V1ObjectMeta().name("task_123").putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_TASKM));
        V1Job taskmaster2 = new V1Job().metadata(new V1ObjectMeta().name("task_223").putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_TASKM));
        V1Job executor = new V1Job().metadata(new V1ObjectMeta().name("task_124").putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_EXEC));
        V1Job anything = new V1Job().metadata(new V1ObjectMeta().name("task_125").putLabelsItem("anything", ""));
        taskBuilder.addJobList(Lists.newArrayList(taskmaster, taskmaster2, executor, anything));
        verify(buildStrategy, times(2)).addTaskMasterJob(any());
        verify(buildStrategy).addOutputFilerJob(any());
        verify(buildStrategy).addExecutorJob(any());
        assertThat(taskBuilder.getAllJobsByName().keySet().size(), is(4));
    }

    @Test
    public void addPodList() {
        TaskBuilder taskBuilder = new TaskBuilder(buildStrategy);
        V1Job anything = new V1Job().metadata(new V1ObjectMeta().name("task_125").putLabelsItem("anything", "")).spec(new V1JobSpec().selector(new V1LabelSelector().putMatchLabelsItem("A", "1").putMatchLabelsItem("B", "2")));
        V1Pod matching1 = new V1Pod().metadata(new V1ObjectMeta().putLabelsItem("B", "2").putLabelsItem("A", "1"));
        V1Pod matching2 = new V1Pod().metadata(new V1ObjectMeta().putLabelsItem("B", "2").putLabelsItem("A", "1").putLabelsItem("c", "2"));
        V1Pod unmatching1 = new V1Pod().metadata(new V1ObjectMeta().putLabelsItem("B", "2"));
        V1Pod unmatching2 = new V1Pod().metadata(new V1ObjectMeta().putLabelsItem("B", "1").putLabelsItem("A", "2"));
        taskBuilder.addJob(anything);
        taskBuilder.addPodList(Lists.newArrayList(matching1, matching2, unmatching1, unmatching2));
        assertThat(taskBuilder.getAllJobsByName().get("task_125").getPods().size(), is(2));
        assertThat(taskBuilder.getAllJobsByName().get("task_125").getPods(), containsInAnyOrder(matching1, matching2));
    }

    @Test
    public void getTask() {
        given(buildStrategy.getTask()).willReturn(new Task("123"));
        TaskBuilder taskBuilder = new TaskBuilder(buildStrategy);
        assertThat(taskBuilder.getTask().getTaskmaster().getJobName(), is("123"));
    }

    @Test
    public void getTaskList() {
        List<Task> tasks = Lists.newArrayList(new Task("123"), new Task("124"));
        given(buildStrategy.getTaskList()).willReturn(tasks);
        TaskBuilder taskBuilder = new TaskBuilder(buildStrategy);
        assertThat(taskBuilder.getTaskList().stream().map(task -> task.getTaskmaster().getJobName()).collect(Collectors.toSet()), containsInAnyOrder("123", "124"));

    }
}