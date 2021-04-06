package uk.ac.ebi.tsc.tesk.tes.api;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.context.request.NativeWebRequest;
import uk.ac.ebi.tsc.tesk.tes.model.TesServiceInfo;
import uk.ac.ebi.tsc.tesk.tes.service.ServiceInfoService;

import java.util.Optional;
@javax.annotation.Generated(value = "org.openapitools.codegen.languages.SpringCodegen", date = "2021-03-24T17:10:08.716Z[Europe/London]")
@RequiredArgsConstructor
@Controller
@RequestMapping("${openapi.taskExecutionService.base-path:/ga4gh/tes/v1}")
public class ServiceInfoApiController implements ServiceInfoApi {

    private final NativeWebRequest request;
    private final ServiceInfoService serviceInfoService;


    @Override
    public Optional<NativeWebRequest> getRequest() {
        return Optional.ofNullable(request);
    }

    @Override
    public ResponseEntity<TesServiceInfo> getServiceInfo() {
        return ResponseEntity.ok(serviceInfoService.getServiceInfo());
    }
}
