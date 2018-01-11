package uk.ac.ebi.tsc.tesk;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.core.io.Resource;

import java.io.IOException;
import java.nio.file.Files;

public class TestUtils {
    private static final Logger logger = LoggerFactory.getLogger(TestUtils.class);

    public static String getFileContentFromResources(String path) throws IOException {
        Resource fileFromResources = new ClassPathResource(path);
        return new String(Files.readAllBytes(fileFromResources.getFile().toPath()));

    }
}
