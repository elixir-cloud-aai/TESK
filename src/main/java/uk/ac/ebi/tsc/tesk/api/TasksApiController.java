package uk.ac.ebi.tsc.tesk.api;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.context.request.NativeWebRequest;
import java.util.Optional;
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
@Controller
@RequestMapping("${openapi.taskExecutionService.base-path:/ga4gh/tes/v1}")
public class TasksApiController implements TasksApi {

    private final NativeWebRequest request;

    @org.springframework.beans.factory.annotation.Autowired
    public TasksApiController(NativeWebRequest request) {
        this.request = request;
    }

    @Override
    public Optional<NativeWebRequest> getRequest() {
        return Optional.ofNullable(request);
    }

}
