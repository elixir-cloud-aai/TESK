package uk.ac.ebi.tsc.tesk.k8s.convert;

import com.google.gson.Gson;
import io.kubernetes.client.openapi.models.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Scope;
import uk.ac.ebi.tsc.tesk.k8s.convert.data.Job;

import java.io.*;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.StringJoiner;
import java.util.function.Supplier;
import java.util.stream.Collectors;

import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.*;
import static uk.ac.ebi.tsc.tesk.k8s.constant.K8sConstants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Templates for tasmaster's and executor's job object.
 */
@Configuration
public class KubernetesObjectsSupplier {


    private final Gson gson;

    private final JobNameGenerator jobNameGenerator;

    private final TaskmasterEnvProperties taskmasterEnvProperties;

    private final String namespace;

    public KubernetesObjectsSupplier(Gson gson, JobNameGenerator jobNameGenerator,
                                     TaskmasterEnvProperties taskmasterEnvProperties, @Value("${tesk.api.k8s.namespace}") String namespace) {
        this.gson = gson;
        this.jobNameGenerator = jobNameGenerator;
        this.taskmasterEnvProperties = taskmasterEnvProperties;
        this.namespace = namespace;
    }

    /**
     * Creates a new empty taskmaster's K8s job object with auto-generated name.
     * Uses JSON file from resources as a template and adds generated name to it.
     * Additionally, places appropriately taskmaster's image name and version from parameters
     *
     * @return - new K8s Job object with auto-generated name.
     */
    @Bean
    @Scope(value = "prototype")
    public V1Job taskMasterTemplate() {
        try (InputStream inputStream = getClass().getClassLoader().getResourceAsStream("taskmaster.json");
             Reader reader = new BufferedReader(new InputStreamReader(inputStream))) {
            V1Job job = gson.fromJson(reader, V1Job.class);
            job.getSpec().getTemplate().getSpec().setServiceAccountName(this.taskmasterEnvProperties.getServiceAccountName());
            V1Container taskmasterContainer = job.getSpec().getTemplate().getSpec().getContainers().get(0).
                    image(new StringJoiner(":").add(taskmasterEnvProperties.getImageName()).add(taskmasterEnvProperties.getImageVersion()).toString())
                    .addArgsItem("-n").addArgsItem(namespace)
                    .addArgsItem("-fn").addArgsItem(this.taskmasterEnvProperties.getFilerImageName())
                    .addArgsItem("-fv").addArgsItem(this.taskmasterEnvProperties.getFilerImageVersion());


            if (this.taskmasterEnvProperties.isDebug()) {
                taskmasterContainer.addArgsItem("-d")
                        .setImagePullPolicy("Always");
            }
            job.getMetadata().putLabelsItem(LABEL_JOBTYPE_KEY, LABEL_JOBTYPE_VALUE_TASKM);
            String taskMasterName = this.jobNameGenerator.getTaskMasterName();
            new Job(job).changeJobName(taskMasterName);
            Set<V1EnvVar> toBeRemoved = new HashSet<>();
            List<V1EnvVar> containerEnvironment = job.getSpec().getTemplate().getSpec().getContainers().get(0).getEnv();
            containerEnvironment.addAll(taskmasterEnvProperties.getEnvironment().entrySet().stream().map(e -> new V1EnvVar().name(e.getKey().toUpperCase().replaceAll("\\.", "_")).value(e.getValue())).collect(Collectors.toList()));
            containerEnvironment.stream().filter(env -> FTP_SECRET_USERNAME_ENV.equals(env.getName()) || FTP_SECRET_PASSWORD_ENV.equals(env.getName()))
                    .forEach(env -> {
                        if (taskmasterEnvProperties.isFTPEnabled()) {
                            //update secret name, if FTP enabled
                            env.getValueFrom().getSecretKeyRef().setName(this.taskmasterEnvProperties.getFtp().getSecretName());
                        } else {
                            //remove FTP secrets otherwise
                            toBeRemoved.add(env);
                        }
                    });

            toBeRemoved.stream().forEach(containerEnvironment::remove);
            return job;
        } catch (IOException ex) {
            throw new RuntimeException(ex);
        }
    }

    /**
     * Creates a new empty executor's K8s job object (without a name),
     * by initializing required objects in the graph (new new new)
     * and putting constants.
     *
     * @return
     */
    @Bean
    @Scope(value = "prototype")
    public V1Job executorTemplate() {
        V1Container container = new V1Container().
                resources(new V1ResourceRequirements());
        if (this.taskmasterEnvProperties.isExecutorSecretEnabled()) {
            container.addVolumeMountsItem(new V1VolumeMount().
                    readOnly(Boolean.TRUE).
                    name(this.taskmasterEnvProperties.getExecutorSecret().getName()).
                    mountPath(this.taskmasterEnvProperties.getExecutorSecret().getMountPath()));
        }

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
        if (this.taskmasterEnvProperties.isExecutorSecretEnabled()) {
            job.getSpec().getTemplate().getSpec().
                    addVolumesItem(new V1Volume().
                            name(this.taskmasterEnvProperties.getExecutorSecret().getName()).
                            secret(new V1SecretVolumeSource().secretName(this.taskmasterEnvProperties.getExecutorSecret().getName())));
        }
        return job;

    }

    @Bean(name = "taskmaster")
    public Supplier<V1Job> taskMasterSupplier() {
        return () -> taskMasterTemplate();
    }

    @Bean(name = "executor")
    public Supplier<V1Job> executorSupplier() {
        return this::executorTemplate;
    }

}
