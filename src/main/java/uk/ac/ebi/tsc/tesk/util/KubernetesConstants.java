package uk.ac.ebi.tsc.tesk.util;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
public class KubernetesConstants {

    /**
     * ENV var that serves as taskmaster script input (JSON format)
     */
    public static final String TASKMASTER_INPUT = "JSON_INPUT";

    /**
     * Key in JSON taskmaster input, which holds list of executors
     */
    public static final String TASKMASTER_INPUT_EXEC_KEY = "executors";

    public static final String K8S_BATCH_API_VERSION = "batch/v1";

    /**
     * Kubernetes Job object type
     */
    public static final String K8S_BATCH_API_JOB_TYPE = "Job";


    public static final String JOB_RESTART_POLICY = "Never";

    /**
     *
     */
    public static final String VOLUME_NAME = "PVC";

    /**
     * Name of a default K8s namespace
     */
    public static final String DEFAULT_NAMESPACE = "default";

    /**
     * Number of attempts of job creation in case of name collision
     */
    public static final int JOB_CREATE_ATTEMPTS_NO = 5;

    /**
     * Constant prefix of taskmaster's job name (== TES task ID)
     */
    public static final String JOB_NAME_TASKM_PREFIX = "task-";
    /**
     * Part of executor's job name, that follows taskmaster's name
     */
    public static final String JOB_NAME_EXEC_PREFIX = "-ex-";
    /**
     * No of bytes of random part of task master's name (which end up encoded to hex)
     */
    public static final int JOB_NAME_TASKM_RAND_PART_LENGTH = 4;
    /**
     * No of digits reserved for executor number in executor's job name. Ends up padded with '0' for numbers < 10
     */
    public static final int JOB_NAME_EXEC_NO_LENGTH = 2;

    /**
     * Key of the annotation, that stores name of TES task in both taskmaster's job and executor's jobs.
     */
    public static final String ANN_TESTASK_NAME_KEY = "tes-task-name";

    /**
     * Key of the annotation, that stores whole input TES task serialized to JSON
     */
    public static final String ANN_JSON_INPUT_KEY = "json-input";

    /**
     * Key of the label, that stores taskmaster's name (==TES task generated ID) in executor jobs
     */
    public static final String LABEL_TESTASK_ID_KEY = "taskmaster-name";

    /**
     * Key of the label, that stores type of a job (taskmaster or executor)
     */
    public static final String LABEL_JOBTYPE_KEY = "job-type";

    /**
     * Value of the label with taskmaster's job type
     */
    public static final String LABEL_JOBTYPE_VALUE_TASKM = "taskmaster";

    /**
     * Value of the label with executor's job type
     */
    public static final String LABEL_JOBTYPE_VALUE_EXEC = "executor";

    /**
     * Key of the label, that holds executor number for executor jobs
     */
    public static final String LABEL_EXECNO_KEY = "executor-no";
    /**
     * Executor CPU resource label
     */
    public static final String RESOURCE_CPU_KEY = "cpu";
    /**
     * Executor memory resource label
     */
    public static final String RESOURCE_MEM_KEY = "memory";
    /**
     * Executor memory resource unit
     */
    public static final String RESOURCE_MEM_UNIT = "Gi";

    /**
     * Pattern to validate paths
     */
    public static final String ABSOLUTE_PATH_REGEXP = "^\\/.*";

    /**
     * Message for absolute path validation (to avoid message.properties)
     */
    public static final String ABSOLUTE_PATH_MESSAGE = "must be an absolute path";
}
