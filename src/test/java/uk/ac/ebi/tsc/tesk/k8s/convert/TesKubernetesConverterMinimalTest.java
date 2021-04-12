package uk.ac.ebi.tsc.tesk.k8s.convert;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.gson.Gson;
import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1JobStatus;
import io.kubernetes.client.models.V1ObjectMeta;
import io.kubernetes.client.models.V1PodList;
import org.hamcrest.CoreMatchers;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.skyscreamer.jsonassert.JSONCompareMode;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.boot.test.autoconfigure.json.JsonTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.json.JsonContentAssert;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Import;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.util.StringUtils;
import uk.ac.ebi.tsc.tesk.TestUtils;
import uk.ac.ebi.tsc.tesk.config.GsonConfig;
import uk.ac.ebi.tsc.tesk.config.security.User;
import uk.ac.ebi.tsc.tesk.k8s.constant.Constants;
import uk.ac.ebi.tsc.tesk.k8s.constant.K8sConstants;
import uk.ac.ebi.tsc.tesk.k8s.convert.data.TaskBuilder;
import uk.ac.ebi.tsc.tesk.tes.model.TesState;
import uk.ac.ebi.tsc.tesk.tes.model.TesTask;
import uk.ac.ebi.tsc.tesk.trs.TrsToolClient;

import java.io.*;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertThat;
import static org.mockito.AdditionalAnswers.returnsFirstArg;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.LABEL_TASKSTATE_KEY;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.LABEL_TASKSTATE_VALUE_CANC;


/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@RunWith(SpringRunner.class)
@JsonTest
@TestPropertySource(locations = {"classpath:application.properties"})
@EnableConfigurationProperties(TaskmasterEnvProperties.class)
public class TesKubernetesConverterMinimalTest {

    @MockBean
    private JobNameGenerator jobNameGenerator;

    private TrsToolClient trsToolClient;

    @TestConfiguration
    @Import({KubernetesObjectsSupplier.class, GsonConfig.class})
    static class Configuration {
    }

    @Autowired
    @Qualifier("executor")
    Supplier<V1Job> executorTemplateSupplier;

    @Autowired
    @Qualifier("taskmaster")
    Supplier<V1Job> taskmasterTemplateSupplier;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private Gson gson;


    private TesKubernetesConverter converter;

    @Before
    public void setUpConverter() {
        trsToolClient = mock(TrsToolClient.class);
        when(trsToolClient.getDockerImageForToolVersionURI(anyString())).then(returnsFirstArg());
        this.converter = new TesKubernetesConverter(executorTemplateSupplier, taskmasterTemplateSupplier,
                objectMapper, gson, trsToolClient);
    }

