package uk.ac.ebi.tsc.tesk.tes.service;

import org.junit.Test;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;
import uk.ac.ebi.tsc.tesk.tes.model.ServiceOrganization;
import uk.ac.ebi.tsc.tesk.tes.model.TesServiceInfo;

import java.net.URI;
import java.net.URISyntaxException;
import java.time.LocalDateTime;
import java.time.ZoneOffset;

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;

/**
 * @author aniewielska
 * @since 09/04/2021
 */
public class ServiceInfoServiceTest {

    private Resource serviceInfoFile = new ClassPathResource("service-info.yaml");
    private ServiceInfoService subject = new ServiceInfoService(serviceInfoFile);

    @Test
    public void getServiceInfo() throws URISyntaxException {
        subject.setUp();
        TesServiceInfo result = subject.getServiceInfo();
        TesServiceInfo expected = new TesServiceInfo()
                .name("example application")
                .createdAt(LocalDateTime.parse("2001-12-14T21:59:00").atOffset(ZoneOffset.UTC))
                .organization(new ServiceOrganization().name("EBI").url("http://example.com"));
        assertThat(result, is(expected));
        subject.loadYaml();
        assertThat(result, is(expected));
    }
}