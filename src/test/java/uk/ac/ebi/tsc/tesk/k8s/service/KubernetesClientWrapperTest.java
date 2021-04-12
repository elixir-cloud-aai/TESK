package uk.ac.ebi.tsc.tesk.k8s.service;

import io.kubernetes.client.ApiException;
import io.kubernetes.client.apis.BatchV1Api;
import io.kubernetes.client.apis.CoreV1Api;
import io.kubernetes.client.models.*;
import org.joda.time.DateTime;
import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mockito;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.HttpStatus;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit4.SpringRunner;
import org.springframework.util.StringUtils;
import uk.ac.ebi.tsc.tesk.config.security.User;
import uk.ac.ebi.tsc.tesk.tes.exception.TaskNotFoundException;

import java.util.Arrays;
import java.util.Optional;

import static org.hamcrest.Matchers.is;
import static org.junit.Assert.assertThat;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.BDDMockito.given;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.LABEL_GROUPNAME_KEY;
import static uk.ac.ebi.tsc.tesk.k8s.constant.Constants.LABEL_USERID_KEY;

@RunWith(SpringRunner.class)
@TestPropertySource(
        properties = {"tesk.api.k8s.namespace = test-namespace"})
public class KubernetesClientWrapperTest {

    @Value("${tesk.api.k8s.namespace}")
    private String namespace;
    @MockBean
    private BatchV1Api batchApi;

    @MockBean
    private CoreV1Api coreApi;


    private KubernetesClientWrapper wrapper;

    @Before
    public void setUp() {

        this.wrapper = new KubernetesClientWrapper(batchApi, batchApi,
                coreApi, coreApi, namespace);
    }

    @Test
    public void createJob() throws ApiException {
        V1Job inJob = new V1Job().metadata(new V1ObjectMeta().name("test job"));
        V1Job outJob = new V1Job().metadata(new V1ObjectMeta().name("test job").creationTimestamp(new DateTime()));
        given(batchApi.createNamespacedJob("test-namespace", inJob, null)).willReturn(outJob);
        V1Job result = wrapper.createJob(inJob);
        assertThat(result, is(outJob));
    }

    @Test
    public void readTaskmasterJob() throws ApiException {
        V1Job job = new V1Job().metadata(new V1ObjectMeta().name("test job").putLabelsItem("job-type", "taskmaster"));
        given(batchApi.readNamespacedJob("123", "test-namespace", null, null, null)).willReturn(job);
        V1Job result = wrapper.readTaskmasterJob("123");
        assertThat(result, is(job));
    }

    @Test(expected = TaskNotFoundException.class)
    public void readTaskmasterJob_wrongType() throws Exception {
        V1Job job = new V1Job().metadata(new V1ObjectMeta().name("test job").putLabelsItem("job-type", "executor"));
        given(batchApi.readNamespacedJob("123", "test-namespace", null, null, null)).willReturn(job);
        wrapper.readTaskmasterJob("123");
    }

    @Test(expected = TaskNotFoundException.class)
    public void readTaskmasterJob_noType() throws Exception {
        V1Job job = new V1Job().metadata(new V1ObjectMeta().name("test job").putLabelsItem("other", "taskmaster"));
        given(batchApi.readNamespacedJob("123", "test-namespace", null, null, null)).willReturn(job);
        wrapper.readTaskmasterJob("123");
    }

    @Test(expected = TaskNotFoundException.class)
    public void readTaskmasterJob_noJob() throws Exception {
        given(batchApi.readNamespacedJob("123", "test-namespace", null, null, null)).willThrow(new ApiException(HttpStatus.NOT_FOUND.value(), "No job"));
        wrapper.readTaskmasterJob("123");
    }


    @Test
    public void listAllTaskmasterJobsForUser_any() throws ApiException {

        User user = User.builder("123").build();
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        given(batchApi.listNamespacedJob(any(), isNull(), isNull(), isNull(), isNull(), any(), isNull(), isNull(), isNull(), isNull())).willReturn(this.resultList());
        V1JobList result = wrapper.listAllTaskmasterJobsForUser(null, null, user);
        Mockito.verify(batchApi).listNamespacedJob(eq("test-namespace"), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("job-type=taskmaster"));
        assertThat(result, is(this.resultList()));
    }

    @Test
    public void listAllTaskmasterJobsForUser_admin() throws ApiException {

        User user = User.builder("123").teskAdmin(true).build();
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        given(batchApi.listNamespacedJob(any(), isNull(), isNull(), isNull(), isNull(), any(), isNull(), isNull(), isNull(), isNull())).willReturn(this.resultList());
        V1JobList result = wrapper.listAllTaskmasterJobsForUser(null, null, user);
        Mockito.verify(batchApi).listNamespacedJob(eq(namespace), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("job-type=taskmaster"));
        assertThat(result, is(this.resultList()));
    }

    @Test
    public void listAllTaskmasterJobsForUser_member() throws ApiException {

        User user = User.builder("123").teskMemberedGroups(StringUtils.commaDelimitedListToSet("TEST")).build();
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        given(batchApi.listNamespacedJob(any(), isNull(), isNull(), isNull(), isNull(), any(), isNull(), isNull(), isNull(), isNull())).willReturn(this.resultList());
        V1JobList result = wrapper.listAllTaskmasterJobsForUser(null, null, user);
        Mockito.verify(batchApi).listNamespacedJob(eq(namespace), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("job-type=taskmaster,creator-group-name in (TEST),creator-user-id=123"));
        assertThat(result, is(this.resultList()));
    }

