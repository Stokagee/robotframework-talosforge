*** Settings ***
Documentation     Acceptance tests for response-code resolution hierarchy
...               (numeric -> 'NXX' range -> default) introduced for issue #2.
...               Mirrors the unit suite tests/unit/test_response_code_fallback.py.

Library     TalosForge
Library     Collections

*** Variables ***
${SPEC_PATH}    ${CURDIR}${/}..${/}fixtures${/}response_code_fallback.yaml

*** Test Cases ***
Numeric Code Wins Over Range And Default
    [Documentation]    Explicit '200' must be picked even when 2XX and default are also defined.
    [Tags]    validation    fallback    precedence
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{data}    exact=ok
    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/exact    response_code=${200}

Range Code Used When Numeric Missing
    [Documentation]    response_code=404 falls through to '4XX' schema when 404 is not explicit.
    [Tags]    validation    fallback    range
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{data}    code=${404}    message=Not Found
    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/range    response_code=${404}

Range Code Bucket Matches By First Digit
    [Documentation]    Any 4xx code resolves to the same '4XX' bucket.
    [Tags]    validation    fallback    range
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{data}    code=${418}    message=I am a teapot
    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/range    response_code=${418}

Default Used When Neither Numeric Nor Range Defined
    [Documentation]    Endpoint with only 'default' catches arbitrary numeric codes.
    [Tags]    validation    fallback    default
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{data}    error=Something broke
    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/default-only    response_code=${500}

Range Schema Mismatch Raises DataValidationError
    [Documentation]    Falling through to 4XX still enforces strict validation - missing required field fails.
    [Tags]    validation    fallback    range    error
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{data}    code=${404}
    TRY
        Validate Data Against Schema
        ...    data=${data}    method=GET    endpoint=/range    response_code=${404}
        Fail    Expected validation error for missing 'message' field
    EXCEPT    *message*    type=GLOB
        No Operation
    END

No Match At Any Level Raises TalosForgeException
    [Documentation]    /range only declares 4XX - a 200 request has no exact, range or default match.
    [Tags]    validation    fallback    error
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{data}    code=${200}    message=ok
    TRY
        Validate Data Against Schema
        ...    data=${data}    method=GET    endpoint=/range    response_code=${200}
        Fail    Expected TalosForgeException for unresolvable status code
    EXCEPT    *status code*    type=GLOB
        No Operation
    END
