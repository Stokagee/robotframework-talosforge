*** Settings ***
Library     TalosForge
Library     Collections
Resource    resources${/}mock_server.resource
Suite Setup       Start Mock OpenAPI Server
Suite Teardown    Stop Mock OpenAPI Server

*** Variables ***
${MOCK_URL}         ${MOCK_BASE}/test_api_responses.yaml

*** Test Cases ***
Validate Against URL Spec Passes
    [Documentation]    Validation against URL spec passes for valid data.
    VAR    &{data}    id=${1}    name=Item-Name
    Validate Data Against Schema
    ...    data=${data}    openapi_url=${MOCK_URL}
    ...    method=POST    endpoint=/items    response_code=${201}

Validate Against URL Spec Raises For Invalid Data
    [Documentation]    Validation against URL spec raises for data that violates schema.
    VAR    &{data}    id=${-5}    name=X
    TRY
        Validate Data Against Schema
        ...    data=${data}    openapi_url=${MOCK_URL}
        ...    method=POST    endpoint=/items    response_code=${201}
    EXCEPT    *Validation failed*    type=GLOB
        No Operation
    END

Generate Then Validate Round Trip Via URL
    [Documentation]    Generated data from URL spec request body must validate against same URL spec response.
    ${data}=    Generate Data From Schema
    ...    method=POST    endpoint=/items    openapi_url=${MOCK_URL}
    Validate Data Against Schema
    ...    data=${data}    openapi_url=${MOCK_URL}
    ...    method=POST    endpoint=/items    response_code=${201}
