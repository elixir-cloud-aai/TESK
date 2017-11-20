package uk.ac.ebi.tsc.tesk.util;

import io.kubernetes.client.models.V1Container;
import io.kubernetes.client.models.V1Job;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import uk.ac.ebi.tsc.tesk.model.TesCreateTaskResponse;
import uk.ac.ebi.tsc.tesk.model.TesExecutor;
import uk.ac.ebi.tsc.tesk.model.TesResources;

import java.util.function.Supplier;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Component
public class TesKubernetesConverter {

    private static final String EXECUTOR_PREFIX = "-ex";

    @Autowired
    @Qualifier("executor")
    private Supplier<V1Job> jobTemplateSupplier;


    public V1Job fromTesExecutorToK8sJob(String generatedTaskId, String tesTaskName, TesExecutor executor, int executorIndex, TesResources resources) {
        V1Job job = jobTemplateSupplier.get();
        job.getMetadata().name(generatedTaskId + EXECUTOR_PREFIX + executorIndex);
        String validName = tesTaskName.toLowerCase().replaceAll("\\s", "-");
        job.getSpec().getTemplate().getMetadata().name(validName);
        V1Container container = job.getSpec().getTemplate().getSpec().getContainers().get(0);
        container.
                name(validName + EXECUTOR_PREFIX + executorIndex).
                image(executor.getImage());
        executor.getCommand().stream().forEach(container::addCommandItem);
        container.getResources().
                putRequestsItem("cpu", resources.getCpuCores().toString()).
                putRequestsItem("memory", resources.getRamGb().toString() + "Gi");
        return job;
    }

    public TesCreateTaskResponse fromK8sJobToTesCreateTaskResponse(V1Job job) {
        return new TesCreateTaskResponse().id(job.getMetadata().getName());
    }


}
