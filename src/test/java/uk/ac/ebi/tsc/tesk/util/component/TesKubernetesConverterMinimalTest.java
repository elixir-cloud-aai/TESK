package uk.ac.ebi.tsc.tesk.util.component;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.gson.Gson;
import io.kubernetes.client.models.V1Job;
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
import uk.ac.ebi.tsc.tesk.config.GsonConfig;
import uk.ac.ebi.tsc.tesk.config.KubernetesObjectsSupplier;
import uk.ac.ebi.tsc.tesk.config.TaskmasterEnvProperties;
import uk.ac.ebi.tsc.tesk.config.security.User;
import uk.ac.ebi.tsc.tesk.model.TesTask;
import uk.ac.ebi.tsc.tesk.util.constant.Constants;

import java.io.*;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.mockito.BDDMockito.given;


/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@RunWith(SpringRunner.class)
@JsonTest
@TestPropertySource(locations = {"classpath:application.properties"},
        properties = {"tesk.api.taskmaster.image-name = task-minimal-image-name",
                "tesk.api.taskmaster.image-version = task-minimal-image-version",
                "tesk.api.taskmaster.filer-image-version = task-minimal-filer-image-version",
                "tesk.api.k8s.namespace = test-namespace"})
@EnableConfigurationProperties(TaskmasterEnvProperties.class)
public class TesKubernetesConverterMinimalTest {

    @MockBean
    private JobNameGenerator jobNameGenerator;

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

        this.converter = new TesKubernetesConverter(executorTemplateSupplier, taskmasterTemplateSupplier,
                objectMapper, gson);
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

        assertEquals(outputJob.getMetadata().getLabels().get("job-type"), "taskmaster");
        assertEquals(outputJob.getMetadata().getLabels().get("creator-user-id"), "test-user-id");
        assertEquals(outputJob.getMetadata().getLabels().get("creator-group-name"), "ABC");

        assertEquals(outputJob.getSpec().getTemplate().getSpec().getContainers().get(0).getArgs().get(0), "$(JSON_INPUT)");

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
}
