package uk.ac.ebi.tsc.tesk.tes.api;

import io.swagger.annotations.ApiParam;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.provider.OAuth2Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import uk.ac.ebi.tsc.tesk.config.security.User;
import uk.ac.ebi.tsc.tesk.tes.model.*;
import uk.ac.ebi.tsc.tesk.tes.service.TesService;
import uk.ac.ebi.tsc.tesk.tes.model.TaskView;

import javax.validation.Valid;

@javax.annotation.Generated(value = "io.swagger.codegen.languages.SpringCodegen", date = "2017-11-07T14:45:12.993Z")

@Controller
@RequiredArgsConstructor
@RequestMapping("${openapi.taskExecutionService.base-path:/ga4gh/tes/v1}")
public class TasksApiController implements TasksApi {

    private final TesService tesService;

    public ResponseEntity<Object> cancelTask(@ApiParam(value = "", required = true) @PathVariable("id") String id) {
        //getTask - for authZ purposes (cancellation only possible for the same tasks, a user can actually see
        this.tesService.getTask(id, TaskView.MINIMAL, getUser());
        this.tesService.cancelTask(id);
        return new ResponseEntity<Object>(HttpStatus.OK);
    }

    public ResponseEntity<TesCreateTaskResponse> createTask(@ApiParam(value = "", required = true) @Valid @RequestBody TesTask body) {
        TesCreateTaskResponse response = this.tesService.createTask(body, this.getUser());
        return new ResponseEntity<>(response, HttpStatus.OK);
    }

    public ResponseEntity<TesTask> getTask(@ApiParam(value = "", required = true) @PathVariable("id") String id,
                                           @ApiParam(value = "OPTIONAL. Affects the fields included in the returned Task messages. See TaskView below.   - MINIMAL: Task message will include ONLY the fields:   Task.Id   Task.State  - BASIC: Task message will include all fields EXCEPT:   Task.ExecutorLog.stdout   Task.ExecutorLog.stderr   Input.content   TaskLog.system_logs  - FULL: Task message includes all fields.", allowableValues = "MINIMAL, BASIC, FULL", defaultValue = "MINIMAL") @RequestParam(value = "view", required = false, defaultValue = "MINIMAL") String view) {

        TaskView taskView = TaskView.fromString(view);
        TesTask task = this.tesService.getTask(id, taskView, this.getUser());
        if (taskView == TaskView.MINIMAL) {
            task.setLogs(null);
        }
        return new ResponseEntity<>(task, HttpStatus.OK);
    }

    public ResponseEntity<TesListTasksResponse> listTasks(@ApiParam(value = "OPTIONAL. Filter the list to include tasks where the name matches this prefix. If unspecified, no task name filtering is done.") @RequestParam(value = "name_prefix", required = false) String namePrefix, @ApiParam(example="256",value = "OPTIONAL. Number of tasks to return in one page. Must be less than 2048. Defaults to 256.") @RequestParam(value = "page_size", required = false) Long pageSize, @ApiParam(value = "OPTIONAL. Page token is used to retrieve the next page of results. If unspecified, returns the first page of results. See ListTasksResponse.next_page_token") @RequestParam(value = "page_token", required = false) String pageToken, @ApiParam(value = "OPTIONAL. Affects the fields included in the returned Task messages. See TaskView below.   - MINIMAL: Task message will include ONLY the fields:   Task.Id   Task.State  - BASIC: Task message will include all fields EXCEPT:   Task.ExecutorLog.stdout   Task.ExecutorLog.stderr   Input.content   TaskLog.system_logs  - FULL: Task message includes all fields.", allowableValues = "MINIMAL, BASIC, FULL", defaultValue = "MINIMAL") @RequestParam(value = "view", required = false, defaultValue = "MINIMAL") String view) {

        TesListTasksResponse response = this.tesService.listTasks(namePrefix, pageSize, pageToken,  TaskView.fromString(view), this.getUser());
        return new ResponseEntity<TesListTasksResponse>(response, HttpStatus.OK);
    }

    private User getUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        OAuth2Authentication oauth = null;
        if (authentication instanceof OAuth2Authentication) {
            oauth = (OAuth2Authentication) authentication;
            return (User)oauth.getPrincipal();
        }
        return  User.builder(authentication.getName()).build();
    }

}
