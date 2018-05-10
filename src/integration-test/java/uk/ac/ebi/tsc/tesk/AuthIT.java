package uk.ac.ebi.tsc.tesk;

import com.github.tomakehurst.wiremock.client.WireMock;
import com.github.tomakehurst.wiremock.junit.WireMockRule;
import io.kubernetes.client.ApiClient;
import io.kubernetes.client.util.Config;
import org.apache.http.HttpStatus;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.test.web.servlet.MockMvc;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.core.WireMockConfiguration.wireMockConfig;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static uk.ac.ebi.tsc.tesk.TestUtils.getFileContentFromResources;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * <p>
 * Integration testing of security (authentication and authorisation using OIDC and Elixir groups)
 * Kubernetes API and OIDC userInfo endpoint are WireMocked
 */
@RunWith(SpringRunner.class)
@SpringBootTest
@AutoConfigureMockMvc
@TestPropertySource(locations = {"classpath:application.properties"},
        properties = {"security.oauth2.resource.user-info-uri = http://localhost:8090"})
public class AuthIT {

    @Autowired
    private MockMvc mvc;

    @Rule
    public WireMockRule mockElixir = new WireMockRule(8090);

    @Rule
    public WireMockRule mockKubernetes = new WireMockRule(wireMockConfig().port(9000).usingFilesUnderDirectory("src/integration-test/resources"));

    @TestConfiguration
    static class KubernetesClientMock {
        @Bean
        @Primary
        public ApiClient kubernetesApiClient() {

            return Config.fromUrl("http://localhost:9000", false);

        }
    }