    @Test
    public void listAllTaskmasterJobsForUser_groupAdmin() throws ApiException {

        User user = User.builder("123").teskManagedGroups(StringUtils.commaDelimitedListToSet("TEST,XYZ")).build();
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        given(batchApi.listNamespacedJob(any(), isNull(), isNull(), isNull(), isNull(), any(), isNull(), isNull(), isNull(), isNull())).willReturn(this.resultList());
        V1JobList result = wrapper.listAllTaskmasterJobsForUser(null, null, user);
        Mockito.verify(batchApi).listNamespacedJob(eq(namespace), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("job-type=taskmaster,creator-group-name in (TEST,XYZ)"));
        assertThat(result, is(this.resultList()));
    }

    @Test
    public void listAllTaskmasterJobsForUser_mixed() throws ApiException {

        User user = User.builder("123").teskManagedGroups(StringUtils.commaDelimitedListToSet("TEST")).teskMemberedGroups(StringUtils.commaDelimitedListToSet("XYZ")).build();
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        given(batchApi.listNamespacedJob(any(), isNull(), isNull(), isNull(), isNull(), any(), isNull(), isNull(), isNull(), isNull())).willReturn(this.resultList());
        V1JobList result = wrapper.listAllTaskmasterJobsForUser(null, null, user);
        Mockito.verify(batchApi).listNamespacedJob(eq(namespace), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("job-type=taskmaster,creator-group-name in (XYZ,TEST)"));
        assertThat(result, is(filteredResultList()));
    }

    @Test
    public void listSingleTaskExecutorJobs() throws ApiException {
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        wrapper.listSingleTaskExecutorJobs("123");
        Mockito.verify(batchApi).listNamespacedJob(eq("test-namespace"), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("taskmaster-name=123"));
    }

    @Test
    public void getSingleTaskOutputFilerJob() throws ApiException {
        V1Job job = new V1Job().metadata(new V1ObjectMeta().name("test job"));
        given(batchApi.readNamespacedJob("123-outputs-filer", "test-namespace", null, null, null)).willReturn(job);
        Optional<V1Job> result = wrapper.getSingleTaskOutputFilerJob("123");
        assertThat(result, is(Optional.of(job)));
    }

    @Test
    public void getSingleTaskOutputFilerJob_noJob() throws ApiException {
        given(batchApi.readNamespacedJob("123-outputs-filer", "test-namespace", null, null, null)).willThrow(new ApiException(HttpStatus.NOT_FOUND.value(), "No Job"));
        Optional<V1Job> result = wrapper.getSingleTaskOutputFilerJob("123");
        assertThat(result, is(Optional.empty()));
    }

    @Test
    public void listAllTaskExecutorJobs() throws ApiException {
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        wrapper.listAllTaskExecutorJobs();
        Mockito.verify(batchApi).listNamespacedJob(eq("test-namespace"), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("job-type=executor"));
    }

    @Test
    public void listAllFilerJobs() throws ApiException {
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        wrapper.listAllFilerJobs();
        Mockito.verify(batchApi).listNamespacedJob(eq("test-namespace"), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("!job-type"));
    }

    @Test
    public void listSingleJobPods() throws ApiException {
        V1Job job = new V1Job().metadata(new V1ObjectMeta().name("test job")).spec(new V1JobSpec().selector(new V1LabelSelector().
                putMatchLabelsItem("label1", "value1").putMatchLabelsItem("labelA", "valueB")));
        ArgumentCaptor<String> argument = ArgumentCaptor.forClass(String.class);
        wrapper.listSingleJobPods(job);
        Mockito.verify(coreApi).listNamespacedPod(eq("test-namespace"), isNull(), isNull(), isNull(), isNull(), argument.capture(), isNull(), isNull(), isNull(), isNull());
        assertThat(argument.getValue(), is("label1=value1,labelA=valueB"));
    }

    @Test
    public void listAllJobPods() throws ApiException {
        wrapper.listAllJobPods();
        Mockito.verify(coreApi).listNamespacedPod(eq("test-namespace"), isNull(), isNull(), isNull(), isNull(), eq("job-name"), isNull(), isNull(), isNull(), isNull());
    }

    private V1JobList resultList() {
        V1JobList jobList = new V1JobList();
        jobList.setItems(Arrays.asList(new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "TEST").putLabelsItem(LABEL_USERID_KEY, "123")),
                new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "TEST").putLabelsItem(LABEL_USERID_KEY, "124")),
                new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "XYZ").putLabelsItem(LABEL_USERID_KEY, "123")),
                new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "XYZ").putLabelsItem(LABEL_USERID_KEY, "124")),
                new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "ABC").putLabelsItem(LABEL_USERID_KEY, "123"))));
        return jobList;
    }

    private V1JobList filteredResultList() {
        V1JobList jobList = new V1JobList();
        jobList.setItems(Arrays.asList(new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "TEST").putLabelsItem(LABEL_USERID_KEY, "123")),
                new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "TEST").putLabelsItem(LABEL_USERID_KEY, "124")),
                new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "XYZ").putLabelsItem(LABEL_USERID_KEY, "123")),
                //this one wan't br filtered in Java, but K8s should not return this one
                new V1Job().metadata(new V1ObjectMeta().putLabelsItem(LABEL_GROUPNAME_KEY, "ABC").putLabelsItem(LABEL_USERID_KEY, "123"))));
        return jobList;
    }
}