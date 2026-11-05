package com.fintorq.ptcenter.controller.oem;

import com.fintorq.common.rest.exception.GlobalExceptionHandler;
import com.fintorq.ptcenter.exception.PartnerApiExceptionHandler;
import jakarta.validation.ConstraintViolationException;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Set;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Uses the OEM package to exercise the real Advice selector without changing business controllers.
 */
class OemValidationExceptionContractTest {

    @ParameterizedTest
    @ValueSource(booleans = {true, false})
    void unlistedValidationException_usesCurrentGenericFallback(boolean globalFirst) throws Exception {
        Object global = new GlobalExceptionHandler();
        Object partner = new PartnerApiExceptionHandler();
        var mvc = MockMvcBuilders.standaloneSetup(new ProbeController())
                .setControllerAdvice(globalFirst ? new Object[]{global, partner} : new Object[]{partner, global})
                .build();

        mvc.perform(get("/skill-eval/unlisted-validation"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.code").value(500))
                .andExpect(jsonPath("$.metadata.error_code").value("INTERNAL_ERROR"));
    }

    @RestController
    static class ProbeController {
        @GetMapping("/skill-eval/unlisted-validation")
        public String fail() {
            throw new ConstraintViolationException(Set.of());
        }
    }
}
