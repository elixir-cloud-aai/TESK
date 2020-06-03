package uk.ac.ebi.tsc.tesk.service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import uk.ac.ebi.tsc.tesk.config.ServiceInfoProperties;
import uk.ac.ebi.tsc.tesk.model.TesServiceInfo;

/**
 * @author aniewielska
 * @since 03/06/2020
 */
@RequiredArgsConstructor
@Service
public class ServiceInfoService {

    private final ServiceInfoProperties properties;

    public TesServiceInfo serviceInfo() {
        return new TesServiceInfo().name(properties.getName()).doc(properties.getDocumentation());
    }
}
