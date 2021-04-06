package uk.ac.ebi.tsc.tesk.k8s.constant;

import io.kubernetes.client.models.V1Job;
import io.kubernetes.client.models.V1ObjectMeta;
import io.kubernetes.client.models.V1Pod;
import uk.ac.ebi.tsc.tesk.tes.model.TesState;

import java.util.EnumSet;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * TESK implementation specific constants
 */
public class Constants {

    /**
     * ENV var that serves as taskmaster script input (JSON format)
     */
    public static final String TASKMASTER_INPUT = "JSON_INPUT";

    /**
     * Key in JSON taskmaster input, which holds list of executors
     */
    public static final String TASKMASTER_INPUT_EXEC_KEY = "executors";

    /**
     *
     */
    public static final String VOLUME_NAME = "PVC";


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
     * Output filer name suffix
     */
    public static final String JOB_NAME_FILER_SUF = "-outputs-filer";

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
     * Key of the label, that holds executor's state
     */
    public static final String LABEL_TASKSTATE_KEY = "task-status";

    /**
     * Value of the label, that holds executor's Cancelled state
     */
    public static final String LABEL_TASKSTATE_VALUE_CANC = "Cancelled";

    /**
     * Key of the label, that holds user id
     */
    public static final String LABEL_USERID_KEY = "creator-user-id";

    /**
     * Key of the label, that holds user's group name
     */
    public static final String LABEL_GROUPNAME_KEY = "creator-group-name";


    /**
     * Pattern to validate paths
     */
    public static final String ABSOLUTE_PATH_REGEXP = "^\\/.*";

    /**
     * Message for absolute path validation (to avoid message.properties)
     */
    public static final String ABSOLUTE_PATH_MESSAGE = "must be an absolute path";

    public static final double RESOURCE_DISK_DEFAULT = 0.1;

    /**
     * TES task states, indicating task is not running and cannot be cancelled
     */
    public static EnumSet<TesState> COMPLETED_STATES = EnumSet.of(TesState.CANCELED, TesState.COMPLETE, TesState.EXECUTOR_ERROR, TesState.SYSTEM_ERROR);

    /**
     * Name of taskmaster's ENV variable with username of FTP account used for storage
     */
    public static final String FTP_SECRET_USERNAME_ENV = "TESK_FTP_USERNAME";
    /**
     * Name of taskmaster's ENV variable with password of FTP account used for storage
     */
    public static final String FTP_SECRET_PASSWORD_ENV = "TESK_FTP_PASSWORD";

    /**
     * Patch object passed to job API, when cancelling task
     */
    public static final V1Job JOB_CANCEL_PATCH = new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_TASKSTATE_KEY, LABEL_TASKSTATE_VALUE_CANC));
    /**
     * Patch object passed to pod API, when cancelling task
     */
    public static final V1Pod POD_CANCEL_PATCH = new V1Pod().metadata(new V1ObjectMeta().putLabelsItem(LABEL_TASKSTATE_KEY, LABEL_TASKSTATE_VALUE_CANC));

}
