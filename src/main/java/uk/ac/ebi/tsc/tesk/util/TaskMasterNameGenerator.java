package uk.ac.ebi.tsc.tesk.util;

import com.google.common.base.Strings;
import org.springframework.stereotype.Component;

import java.util.concurrent.ThreadLocalRandom;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Component
public class TaskMasterNameGenerator {

    private static final String TASKMASTER_PREFIX = "task-";

    public String getTaskMasterName() {
        return TASKMASTER_PREFIX + Strings.padStart(String.valueOf(ThreadLocalRandom.current().nextLong(10000)), 4, '0');
    }
}
