package uk.ac.ebi.tsc.tesk.trs;

import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.client.RestTemplate;
import uk.ac.ebi.tsc.tesk.trs.model.ImageData;
import uk.ac.ebi.tsc.tesk.trs.model.ImageType;
import uk.ac.ebi.tsc.tesk.trs.model.ToolVersion;

import java.util.Arrays;
import java.util.Map;
import java.util.Optional;

/**
 * @author aniewielska
 * @since 22/09/2020
 */
@Slf4j
@Service
public class TrsToolClient {
    private final RestTemplate restTemplate;
    private final TrsProperties properties;

    public TrsToolClient(RestTemplateBuilder restTemplateBuilder, TrsProperties properties) {
        this.restTemplate = restTemplateBuilder.build();
        this.properties = properties;
    }

    public String getDockerImageForToolVersionURI(String trsURI) {
        String[] toolCoordinates = new String[3];
        if (translateTrsURI(trsURI, toolCoordinates)) {
            return getDockerImageForToolVersion(toolCoordinates[0], toolCoordinates[1], toolCoordinates[2]).orElse(trsURI);
        }
        return trsURI;
    }

    Optional<String> getDockerImageForToolVersion(String trsHost, String toolId, String toolVersion) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setAccept(Arrays.asList(MediaType.APPLICATION_JSON));
            //Why do I need to emulate the browser is not quite clear.. TBC
            headers.add("user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36");
            HttpEntity entity = new HttpEntity(headers);
            ResponseEntity<ToolVersion> response = restTemplate.exchange(properties.getUrlPattern(), HttpMethod.GET, entity, ToolVersion.class, trsHost, toolId, toolVersion);
            if (response.getStatusCode().is2xxSuccessful()) {
                ToolVersion version = response.getBody();
                if (response.getBody() != null && !version.getImages().isEmpty()) {
                    return version.getImages().stream().filter(imageData -> imageData.getImageType() == ImageType.Docker).findFirst().map(ImageData::getImageName);
                }
            }
        } catch (Exception e) {
            log.info("Error {} retrieving TRS Version {} {} {}", e, trsHost, toolId, toolVersion);
        }
        return Optional.empty();

    }

    boolean translateTrsURI(String trsURI, String[] result) {
        AntPathMatcher matcher = new AntPathMatcher();
        if (matcher.match(properties.getUriPattern(), trsURI)) {
            Map<String, String> variables = matcher.extractUriTemplateVariables(properties.getUriPattern(), trsURI);
            result[0] = variables.get("host");
            result[1] = variables.get("id");
            result[2] = variables.get("version");
            return true;
        }
        return false;
    }

}
