*** Settings ***
Documentation     URL-spec error scenarios for keyword 'Validate Data Against Schema'.
...               Mirrors the error-path tests from tests/integration/test_validation_url.py:
...                 - 404 URL                            -> TestValidateURLErrorHandling::test_404_url_raises_talosforge_exception
...                 - Invalid YAML at URL                -> TestValidateURLErrorHandling::test_invalid_yaml_url_raises
...                 - Unknown endpoint in URL spec       -> TestValidateAgainstURL::test_validate_unknown_endpoint_raises
...                 - Unknown response_code in URL spec  -> TestValidateAgainstURL::test_validate_unknown_response_code_raises
...
...               The caching scenario (TestValidateURLCaching::test_url_fetched_only_once_per_session)
...               is intentionally NOT mirrored here - counting HTTP fetches without
...               monkey-patching is outside Robot's idiomatic scope and is already
...               covered by the Python integration test.

Library     TalosForge
Library     Collections
Resource    resources${/}mock_server.resource

Suite Setup       Start Mock OpenAPI Server
Suite Teardown    Stop Mock OpenAPI Server

*** Variables ***
${MOCK_PORT}            18080
${MOCK_BASE}            http://127.0.0.1:${MOCK_PORT}
${MOCK_URL_VALID}       ${MOCK_BASE}/test_api_responses.yaml
${MOCK_URL_404}         ${MOCK_BASE}/this_does_not_exist.yaml
${MOCK_URL_INVALID}     ${MOCK_BASE}/invalid_yaml.yaml

*** Test Cases ***
Validate URL 404 Raises
    [Documentation]    URL returning HTTP 404 raises TalosForgeException wrapping the requests error.
    ...                Mirrors test_validation_url.py::TestValidateURLErrorHandling::test_404_url_raises_talosforge_exception.
    [Tags]    validation    openapi_url    error_handling    negative
    ${data}=    Create Dictionary    id=${1}
    Run Keyword And Expect Error    *404*
    ...    Validate Data Against Schema
    ...    data=${data}    openapi_url=${MOCK_URL_404}
    ...    method=GET    endpoint=/items    response_code=${200}

Validate URL Invalid YAML Raises
    [Documentation]    URL serving malformed YAML raises TalosForgeException
    ...                ('Neplatný YAML formát ...').
    ...                Mirrors test_validation_url.py::TestValidateURLErrorHandling::test_invalid_yaml_url_raises.
    [Tags]    validation    openapi_url    error_handling    negative
    ${data}=    Create Dictionary    id=${1}
    Run Keyword And Expect Error    *YAML*
    ...    Validate Data Against Schema
    ...    data=${data}    openapi_url=${MOCK_URL_INVALID}
    ...    method=GET    endpoint=/items    response_code=${200}

Validate URL Unknown Endpoint Raises
    [Documentation]    Endpoint not present in the URL-fetched spec raises TalosForgeException.
    ...                Mirrors test_validation_url.py::TestValidateAgainstURL::test_validate_unknown_endpoint_raises.
    [Tags]    validation    openapi_url    error_handling    negative
    ${data}=    Create Dictionary    id=${1}
    Run Keyword And Expect Error    *not found*
    ...    Validate Data Against Schema
    ...    data=${data}    openapi_url=${MOCK_URL_VALID}
    ...    method=GET    endpoint=/nonexistent    response_code=${200}

Validate URL Unknown Response Code Raises
    [Documentation]    Endpoint exists in the URL-fetched spec but the requested response_code does not.
    ...                Mirrors test_validation_url.py::TestValidateAgainstURL::test_validate_unknown_response_code_raises.
    [Tags]    validation    openapi_url    error_handling    negative
    ${data}=    Create Dictionary    id=${1}
    Run Keyword And Expect Error    *status code*
    ...    Validate Data Against Schema
    ...    data=${data}    openapi_url=${MOCK_URL_VALID}
    ...    method=POST    endpoint=/items    response_code=${999}
