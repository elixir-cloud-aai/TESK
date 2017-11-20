package uk.ac.ebi.tsc.tesk.service;

import com.google.gson.Gson;
import io.kubernetes.client.ApiException;
import io.kubernetes.client.apis.BatchV1Api;
import io.kubernetes.client.models.V1Job;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import uk.ac.ebi.tsc.tesk.exception.KubernetesException;
import uk.ac.ebi.tsc.tesk.model.TesCreateTaskResponse;
import uk.ac.ebi.tsc.tesk.model.TesTask;
import uk.ac.ebi.tsc.tesk.util.TaskMasterNameGenerator;
import uk.ac.ebi.tsc.tesk.util.TesKubernetesConverter;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Supplier;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Service
public class TesService {

    private static final int JOB_CREATE_ATTEMPTS_NO = 5;

    private static final String DEFAULT_NAMESPACE = "default";

    private static final String TASKMASTER_INPUT = "JSON_INPUT";

    @Autowired
    private Gson gson;

    @Autowired
    private BatchV1Api batchV1Api;

    @Autowired
    @Qualifier("taskmaster")
    private Supplier<V1Job> jobTemplateSupplier;

    @Autowired
    private TesKubernetesConverter converter;

    @Autowired
    private TaskMasterNameGenerator nameGenerator;

    public TesCreateTaskResponse createTask(TesTask task) {

        V1Job job = this.jobTemplateSupplier.get();
        List<V1Job> executorsAsJobs = IntStream.range(0, task.getExecutors().size()).
                mapToObj(i -> this.converter.fromTesExecutorToK8sJob(job.getMetadata().getName(), task.getName(), task.getExecutors().get(i), i, task.getResources())).
                collect(Collectors.toList());
        Map<String, List<V1Job>> taskMasterInput = new HashMap<>();
        taskMasterInput.put("executors", executorsAsJobs);
        String taskMasterInputAsJSON = this.gson.toJson(taskMasterInput);
        job.getSpec().getTemplate().getSpec().getContainers().get(0).getEnv().stream().filter(x -> x.getName().equals(TASKMASTER_INPUT)).forEach(x -> x.setValue(taskMasterInputAsJSON));
        int attemptsNo = 0;
        while (true) {
            try {
                V1Job createdJob = this.batchV1Api.createNamespacedJob(DEFAULT_NAMESPACE, job, null);
                return this.converter.fromK8sJobToTesCreateTaskResponse(createdJob);
            } catch (ApiException e) {
                if (e.getCode() != HttpStatus.CONFLICT.value() || ++attemptsNo >= JOB_CREATE_ATTEMPTS_NO) {
                    throw KubernetesException.fromApiException(e);
                }
                job.getMetadata().setName(this.nameGenerator.getTaskMasterName());
            }
        }
    }
}
