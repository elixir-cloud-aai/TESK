package uk.ac.ebi.tsc.tesk.api;

import uk.ac.ebi.tsc.tesk.model.TesCancelTaskResponse;
import uk.ac.ebi.tsc.tesk.model.TesCreateTaskResponse;
import uk.ac.ebi.tsc.tesk.model.TesListTasksResponse;
import uk.ac.ebi.tsc.tesk.model.TesServiceInfo;
import uk.ac.ebi.tsc.tesk.model.TesTask;

import io.swagger.annotations.*;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

import javax.validation.constraints.*;
import javax.validation.Valid;
@javax.annotation.Generated(value = "io.swagger.codegen.languages.SpringCodegen", date = "2017-11-07T14:45:12.993Z")

@Controller
public class V1ApiController implements V1Api {



    public ResponseEntity<TesCancelTaskResponse> cancelTask(@ApiParam(value = "",required=true ) @PathVariable("id") String id) {
        // do some magic!
        return new ResponseEntity<TesCancelTaskResponse>(HttpStatus.OK);
    }

    public ResponseEntity<TesCreateTaskResponse> createTask(@ApiParam(value = "" ,required=true )  @Valid @RequestBody TesTask body) {
        // do some magic!
        return new ResponseEntity<TesCreateTaskResponse>(HttpStatus.OK);
    }

    public ResponseEntity<TesServiceInfo> getServiceInfo() {
        // do some magic!
        return new ResponseEntity<TesServiceInfo>(HttpStatus.OK);
    }

    public ResponseEntity<TesTask> getTask(@ApiParam(value = "",required=true ) @PathVariable("id") String id,
        @ApiParam(value = "OPTIONAL. Affects the fields included in the returned Task messages. See TaskView below.   - MINIMAL: Task message will include ONLY the fields:   Task.Id   Task.State  - BASIC: Task message will include all fields EXCEPT:   Task.ExecutorLog.stdout   Task.ExecutorLog.stderr   TaskParameter.Contents in Task.Inputs  - FULL: Task message includes all fields.", allowableValues = "MINIMAL, BASIC, FULL", defaultValue = "MINIMAL") @RequestParam(value = "view", required = false, defaultValue="MINIMAL") String view) {
        // do some magic!
        return new ResponseEntity<TesTask>(HttpStatus.OK);
    }

    public ResponseEntity<TesListTasksResponse> listTasks(@ApiParam(value = "OPTIONAL. Filter the task list to include tasks in this project.") @RequestParam(value = "project", required = false) String project,
        @ApiParam(value = "OPTIONAL. Filter the list to include tasks where the name matches this prefix. If unspecified, no task name filtering is done.") @RequestParam(value = "name_prefix", required = false) String namePrefix,
        @ApiParam(value = "OPTIONAL. Number of tasks to return in one page. Must be less than 2048. Defaults to 256.") @RequestParam(value = "page_size", required = false) Long pageSize,
        @ApiParam(value = "OPTIONAL. Page token is used to retrieve the next page of results. If unspecified, returns the first page of results. See ListTasksResponse.next_page_token") @RequestParam(value = "page_token", required = false) String pageToken,
        @ApiParam(value = "OPTIONAL. Affects the fields included in the returned Task messages. See TaskView below.   - MINIMAL: Task message will include ONLY the fields:   Task.Id   Task.State  - BASIC: Task message will include all fields EXCEPT:   Task.ExecutorLog.stdout   Task.ExecutorLog.stderr   TaskParameter.Contents in Task.Inputs  - FULL: Task message includes all fields.", allowableValues = "MINIMAL, BASIC, FULL", defaultValue = "MINIMAL") @RequestParam(value = "view", required = false, defaultValue="MINIMAL") String view) {
        // do some magic!
        return new ResponseEntity<TesListTasksResponse>(HttpStatus.OK);
    }

}
