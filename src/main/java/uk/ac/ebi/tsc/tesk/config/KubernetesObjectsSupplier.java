package uk.ac.ebi.tsc.tesk.config;

import com.google.gson.Gson;
import io.kubernetes.client.models.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Scope;
import uk.ac.ebi.tsc.tesk.util.TaskMasterNameGenerator;

import java.io.*;
import java.util.ArrayList;
import java.util.function.Supplier;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Configuration
public class KubernetesObjectsSupplier {


    @Autowired
    private Gson gson;

    @Autowired
    private TaskMasterNameGenerator taskMasterNameGenerator;

    @Bean
    @Scope(value = "prototype")
    public V1Job taskMasterTemplate() {
        try (InputStream inputStream = getClass().getClassLoader().getResourceAsStream("taskmaster.json");
             Reader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            V1Job job = gson.fromJson(reader, V1Job.class);
            job.getMetadata().setName(this.taskMasterNameGenerator.getTaskMasterName());
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
                apiVersion("batch/v1").kind("Job").
                metadata(new V1ObjectMeta()).
                spec(new V1JobSpec().
                        template(new V1PodTemplateSpec().
                                metadata(new V1ObjectMeta()).
                                spec(new V1PodSpec().
                                        addContainersItem(container).
                                        restartPolicy("Never"))));
        return job;


    }

    @Bean(name = "taskmaster")
    public Supplier<V1Job> taskMasterSupplier() {
        return this::taskMasterTemplate;
    }

    @Bean(name = "executor")
    public Supplier<V1Job> executorSupplier() {
        return this::executorTemplate;
    }

}
