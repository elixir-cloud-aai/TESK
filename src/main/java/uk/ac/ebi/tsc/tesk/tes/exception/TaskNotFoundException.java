package uk.ac.ebi.tsc.tesk.tes.exception;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * 404 - for getTask
 */
@ResponseStatus(HttpStatus.NOT_FOUND)
public class TaskNotFoundException extends RuntimeException {
    private static final String message = "Job with ID=%s not found.";
    public TaskNotFoundException(String taskId) {
        super(String.format(message, taskId));
    }
}
