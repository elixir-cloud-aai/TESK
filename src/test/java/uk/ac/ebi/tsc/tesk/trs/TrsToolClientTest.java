package uk.ac.ebi.tsc.tesk.trs;

import lombok.AllArgsConstructor;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.Parameterized;
import org.springframework.boot.web.client.RestTemplateBuilder;

import java.util.Arrays;
import java.util.Collection;

import static org.hamcrest.CoreMatchers.is;
import static org.junit.Assert.assertThat;

/**
 * @author aniewielska
 * @since 30/03/2021
 */
@AllArgsConstructor
@RunWith(Parameterized.class)
public class TrsToolClientTest {


    private final String uriPattern;
    private final String uri;
    private final boolean expectedMatch;
    private final String host;
    private final String id;
    private final String version;

    private final static String URI_PATTERN_1 = "trs://{host}/{id}/versions/{version}";
    private final static String URI_PATTERN_2 = "protocol{host}_{id}_{version}";


    @Parameterized.Parameters
    public static Collection<Object[]> data() {
        return Arrays.asList(new Object[][]{
                {URI_PATTERN_1, "trs://example.com/identifier/versions/123", true, "example.com", "identifier", "123"},
                {URI_PATTERN_1, "trs://example.com/identifier/123", false, "", "", ""},
                {URI_PATTERN_2, "protocolexample.com_identifier_123", true, "example.com", "identifier", "123"},
                {URI_PATTERN_2, "protocoexample.com_identifier_123", false, "", "", ""}
        });
    }


    @Test
    public void testTranslateTrsURI_match() {
        String[] results = new String[3];
        TrsProperties properties = new TrsProperties();
        properties.setUriPattern(uriPattern);
        TrsToolClient subject = new TrsToolClient(new RestTemplateBuilder(), properties);
        boolean match = subject.translateTrsURI(uri, results);
        assertThat(match, is(expectedMatch));
        if (expectedMatch) {
            assertThat(results[0], is(host));
            assertThat(results[1], is(id));
            assertThat(results[2], is(version));
        }
    }

}