package uk.ac.ebi.tsc.tesk.config;

import com.google.gson.Gson;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Scope;
import io.kubernetes.client.models.V1Job;

import java.io.*;
import java.util.UUID;
import java.util.function.Supplier;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Configuration
public class TaskMasterSupplier {

    @Autowired
    private Gson gson;

    @Bean
    @Scope(value = "prototype")
    public V1Job jobTemplate() {
        try (InputStream inputStream = getClass().getClassLoader().getResourceAsStream("taskmaster.json");
             Reader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            V1Job job = gson.fromJson(reader, V1Job.class);
            job.getMetadata().setName("task-" + UUID.randomUUID());
            return job;
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }


    }

    @Bean
    public Supplier<V1Job> jobTemplateSupplier() {
        return this::jobTemplate;
    }

}