    @Test
    public void authorizedUser_createTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST\"]}")));

        mockKubernetes.givenThat(
                WireMock.post("/apis/batch/v1/namespaces/default/jobs")
                        .withRequestBody(matchingJsonPath("$.metadata.labels[?(@.creator-group-name == 'TEST')]"))
                        .withRequestBody(matchingJsonPath("$.metadata.labels[?(@.creator-user-id == '123')]"))
                        .willReturn(okJson("{\"metadata\":{\"name\":\"task-fe99716a\"}}")));

        String path = "fromTesToK8s_minimal/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .header("Authorization", "Bearer BAR")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk());
    }

    @Test
    public void multiGroups_createTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST\", \"elixir:GA4GH:GA4GH-CAP:EBI:ABC\"]}")));

        mockKubernetes.givenThat(
                WireMock.post("/apis/batch/v1/namespaces/default/jobs")
                        .withRequestBody(matchingJsonPath("$.metadata.labels[?(@.creator-user-id == '123')]"))
                        .willReturn(okJson("{\"metadata\":{\"name\":\"task-fe99716a\"}}")));

        String path = "fromTesToK8s_minimal/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .header("Authorization", "Bearer BAR")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk());
    }

    @Test
    public void chosenGroup_createTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST\", \"elixir:GA4GH:GA4GH-CAP:EBI:ABC\"]}")));

        mockKubernetes.givenThat(
                WireMock.post("/apis/batch/v1/namespaces/default/jobs")
                        .withRequestBody(matchingJsonPath("$.metadata.labels[?(@.creator-user-id == '123')]"))
                        .withRequestBody(matchingJsonPath("$.metadata.labels[?(@.creator-group-name == 'ABC')]"))
                        .willReturn(okJson("{\"metadata\":{\"name\":\"task-fe99716a\"}}")));

        String path = "fromTesToK8s/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .header("Authorization", "Bearer BAR")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isOk());
    }

    @Test
    public void wrongChosenGroup_createTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST\", \"elixir:GA4GH:GA4GH-CAP:EBI:XYZ\"]}")));

        String path = "fromTesToK8s/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .header("Authorization", "Bearer BAR")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isForbidden());
    }

    @Test
    public void unauthenicated_createTask() throws Exception {

        String path = "fromTesToK8s_minimal/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isUnauthorized());
    }

    @Test
    public void differentGroup_createTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\":\"123\",\"groupNames\":[\"elixir:different\"]}")));

        String path = "fromTesToK8s_minimal/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .contentType(MediaType.APPLICATION_JSON)
                .header("Authorization", "Bearer BAR")
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isForbidden());
    }

    @Test
    public void noGroups_createTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\":\"123\",\"groupNames\":[]}")));

        String path = "fromTesToK8s_minimal/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .header("Authorization", "Bearer BAR")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isForbidden());
    }

    @Test
    public void noGroupsScope_createTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\":\"123\"}")));

        String path = "fromTesToK8s_minimal/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .header("Authorization", "Bearer BAR")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isForbidden());
    }

    @Test
    public void wrongGroupPrefix_createTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\":\"123\",\"groupNames\":[\"GA4GH:GA4GH-CAP:EBI\"]}")));

        String path = "fromTesToK8s_minimal/task.json";
        this.mvc.perform(post("/v1/tasks")
                .content(getFileContentFromResources(path))
                .header("Authorization", "Bearer BAR")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)).andExpect(status().isForbidden());
    }

    @Test
    public void unauthenticated_getTask() throws Exception {
        this.mvc.perform(get("/v1/tasks/{id}", 123))
                .andExpect(status().isUnauthorized());
    }

    @Test
    public void unauthenticated_cancelTask() throws Exception {
        this.mvc.perform(post("/v1/tasks/{id}:cancel", 123))
                .andExpect(status().isUnauthorized());
    }

    @Test
    public void authorized_getTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST\"]}")));

        mockGetTaskKubernetesResponses();


        this.mvc.perform(get("/v1/tasks/{id}", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());

        this.mvc.perform(get("/v1/tasks/{id}?view=BASIC", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());
        this.mvc.perform(get("/v1/tasks/{id}?view=FULL", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());
    }

    @Test
    public void authorized_cancelTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST\"]}")));

        mockGetTaskKubernetesResponses();

        this.mvc.perform(post("/v1/tasks/{id}:cancel", "task-123")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.message").value("Job with ID=task-123 has no pods in RUNNING status."));

    }

    @Test
    public void nonauthorized_cancelTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"124\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST\"]}")));

        mockGetTaskKubernetesResponses();

        this.mvc.perform(post("/v1/tasks/{id}:cancel", "task-123")
                .contentType(MediaType.APPLICATION_JSON)
                .accept(MediaType.APPLICATION_JSON)
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());

    }

    @Test
    public void memberNonAuthor_getTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"124\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST\"]}")));

        mockGetTaskKubernetesResponses();

        this.mvc.perform(get("/v1/tasks/{id}", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
        this.mvc.perform(get("/v1/tasks/{id}?view=BASIC", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
        this.mvc.perform(get("/v1/tasks/{id}?view=FULL", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
    }

    @Test
    public void adminNonAuthor_getTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"124\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\", \"elixir:GA4GH:GA4GH-CAP:EBI:TEST:ADMIN\"]}")));

        mockGetTaskKubernetesResponses();

        this.mvc.perform(get("/v1/tasks/{id}", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());
        this.mvc.perform(get("/v1/tasks/{id}?view=BASIC", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());
        this.mvc.perform(get("/v1/tasks/{id}?view=FULL", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());
    }

    @Test
    public void authorNonMember_getTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\"]}")));

        mockGetTaskKubernetesResponses();

        this.mvc.perform(get("/v1/tasks/{id}", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
        this.mvc.perform(get("/v1/tasks/{id}?view=BASIC", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
        this.mvc.perform(get("/v1/tasks/{id}?view=FULL", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
    }

    @Test
    public void superAdmin_getTask() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"xyz\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI:ADMIN\"]}")));

        mockGetTaskKubernetesResponses();

        this.mvc.perform(get("/v1/tasks/{id}", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());
        this.mvc.perform(get("/v1/tasks/{id}?view=BASIC", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());
        this.mvc.perform(get("/v1/tasks/{id}?view=FULL", "task-123")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk());
    }

    @Test
    public void member_getList() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI\",\"elixir:GA4GH:GA4GH-CAP:EBI:TEST\"]}")));

        mockKubernetes.givenThat(
                WireMock.get("/apis/batch/v1/namespaces/default/jobs?labelSelector=job-type%3Dtaskmaster" +
                        "%2Ccreator-group-name%20in%20%28TEST%29%2Ccreator-user-id%3D123")
                        .willReturn(aResponse().withBodyFile("list/taskmasters.json")));
        mockListTaskKubernetesResponses();

        performListTask(4);

    }

    @Test
    public void superAdmin_getList() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI:ADMIN\"]}")));

        mockKubernetes.givenThat(
                WireMock.get("/apis/batch/v1/namespaces/default/jobs?labelSelector=job-type%3Dtaskmaster")
                        .willReturn(aResponse().withBodyFile("list/taskmasters.json")));
        mockListTaskKubernetesResponses();

        performListTask(4);

    }

    @Test
    public void groupAdmin_getList() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI:TEST:ADMIN\"]}")));

        mockKubernetes.givenThat(
                WireMock.get("/apis/batch/v1/namespaces/default/jobs?labelSelector=job-type%3Dtaskmaster" +
                        "%2Ccreator-group-name%20in%20%28TEST%29")
                        .willReturn(aResponse().withBodyFile("list/taskmasters.json")));
        mockListTaskKubernetesResponses();

        performListTask(4);

    }

    @Test
    public void mixed_getList() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"elixir:GA4GH:GA4GH-CAP:EBI:ABC:ADMIN\",\"elixir:GA4GH:GA4GH-CAP:EBI:TEST\"]}")));

        mockKubernetes.givenThat(
                WireMock.get("/apis/batch/v1/namespaces/default/jobs?labelSelector=job-type%3Dtaskmaster" +
                        "%2Ccreator-group-name%20in%20%28TEST%2CABC%29")
                        .willReturn(aResponse().withBodyFile("list/taskmasters.json")));
        mockListTaskKubernetesResponses();

        performListTask(3);

    }

    @Test
    public void unauthenticated_getList() throws Exception {

        this.mvc.perform(get("/v1/tasks")
                .header("Authorization", "different BAR"))
                .andExpect(status().isUnauthorized());
        this.mvc.perform(get("/v1/tasks?view=BASIC")
                .header("Different", "Bearer BAR"))
                .andExpect(status().isUnauthorized());
        this.mvc.perform(get("/v1/tasks?view=FULL"))
                .andExpect(status().isUnauthorized());

    }

    @Test
    public void nonmember_getList() throws Exception {

        mockElixir.givenThat(
                WireMock.get("/")
                        .willReturn(okJson("{\"sub\" : \"123\",  \"groupNames\" : [\"sth\",\"elixir:GA4GH:GA4GH-CAP\"]}")));

        this.mvc.perform(get("/v1/tasks")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
        this.mvc.perform(get("/v1/tasks?view=BASIC")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
        this.mvc.perform(get("/v1/tasks?view=FULL")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isForbidden());
    }

    private void mockGetTaskKubernetesResponses() {
        mockKubernetes.givenThat(
                WireMock.get("/apis/batch/v1/namespaces/default/jobs?labelSelector=taskmaster-name%3Dtask-123")
                        .willReturn(aResponse().withBodyFile("task-123/executor.json")));
        mockKubernetes.givenThat(
                WireMock.get("/apis/batch/v1/namespaces/default/jobs/task-123")
                        .willReturn(aResponse().withBodyFile("task-123/taskmaster.json")));
        mockKubernetes.givenThat(WireMock.get("/apis/batch/v1/namespaces/default/jobs/task-123-outputs-filer")
                .willReturn(aResponse().withStatus(HttpStatus.SC_NOT_FOUND)));

        mockKubernetes.givenThat(
                WireMock.get("/api/v1/namespaces/default/pods?labelSelector=controller-uid%3D24a0504a-4a2b-11e8-a06f-fa163ecf0042")
                        .willReturn(aResponse().withBodyFile("task-123/taskmaster_pods.json")));
        mockKubernetes.givenThat(
                WireMock.get("/api/v1/namespaces/default/pods?labelSelector=controller-uid%3D25f89bbb-4a2b-11e8-a06f-fa163ecf0042")
                        .willReturn(aResponse().withBodyFile("task-123/executor_pods.json")));
        mockKubernetes.givenThat(
                WireMock.get("/api/v1/namespaces/default/pods/pod-123/log")
                        .willReturn(ok("hello!")));
        mockKubernetes.givenThat(
                WireMock.get("/api/v1/namespaces/default/pods/pod-ex-123/log")
                        .willReturn(ok("hello executor!")));
    }


    private void mockListTaskKubernetesResponses() {
        mockKubernetes.givenThat(
                WireMock.get("/apis/batch/v1/namespaces/default/jobs?labelSelector=job-type%3Dexecutor")
                        .willReturn(aResponse().withBodyFile("list/executors.json")));

        mockKubernetes.givenThat(WireMock.get("/apis/batch/v1/namespaces/default/jobs?labelSelector=%21job-type")
                .willReturn(okJson("{\n" +
                        "  \"items\": []\n" +
                        "}")));

        mockKubernetes.givenThat(
                WireMock.get("/api/v1/namespaces/default/pods?labelSelector=job-name")
                        .willReturn(aResponse().withBodyFile("list/pods.json")));
        mockKubernetes.givenThat(
                WireMock.get(urlPathMatching("/api/v1/namespaces/default/pods/([-a-z0-9]+)/log"))
                        .willReturn(ok("hello!")));
    }

    private void performListTask(int expectedLength) throws Exception {
        this.mvc.perform(get("/v1/tasks")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.tasks.length()").value(expectedLength));
        this.mvc.perform(get("/v1/tasks?view=BASIC")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.tasks.length()").value(expectedLength));
        this.mvc.perform(get("/v1/tasks?view=FULL")
                .header("Authorization", "Bearer BAR"))
                .andExpect(status().isOk()).andExpect(jsonPath("$.tasks.length()").value(expectedLength));
    }

}
