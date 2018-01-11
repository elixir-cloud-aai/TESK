package uk.ac.ebi.tsc.tesk.api;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;
import uk.ac.ebi.tsc.tesk.service.TesService;

import static org.hamcrest.Matchers.containsString;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static uk.ac.ebi.tsc.tesk.TestUtils.getFileContentFromResources;

@RunWith(SpringRunner.class)
@WebMvcTest(V1ApiController.class)
public class V1ApiControllerTest {

    @Autowired
    private MockMvc mvc;

    @MockBean
    private TesService tesService;

    @Test
    public void createTask_valid() throws Exception {
        String[] paths = new String[]{"fromTesToK8s/task.json", "fromTesToK8s_minimal/task.json"};
        for (String path : paths) {
            this.mvc.perform(post("/v1/tasks")
                    .content(getFileContentFromResources(path))
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
            this.mvc.perform(post("/v1/tasks")
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
            this.mvc.perform(post("/v1/tasks")
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
                new String[]{"no_type.json", "outputs[0].type"}
        };
        for (String[] file : files) {
            this.mvc.perform(post("/v1/tasks")
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
            this.mvc.perform(post("/v1/tasks")
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
            this.mvc.perform(post("/v1/tasks")
                    .content(getFileContentFromResources("invalid_tasks/" + file[0]))
                    .contentType(MediaType.APPLICATION_JSON)
                    .accept(MediaType.APPLICATION_JSON)).andExpect(status().is4xxClientError())
                    .andExpect(jsonPath("$.message", containsString(file[1])));
        }


    }

}