package uk.ac.ebi.tsc.tesk.config.security;

import org.springframework.boot.autoconfigure.http.HttpMessageConverters;
import org.springframework.boot.web.servlet.error.ErrorAttributes;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageConverter;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.oauth2.common.exceptions.OAuth2Exception;
import org.springframework.security.oauth2.provider.error.DefaultOAuth2ExceptionRenderer;
import org.springframework.security.oauth2.provider.error.DefaultWebResponseExceptionTranslator;
import org.springframework.security.oauth2.provider.error.OAuth2AuthenticationEntryPoint;
import org.springframework.security.oauth2.provider.error.WebResponseExceptionTranslator;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.servlet.HandlerExceptionResolver;
import org.springframework.web.servlet.mvc.support.DefaultHandlerExceptionResolver;
import org.springframework.web.util.WebUtils;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * @author Ania Niewielska <aniewielska@ebi.ac.uk>
 *
 * Entrypoint for OAuth Errors. Inspired by {@link OAuth2AuthenticationEntryPoint} - sadly needed some repetition.
 * Adds more data to response body object, to conform to ErrorAttributes format plus uses externally supllied messageConverters
 * (Autoconfigured HttpMessageConverters from context are used - {@link ResourceServerConfiguration}
 */
public class CustomAuthenticationEntryPoint extends OAuth2AuthenticationEntryPoint {

    private WebResponseExceptionTranslator exceptionTranslator = new DefaultWebResponseExceptionTranslator();
    private HandlerExceptionResolver handlerExceptionResolver = new DefaultHandlerExceptionResolver();
    private DefaultOAuth2ExceptionRenderer exceptionRenderer = new DefaultOAuth2ExceptionRenderer();
    private final ErrorAttributes errorAttributes;


    CustomAuthenticationEntryPoint(ErrorAttributes errorAttributes, HttpMessageConverters messageConverters) {
        this.errorAttributes = errorAttributes;
        List<HttpMessageConverter<?>> converters = new ArrayList<>();
        converters.addAll(messageConverters.getConverters());
        this.exceptionRenderer.setMessageConverters(converters);
    }

    @Override
    public void commence(HttpServletRequest request, HttpServletResponse response, AuthenticationException authException)
            throws IOException, ServletException {
        try {
            ResponseEntity<OAuth2Exception> result = exceptionTranslator.translate(authException);
            result = enhanceResponse(result, authException);
            WebUtils.exposeErrorRequestAttributes(request, authException, null);
            request.setAttribute(WebUtils.ERROR_STATUS_CODE_ATTRIBUTE, result.getStatusCode().value());
            Map<String, Object> errorBody = errorAttributes.getErrorAttributes(new ServletWebRequest(request), false);
            errorBody.put(OAuth2Exception.ERROR, result.getBody().getOAuth2ErrorCode());
            errorBody.put(OAuth2Exception.DESCRIPTION, result.getBody().getMessage());
            ResponseEntity<Map<String, Object>> newResult = new ResponseEntity<>(errorBody, result.getHeaders(), result.getStatusCode());
            exceptionRenderer.handleHttpEntityResponse(newResult, new ServletWebRequest(request, response));
            response.flushBuffer();
        } catch (ServletException e) {
            // Re-use some of the default Spring dispatcher behaviour - the exception came from the filter chain and
            // not from an MVC handler so it won't be caught by the dispatcher (even if there is one)
            if (handlerExceptionResolver.resolveException(request, response, this, e) == null) {
                throw e;
            }
        } catch (IOException|RuntimeException e) {
            throw e;
        } catch (Exception e) {
            // Wrap other Exceptions. These are not expected to happen
            throw new RuntimeException(e);
        }
    }
}
