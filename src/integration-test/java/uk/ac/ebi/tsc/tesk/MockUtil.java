package uk.ac.ebi.tsc.tesk;

import com.github.tomakehurst.wiremock.client.WireMock;
import com.github.tomakehurst.wiremock.junit.WireMockRule;
import org.apache.http.HttpStatus;

import static com.github.tomakehurst.wiremock.client.WireMock.*;
import static com.github.tomakehurst.wiremock.client.WireMock.ok;

class MockUtil {
    static void mockGetTaskKubernetesResponses(WireMockRule mockKubernetes) {
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


    static void mockListTaskKubernetesResponses(WireMockRule mockKubernetes) {
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
}
