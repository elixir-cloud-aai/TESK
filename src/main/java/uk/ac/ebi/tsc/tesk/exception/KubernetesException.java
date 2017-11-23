package uk.ac.ebi.tsc.tesk.exception;

import io.kubernetes.client.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 */
@ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
public class KubernetesException extends RuntimeException {

    private ApiException apiException;

    public static KubernetesException fromApiException(ApiException apiException) {
        return new KubernetesException(apiException);
    }

    public KubernetesException(ApiException apiException) {
        super(apiException.getMessage(), apiException.getCause());
        this.apiException = apiException;
    }
    public boolean isObjectNameDuplicated() {
        return apiException.getCode() == HttpStatus.CONFLICT.value();
    }
}
