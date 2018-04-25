package uk.ac.ebi.tsc.tesk.config;


import org.springframework.boot.autoconfigure.web.servlet.error.BasicErrorController;
import org.springframework.boot.web.servlet.error.ErrorAttributes;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.validation.FieldError;
import org.springframework.validation.ObjectError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseBody;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.context.request.RequestAttributes;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import javax.servlet.http.HttpServletRequest;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 * Custom Error Handler:
 * 1) created mainly to bypass default Spring Boot error controller {@link BasicErrorController} in order
 * to avoid generating html error page for browser requests
 * (always tries to return JSON instead)
 * 2) uses default Spring Boot's ErrorAttributes, customizing output for MethodArgumentNotValidException
 * 3) overrides ResponseEntityExceptionHandler {@link ResponseEntityExceptionHandler} to
 * return sensible HTTP status codes for Spring internal exceptions
 */
@ControllerAdvice
public class CustomErrorHandler extends ResponseEntityExceptionHandler {

    private final ErrorAttributes errorAttributes;

    public CustomErrorHandler(ErrorAttributes errorAttributes) {
        this.errorAttributes = errorAttributes;
    }


    /**
     * Access denied handler
     */
    @ExceptionHandler(AccessDeniedException.class)
    @ResponseBody
    public ResponseEntity<?> accessDeniedHandler(HttpServletRequest request, AccessDeniedException ex) {
        return this.handleExceptionInternal(request, HttpStatus.FORBIDDEN);
    }


    /**
     * Fallback handler for all exceptions other than
     * those handled in ResponseEntityExceptionHandler
     * Tries to retrieve response status from Exception annotation.
     * If not present, returns HTTP 500.
     * Places default ErrorAttributes in the response body
     */
    @ExceptionHandler(Exception.class)
    @ResponseBody
    public ResponseEntity<?> commonErrorHandler(HttpServletRequest request, Exception ex) {
        ResponseStatus requestedResponseStatus = AnnotatedElementUtils.findMergedAnnotation(ex.getClass(), ResponseStatus.class);
        HttpStatus status = requestedResponseStatus != null ? requestedResponseStatus.code() : HttpStatus.INTERNAL_SERVER_ERROR;
        return this.handleExceptionInternal(request, status);
    }

    /**
     * Handles MethodArgumentNotValidException, replacing message and error from Spring Boot's default implementation
     * with messages composed of validator binding results.
     */
    @Override
    @SuppressWarnings("unchecked")
    protected ResponseEntity<Object> handleMethodArgumentNotValid(MethodArgumentNotValidException ex, HttpHeaders headers, HttpStatus status, WebRequest request) {
        ResponseEntity<Object> response = super.handleMethodArgumentNotValid(ex, headers, status, request);
        List<FieldError> fieldErrors = ex.getBindingResult().getFieldErrors();
        List<ObjectError> globalErrors = ex.getBindingResult().getGlobalErrors();
        List<String> errors = new ArrayList<>(fieldErrors.size() + globalErrors.size());
        String error;
        for (FieldError fieldError : fieldErrors) {
            error = "Field '" + fieldError.getField() + "' " + fieldError.getDefaultMessage();
            errors.add(error);
        }
        for (ObjectError objectError : globalErrors) {
            error = objectError.getObjectName() + " " + objectError.getDefaultMessage();
            errors.add(error);
        }
        Map<String, Object> responseBody = (Map<String, Object>) response.getBody();
        responseBody.remove("message");
        responseBody.remove("errors");
        responseBody.put("messages", errors);
        return response;
    }

    /**
     * Customizes the response body of all Spring Boot default exception types
     * adding map retrieved from default errorAttributes
     */
    @Override
    @SuppressWarnings("unchecked")
    protected ResponseEntity<Object> handleExceptionInternal(Exception ex, Object body,
                                                             HttpHeaders headers, HttpStatus status, WebRequest request) {

        if (request instanceof ServletWebRequest) {
            ServletWebRequest servletRequest = (ServletWebRequest) request;
            HttpServletRequest httpServletRequest = servletRequest.getNativeRequest(HttpServletRequest.class);
            return (ResponseEntity<Object>) this.handleExceptionInternal(httpServletRequest, status);
        }
        return super.handleExceptionInternal(ex, null, headers, status, request);
    }

    /**
     * Retrieves (from default errorAttributes object)
     * the JSON object to be placed by default in response body.
     */
    private ResponseEntity<?> handleExceptionInternal(HttpServletRequest request, HttpStatus status) {
        WebRequest requestAttributes = new ServletWebRequest(request);
        //missing request parameters used by DefaultErrorAttributes implementation
        requestAttributes.setAttribute("javax.servlet.error.status_code", status.value(), RequestAttributes.SCOPE_REQUEST);
        requestAttributes.setAttribute("javax.servlet.error.request_uri", request.getRequestURI(), RequestAttributes.SCOPE_REQUEST);
        return new ResponseEntity<>(this.errorAttributes.getErrorAttributes(requestAttributes,
                false), status);
    }


}