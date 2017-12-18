package uk.ac.ebi.tsc.tesk.config;

import com.google.gson.Gson;
import io.kubernetes.client.models.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Scope;
import uk.ac.ebi.tsc.tesk.util.component.JobNameGenerator;
import uk.ac.ebi.tsc.tesk.util.data.Job;

import java.io.*;
import java.util.ArrayList;
import java.util.StringJoiner;
import java.util.function.Supplier;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.*;
import static uk.ac.ebi.tsc.tesk.util.constant.K8sConstants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * Templates for tasmaster's and executor's job object.
 *
 */
@Configuration
public class KubernetesObjectsSupplier {


    private final Gson gson;

    private final JobNameGenerator jobNameGenerator;

    public KubernetesObjectsSupplier(Gson gson, JobNameGenerator jobNameGenerator) {
        this.gson = gson;
        this.jobNameGenerator = jobNameGenerator;
    }

    /**
     * Creates a new empty taskmaster's K8s job object with auto-generated name.
     * Uses JSON file from resources as a template and adds generated name to it.
     * Additionally, places appropriately taskmaster's image name and version from parameters
     * @param imageName - taskmaster's image name
     * @param imageVersion - taskmaster's image name
     * @return - new K8s Job object with auto-generated name.
     */
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
            new Job(job).changeJobName(taskMasterName);
            return job;
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }
    }

    /**
     * Creates a new empty executor's K8s job object (without a name),
     * by initializing required objects in the graph (new new new)
     * and putting constants.
     * @return
     */
    @Bean
    @Scope(value = "prototype")
    public V1Job executorTemplate() {
        V1Container container = new V1Container().
                command(new ArrayList<>()).
                resources(new V1ResourceRequirements());/*.
                addVolumeMountsItem(new V1VolumeMount().
                        readOnly(Boolean.FALSE).
                        name(VOLUME_NAME));*/
        return new V1Job().
                apiVersion(K8S_BATCH_API_VERSION).kind(K8S_BATCH_API_JOB_TYPE).
                metadata(new V1ObjectMeta().
                        putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_EXEC)).
                spec(new V1JobSpec().
                        template(new V1PodTemplateSpec().
                                metadata(new V1ObjectMeta()).
                                spec(new V1PodSpec().
                                        addContainersItem(container).
                                        restartPolicy(JOB_RESTART_POLICY))));/*.
                                        addVolumesItem(new V1Volume().
                                                name(VOLUME_NAME).
                                                persistentVolumeClaim(new V1PersistentVolumeClaimVolumeSource().
                                                        readOnly(Boolean.FALSE))))));*/


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
