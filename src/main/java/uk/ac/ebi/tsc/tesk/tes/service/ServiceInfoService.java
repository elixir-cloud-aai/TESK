package uk.ac.ebi.tsc.tesk.tes.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.constructor.Construct;
import org.yaml.snakeyaml.constructor.Constructor;
import org.yaml.snakeyaml.nodes.Node;
import org.yaml.snakeyaml.nodes.NodeId;
import org.yaml.snakeyaml.nodes.Tag;
import uk.ac.ebi.tsc.tesk.tes.model.TesServiceInfo;

import javax.annotation.PostConstruct;
import java.io.InputStream;
import java.time.ZoneOffset;
import java.util.Date;

/**
 * @author aniewielska
 * @since 03/06/2020
 */

@Service
@Slf4j
public class ServiceInfoService {

    private static final int RELOAD_INTERVAL = 1000 * 60 * 60;

    private TesServiceInfo serviceInfo;

    private final Resource resourceFile;

    public ServiceInfoService(@Value("${tesk.api.service-info.location}") Resource resourceFile) {
        this.resourceFile = resourceFile;
    }

    @PostConstruct
    public void setUp() {
        loadYaml();
    }

    @Scheduled(fixedDelay = RELOAD_INTERVAL, initialDelay = RELOAD_INTERVAL)
    public void reload() {
        log.debug("Reload Service Info Yaml");
        loadYaml();
    }

    public void loadYaml() {
        Yaml yaml = new Yaml(new OffsetDateTimePropertyConstructor());
        try (InputStream is = resourceFile.getInputStream()) {
            serviceInfo = yaml.loadAs(is, TesServiceInfo.class);
        } catch (Exception e) {
            log.error("Unable to parse Service Info Yaml", e);
        }
    }

    public TesServiceInfo getServiceInfo() {
        return serviceInfo;
    }

    //https://bitbucket.org/asomov/snakeyaml/wiki/Howto#markdown-header-how-to-parse-jodatime
    class OffsetDateTimePropertyConstructor extends Constructor {
        public OffsetDateTimePropertyConstructor() {
            yamlClassConstructors.put(NodeId.scalar, new TimeStampConstruct());
        }

        class TimeStampConstruct extends Constructor.ConstructScalar {
            @Override
            public Object construct(Node nnode) {
                //a change here - Tag != String
                if (nnode.getTag().toString().equals("tag:yaml.org,2002:timestamp")) {
                    Construct dateConstructor = yamlConstructors.get(Tag.TIMESTAMP);
                    Date date = (Date) dateConstructor.construct(nnode);
                    return date.toInstant()
                            .atOffset(ZoneOffset.UTC);
                } else {
                    return super.construct(nnode);
                }
            }

        }
    }
}
