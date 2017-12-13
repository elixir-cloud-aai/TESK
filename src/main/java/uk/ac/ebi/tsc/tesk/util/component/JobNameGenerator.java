package uk.ac.ebi.tsc.tesk.util.component;

import com.google.common.base.Strings;
import org.springframework.stereotype.Component;

import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static uk.ac.ebi.tsc.tesk.util.constant.Constants.*;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@Component
public class JobNameGenerator {

    public String getTaskMasterName() {
        byte[] buffer = new byte[JOB_NAME_TASKM_RAND_PART_LENGTH];
        ThreadLocalRandom.current().nextBytes(buffer);
        String rand = IntStream.range(0, buffer.length).mapToObj(i->String.format("%02x", buffer[i])).collect(Collectors.joining());
        return JOB_NAME_TASKM_PREFIX + rand;
    }
    public String getExecutorName(String taskMasterName, int executorIndex) {
        return new StringBuilder(taskMasterName).append(JOB_NAME_EXEC_PREFIX).
                append(Strings.padStart(String.valueOf(executorIndex), JOB_NAME_EXEC_NO_LENGTH, '0')).toString();
    }

}
