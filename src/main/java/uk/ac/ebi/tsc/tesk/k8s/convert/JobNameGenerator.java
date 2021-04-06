package uk.ac.ebi.tsc.tesk.k8s.convert;

import org.springframework.stereotype.Component;

import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.JOB_NAME_TASKM_PREFIX;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.JOB_NAME_TASKM_RAND_PART_LENGTH;

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

}