    @Test
    public void fromTesTaskToK8sJob_minimal() throws IOException {

        given(this.jobNameGenerator.getTaskMasterName()).willReturn("task-98605447");

        Resource inputTaskFile = new ClassPathResource("fromTesToK8s_minimal/task.json");
        TesTask inputTask;
        try (InputStream inputStream = inputTaskFile.getInputStream();
             Reader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            inputTask = this.objectMapper.readValue(reader, TesTask.class);
        }
        V1Job outputJob = this.converter.fromTesTaskToK8sJob(inputTask, User.builder("test-user-id").teskMemberedGroups(StringUtils.commaDelimitedListToSet("ABC")).build());
        assertNull(outputJob.getMetadata().getAnnotations().get("tes-task-name"));
        //testing annotation with entire serialized task content..
        assertThat(outputJob.getMetadata().getAnnotations().get("json-input")).isNotEmpty();
        //..comparing jsons
        JsonContentAssert annotationWithEntireTask = new JsonContentAssert(this.getClass(), outputJob.getMetadata().getAnnotations().get("json-input"));
        annotationWithEntireTask.isEqualToJson(inputTaskFile);

        //..and one example path
        annotationWithEntireTask.extractingJsonPathArrayValue("@.executors[0].command").startsWith("echo");

        assertThat(outputJob.getMetadata().getLabels().get("job-type"), is("taskmaster"));
        assertThat(outputJob.getMetadata().getLabels().get("creator-user-id"), is("test-user-id"));
        assertThat(outputJob.getMetadata().getLabels().get("creator-group-name"), is("ABC"));

        assertThat(outputJob.getSpec().getTemplate().getSpec().getContainers().get(0).getArgs().get(0), is("$(JSON_INPUT)"));

        JsonContentAssert taskMasterInputJson = new JsonContentAssert(this.getClass(), outputJob.getSpec().getTemplate().getSpec().
                getContainers().get(0).getEnv().stream().filter(env -> env.getName().equals("JSON_INPUT")).findAny().get().getValue());
        taskMasterInputJson.hasJsonPathValue("outputs");
        taskMasterInputJson.extractingJsonPathNumberValue("outputs.size()").isEqualTo(0);
        taskMasterInputJson.extractingJsonPathNumberValue("inputs.size()").isEqualTo(0);
        taskMasterInputJson.extractingJsonPathNumberValue("volumes.size()").isEqualTo(0);
        taskMasterInputJson.extractingJsonPathMapValue("executors[0].metadata.annotations").isEmpty();
        taskMasterInputJson.extractingJsonPathArrayValue("executors[*].metadata.labels['job-type']").containsOnly("executor").hasSize(1);
        taskMasterInputJson.extractingJsonPathArrayValue("executors[*].metadata.labels['taskmaster-name']").containsOnly("task-98605447").hasSize(1);

        taskMasterInputJson.extractingJsonPathArrayValue("executors[*].spec.template.spec.restartPolicy").containsOnly("Never").hasSize(1);
        taskMasterInputJson.extractingJsonPathMapValue("executors[0].spec.template.spec.containers[0].resources").isEmpty();

        taskMasterInputJson.extractingJsonPathArrayValue("executors[0].spec.template.spec.containers[0].command").containsExactly("echo", "hello world");
        taskMasterInputJson.extractingJsonPathStringValue("executors[0].spec.template.spec.containers[0].image").isEqualTo("ubuntu");

        taskMasterInputJson.extractingJsonPathMapValue("executors[0].spec.template.spec.containers[0]").containsOnlyKeys("name", "image", "command", "resources");

        taskMasterInputJson.extractingJsonPathNumberValue("resources.disk_gb").isEqualTo(0.1);

        taskMasterInputJson.isEqualToJson(new ClassPathResource("fromTesToK8s_minimal/taskmaster_param.json"), JSONCompareMode.NON_EXTENSIBLE);

        Resource outputJobFile = new ClassPathResource("fromTesToK8s_minimal/job.json");
        V1Job expectedJob;
        try (InputStream inputStream = outputJobFile.getInputStream();
             Reader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            expectedJob = this.gson.fromJson(reader, V1Job.class);
        }
        expectedJob.getMetadata().setAnnotations(null);
        outputJob.getMetadata().setAnnotations(null);
        expectedJob.getSpec().getTemplate().getSpec().getContainers().get(0).getEnv().stream().filter(env -> env.getName().equals(Constants.TASKMASTER_INPUT)).forEach(env -> env.setValue(""));
        outputJob.getSpec().getTemplate().getSpec().getContainers().get(0).getEnv().stream().filter(env -> env.getName().equals(Constants.TASKMASTER_INPUT)).forEach(env -> env.setValue(""));
        //comparing fields of resulting Job object and pattern Job objects other those with JSON values, which were cleared in previous lines (JSON strings do not have to be exactly equal to pattern).
        assertEquals(expectedJob, outputJob);
    }

