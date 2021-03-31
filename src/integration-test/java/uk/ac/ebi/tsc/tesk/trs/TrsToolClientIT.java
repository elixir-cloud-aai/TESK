package uk.ac.ebi.tsc.tesk.trs;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.client.RestClientTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.client.MockRestServiceServer;
import uk.ac.ebi.tsc.tesk.trs.model.ImageData;
import uk.ac.ebi.tsc.tesk.trs.model.ImageType;
import uk.ac.ebi.tsc.tesk.trs.model.ToolVersion;

import javax.annotation.PostConstruct;
import java.util.Optional;

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

/**
 * @author aniewielska
 * @since 31/03/2021
 */
@RunWith(SpringRunner.class)
@RestClientTest(TrsToolClient.class)
@TestPropertySource(properties = {"tesk.api.trs.urlPattern=https://{host}/trs/{id}/versions/{version}",
        "tesk.api.trs.uriPattern=trs://{host}/trs-id/{id}/{version}"})
public class TrsToolClientIT {

    @Autowired
    private TrsToolClient subject;
    @Autowired
    private MockRestServiceServer server;
    @Autowired
    private ObjectMapper objectMapper;

    @TestConfiguration
    static class Configuration {
        @Bean
        public TrsProperties trsProperties() {
            return new TrsProperties();
        }
    }

    private String detailsStringWithDocker;
    private String detailsStringWithoutDocker;

    @PostConstruct
    public void setup() throws Exception {
        ToolVersion toolVersion = new ToolVersion();
        ImageData imageData1 = new ImageData();
        imageData1.setImageType(ImageType.Docker);
        imageData1.setImageName("ubuntu:latest");
        toolVersion.getImages().add(imageData1);
        ImageData imageData2 = new ImageData();
        imageData2.setImageType(ImageType.Conda);
        imageData2.setImageName("sthElse");
        toolVersion.getImages().add(imageData2);
        detailsStringWithDocker =
                objectMapper.writeValueAsString(toolVersion);
        toolVersion.getImages().remove(0);
        detailsStringWithoutDocker =
                objectMapper.writeValueAsString(toolVersion);
    }

    @Before
    public void setUp() {
        this.server.reset();
    }

    @Test
    public void getDockerImageForToolVersionURI_success() {
        this.server.expect(requestTo("https://trsHost/trs/toolId/versions/toolVersion"))
                .andRespond(withSuccess(detailsStringWithDocker, MediaType.APPLICATION_JSON));
        String result = subject.getDockerImageForToolVersionURI("trs://trsHost/trs-id/toolId/toolVersion");
        assertThat(result, is("ubuntu:latest"));
    }

    @Test
    public void getDockerImageForToolVersionURI_wrongUri() {
        String result = subject.getDockerImageForToolVersionURI("sth");
        assertThat(result, is("sth"));
    }

    @Test
    public void getDockerImageForToolVersionURI_noDocker() {
        this.server.expect(requestTo("https://trsHost/trs/toolId2/versions/toolVersion2"))
                .andRespond(withSuccess(detailsStringWithoutDocker, MediaType.APPLICATION_JSON));
        String result = subject.getDockerImageForToolVersionURI("trs://trsHost/trs-id/toolId2/toolVersion2");
        assertThat(result, is("trs://trsHost/trs-id/toolId2/toolVersion2"));
    }

    @Test
    public void getDockerImageForToolVersion_success() {
        this.server.expect(requestTo("https://trsHost/trs/toolId/versions/toolVersion"))
                .andRespond(withSuccess(detailsStringWithDocker, MediaType.APPLICATION_JSON));
        Optional<String> result = subject.getDockerImageForToolVersion("trsHost", "toolId", "toolVersion");
        assertThat(result.get(), is("ubuntu:latest"));
    }

    @Test
    public void getDockerImageForToolVersion_noDocker() {
        this.server.expect(requestTo("https://trsHost/trs/toolId2/versions/toolVersion2"))
                .andRespond(withSuccess(detailsStringWithoutDocker, MediaType.APPLICATION_JSON));
        Optional<String> result = subject.getDockerImageForToolVersion("trsHost", "toolId2", "toolVersion2");
        assertThat(result, is(Optional.empty()));
    }
}