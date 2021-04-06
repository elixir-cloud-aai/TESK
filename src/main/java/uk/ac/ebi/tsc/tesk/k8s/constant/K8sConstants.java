package uk.ac.ebi.tsc.tesk.k8s.constant;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * Kubernetes specific constants (parts of K8s API)
 */
public class K8sConstants {

    public enum PodPhase {
        PENDING("Pending");
        private String code;

        PodPhase(String code) {
            this.code = code;
        }

        public String getCode() {
            return code;
        }
    }

    public static final String K8S_BATCH_API_VERSION = "batch/v1";

    /**
     * Kubernetes Job object type
     */
    public static final String K8S_BATCH_API_JOB_TYPE = "Job";


    public static final String JOB_RESTART_POLICY = "Never";

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
    public static final String RESOURCE_MEM_UNIT = "G";


}
