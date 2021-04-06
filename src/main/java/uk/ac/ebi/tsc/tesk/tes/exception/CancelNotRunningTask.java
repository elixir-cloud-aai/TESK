package uk.ac.ebi.tsc.tesk.tes.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * 400 - cancel task in status other than RUNNING
 */
@ResponseStatus(HttpStatus.BAD_REQUEST)
public class CancelNotRunningTask extends RuntimeException {
    private static final String message = "Job with ID=%s has no pods in RUNNING status.";
    public CancelNotRunningTask(String taskId) {
        super(String.format(message, taskId));
    }
}