    private TaskBuilder prepareBaseTaskBuider(boolean withExecutors, boolean withPods) throws IOException {
        TaskBuilder taskBuilder = TaskBuilder.newSingleTask();
        taskBuilder.addJob(this.gson.fromJson(TestUtils.getFileContentFromResources("fromK8sToTes_minimal/taskmaster.json"), V1Job.class));
        if (withExecutors) {
            taskBuilder.addJob(this.gson.fromJson(TestUtils.getFileContentFromResources("fromK8sToTes_minimal/executor_00.json"), V1Job.class));
            taskBuilder.addJob(this.gson.fromJson(TestUtils.getFileContentFromResources("fromK8sToTes_minimal/executor_01.json"), V1Job.class));
        }
        if (withPods) {
            taskBuilder.addPodList(this.gson.fromJson(TestUtils.getFileContentFromResources("fromK8sToTes_minimal/taskmaster_pods.json"), V1PodList.class).getItems());
            taskBuilder.addPodList(this.gson.fromJson(TestUtils.getFileContentFromResources("fromK8sToTes_minimal/executor_pods.json"), V1PodList.class).getItems());
        }
        return taskBuilder;
    }

    private TesTask prepareBaseExpectedTask() throws IOException {
        return this.objectMapper.readValue(TestUtils.getFileContentFromResources("fromK8sToTes_minimal/task.json"), TesTask.class);
    }

    @Test
    public void fromK8sToTask_complete() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(true, false);
        taskBuilder.getTask().getTaskmaster().getJob().getStatus().succeeded(1);
        taskBuilder.getTask().getLastExecutor().get().getJob().getStatus().succeeded(1);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.COMPLETE);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_list() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(true, false);
        taskBuilder.getTask().getTaskmaster().getJob().getStatus().succeeded(1);
        taskBuilder.getTask().getLastExecutor().get().getJob().getStatus().succeeded(1);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.COMPLETE);
        expectedTask.setLogs(null);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), true);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_cancelled() throws IOException {
        //only taskmaster job matters
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(false, false);
        taskBuilder.getTask().getTaskmaster().getJob().getMetadata().getLabels().putIfAbsent(LABEL_TASKSTATE_KEY, LABEL_TASKSTATE_VALUE_CANC);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.CANCELED);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_running() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(true, false);
        taskBuilder.getTask().getTaskmaster().getJob().getStatus().active(1);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.RUNNING);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_queued_taskmaster() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(false, true);
        taskBuilder.getTask().getTaskmaster().getFirstPod().getStatus().setPhase(K8sConstants.PodPhase.PENDING.getCode());
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.QUEUED);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_queued_executor() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(true, true);
        taskBuilder.getTask().getLastExecutor().get().getFirstPod().getStatus().setPhase(K8sConstants.PodPhase.PENDING.getCode());
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.QUEUED);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_system_error_no_state() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(false, false);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.SYSTEM_ERROR);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_system_error_no_executors() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(false, false);
        taskBuilder.getTask().getTaskmaster().getJob().getStatus().succeeded(1);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.SYSTEM_ERROR);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_system_error_mismatch() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(true, false);
        taskBuilder.getTask().getTaskmaster().getJob().getStatus().succeeded(1);
        taskBuilder.getTask().getLastExecutor().get().getJob().getStatus().active(1);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.SYSTEM_ERROR);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_system_error_filer() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(true, false)
        .addJob(new V1Job().metadata(new V1ObjectMeta().putLabelsItem("aa", "vv")).status(new V1JobStatus().failed(2)));
        taskBuilder.getTask().getTaskmaster().getJob().getStatus().succeeded(1);
        taskBuilder.getTask().getLastExecutor().get().getJob().getStatus().succeeded(1);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.SYSTEM_ERROR);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_executor_error() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(true, false);
        taskBuilder.getTask().getTaskmaster().getJob().getStatus().succeeded(1);
        taskBuilder.getTask().getLastExecutor().get().getJob().getStatus().failed(1);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.EXECUTOR_ERROR);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }

    @Test
    public void fromK8sToTask_initializing() throws IOException {
        TaskBuilder taskBuilder = this.prepareBaseTaskBuider(false, false);
        taskBuilder.getTask().getTaskmaster().getJob().getStatus().active(1);
        TesTask expectedTask = this.prepareBaseExpectedTask();
        expectedTask.setState(TesState.INITIALIZING);
        TesTask outputTask = this.converter.fromK8sJobsToTesTaskMinimal(taskBuilder.getTask(), false);
        assertThat(outputTask, CoreMatchers.is(expectedTask));
    }


}
