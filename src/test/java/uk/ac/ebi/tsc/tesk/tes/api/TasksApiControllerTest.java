package uk.ac.ebi.tsc.tesk.tes.api;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.security.oauth2.common.OAuth2AccessToken;
import org.springframework.security.oauth2.common.exceptions.InvalidTokenException;
import org.springframework.security.oauth2.config.annotation.web.configuration.EnableResourceServer;
import org.springframework.security.oauth2.config.annotation.web.configuration.ResourceServerConfigurerAdapter;
import org.springframework.security.oauth2.config.annotation.web.configurers.ResourceServerSecurityConfigurer;
import org.springframework.security.oauth2.provider.OAuth2Authentication;
import org.springframework.security.oauth2.provider.OAuth2Request;
import org.springframework.security.oauth2.provider.token.ResourceServerTokenServices;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;
import uk.ac.ebi.tsc.tesk.config.security.User;
import uk.ac.ebi.tsc.tesk.tes.service.ServiceInfoService;
import uk.ac.ebi.tsc.tesk.tes.service.TesService;

import java.util.List;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static uk.ac.ebi.tsc.tesk.TestUtils.getFileContentFromResources;
import static uk.ac.ebi.tsc.tesk.UrlConstants.TASK_URL;

@RunWith(SpringRunner.class)
@WebMvcTest(TasksApiController.class)
public class TasksApiControllerTest {

    @TestConfiguration
    @EnableResourceServer
    static class ResourceServerConfiguration extends ResourceServerConfigurerAdapter {

        @Override
        public void configure(ResourceServerSecurityConfigurer security) {
            security.tokenServices(tokenServices());
        }
        ResourceServerTokenServices tokenServices() {
            return new ResourceServerTokenServices() {

                @Override
                public OAuth2Authentication loadAuthentication(String accessToken) throws AuthenticationException, InvalidTokenException {
                    Object principal = User.builder("admin").build();
                    List<GrantedAuthority> authorities = AuthorityUtils.commaSeparatedStringToAuthorityList(accessToken);
                    OAuth2Request request = new OAuth2Request(null, null, null, true, null,
                            null, null, null, null);
                    UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken(
                            principal, "N/A", authorities);
                    return new OAuth2Authentication(request, token);
                }

                @Override
                public OAuth2AccessToken readAccessToken(String accessToken) {
                    return null;
                }
            };
        }
    }


    @Autowired
    private MockMvc mvc;

    @MockBean
    private TesService tesService;
    @MockBean
    ServiceInfoService serviceInfoService;

    @Test
    public void createTask_valid() throws Exception {
        String[] paths = new String[]{"fromTesToK8s/task.json", "fromTesToK8s_minimal/task.json"};
        for (String path : paths) {
            this.mvc.perform(post(TASK_URL)
                    .content(getFileContentFromResources(path))
                    .header("Authorization", "Bearer BAR")
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk());
        }
    }

    @Test
    public void createTask_invalid_executors() throws Exception {
        String[][] files = new String[][]{
                new String[]{"none.json", "executors"},
                new String[]{"empty.json", "executors"},
                new String[]{"no_image.json", "image"},
                new String[]{"no_command.json", "command"},
                new String[]{"invalid_stdin.json", "stdin"},
        };
        for (String[] file : files) {
            this.mvc.perform(post(TASK_URL)
                    .header("Authorization", "Bearer BAR")
                    .content(getFileContentFromResources("invalid_tasks/executors/" + file[0]))
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)).andExpect(status().is4xxClientError())
                    .andExpect(jsonPath("$.messages[0]", containsString(file[1])));
        }


    }

    @Test
    public void createTask_invalid_inputs() throws Exception {
        String[][] files = new String[][]{
                new String[]{"no_path.json", "inputs[0].path"},
                new String[]{"no_source.json", "URL or content required"},
                new String[]{"wrong_type.json", "inputs[0].type"}
        };
        for (String[] file : files) {
            this.mvc.perform(post(TASK_URL)
                    .header("Authorization", "Bearer BAR")
                    .content(getFileContentFromResources("invalid_tasks/inputs/" + file[0]))
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)).andExpect(status().is4xxClientError())
                    .andExpect(jsonPath("$.messages[0]", containsString(file[1])));
        }


    }

    @Test
    public void createTask_invalid_outputs() throws Exception {
        String[][] files = new String[][]{
                new String[]{"no_path.json", "outputs[0].path"},
                new String[]{"no_url.json", "outputs[0].url"},
                new String[]{"empty_type.json", "outputs[0].type"}
        };
        for (String[] file : files) {
            this.mvc.perform(post(TASK_URL)
                    .header("Authorization", "Bearer BAR")
                    .content(getFileContentFromResources("invalid_tasks/outputs/" + file[0]))
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)).andExpect(status().is4xxClientError())
                    .andExpect(jsonPath("$.messages[0]", containsString(file[1])));
        }


    }

    @Test
    public void createTask_invalid_volumes() throws Exception {
        String[][] files = new String[][]{
                new String[]{"wrong_volumes.json", "volumes[1]"}
        };
        for (String[] file : files) {
            this.mvc.perform(post(TASK_URL)
                    .header("Authorization", "Bearer BAR")
                    .content(getFileContentFromResources("invalid_tasks/" + file[0]))
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)).andExpect(status().is4xxClientError())
                    .andExpect(jsonPath("$.messages[0]", containsString(file[1])));
        }


    }

    @Test
    public void createTask_invalid_unrecognized_field() throws Exception {
        String[][] files = new String[][]{
                new String[]{"unrecognized_field.json", "Unrecognized field \"unknown\""}
        };
        for (String[] file : files) {
            this.mvc.perform(post(TASK_URL)
                    .header("Authorization", "Bearer BAR")
                    .content(getFileContentFromResources("invalid_tasks/" + file[0]))
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)).andExpect(status().is4xxClientError())
                    .andExpect(jsonPath("$.message", containsString(file[1])));
        }


    }

}