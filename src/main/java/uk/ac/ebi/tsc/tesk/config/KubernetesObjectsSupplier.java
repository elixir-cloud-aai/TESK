package uk.ac.ebi.tsc.tesk.config;

import com.google.gson.Gson;
import io.kubernetes.client.models.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Scope;
import uk.ac.ebi.tsc.tesk.util.JobNameGenerator;

import java.io.*;
import java.util.ArrayList;
import java.util.StringJoiner;
import java.util.function.Supplier;

import static uk.ac.ebi.tsc.tesk.util.KubernetesConstants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Configuration
public class KubernetesObjectsSupplier {



    @Autowired
    private Gson gson;

    @Autowired
    private JobNameGenerator jobNameGenerator;

    @Bean
    @Scope(value = "prototype")
    public V1Job taskMasterTemplate(@Value("${tesk.api.taskmaster.image.name}") String imageName, @Value("tesk.api.taskmaster.image.version") String imageVersion) {
        try (InputStream inputStream = getClass().getClassLoader().getResourceAsStream("taskmaster.json");
             Reader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            V1Job job = gson.fromJson(reader, V1Job.class);
            job.getSpec().getTemplate().getSpec().getContainers().get(0).
                    setImage(new StringJoiner(":").add(imageName).add(imageVersion).toString());
            job.getMetadata().putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_TASKM);
            String taskMasterName = this.jobNameGenerator.getTaskMasterName();
            job.getMetadata().setName(taskMasterName);
            job.getSpec().getTemplate().getMetadata().setName(taskMasterName);
            job.getSpec().getTemplate().getSpec().getContainers().get(0).setName(taskMasterName);
            return job;
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }
    }

    @Bean
    @Scope(value = "prototype")
    public V1Job executorTemplate() {
        V1Container container = new V1Container().
                command(new ArrayList<>()).
                resources(new V1ResourceRequirements());
        V1Job job = new V1Job().
                apiVersion(K8S_BATCH_API_VERSION).kind(K8S_BATCH_API_JOB_TYPE).
                metadata(new V1ObjectMeta().
                        putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_EXEC)).
                spec(new V1JobSpec().
                        template(new V1PodTemplateSpec().
                                metadata(new V1ObjectMeta()).
                                spec(new V1PodSpec().
                                        addContainersItem(container).
                                        restartPolicy(JOB_RESTART_POLICY))));
        return job;


    }

    @Bean(name = "taskmaster")
    public Supplier<V1Job> taskMasterSupplier(@Value("${tesk.api.taskmaster.image.name}") String imageName, @Value("${tesk.api.taskmaster.image.version}") String imageVersion) {
        return () -> taskMasterTemplate(imageName, imageVersion);
    }

    @Bean(name = "executor")
    public Supplier<V1Job> executorSupplier() {
        return this::executorTemplate;
    }

}
