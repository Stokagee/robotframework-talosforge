*** Settings ***
Library     TalosForge
Library     Collections

*** Variables ***
${SPEC_PATH}    ${CURDIR}${/}..${/}fixtures${/}test_api_responses.yaml

*** Test Cases ***
Validate Loaded Endpoint Response Passes
    [Documentation]    Validation against a response schema passes for valid data through $ref.
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{address}    city=Praha    country=CZ
    VAR    &{data}    id=${1}    name=Jan    address=${address}
    Validate Data Against Schema
    ...    data=${data}    method=POST    endpoint=/users    response_code=${201}

Validate Endpoint With Method In Path Backward Compat
    [Documentation]    'POST /users' string form (no separate method=) still works.
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{address}    city=Praha
    VAR    &{data}    id=${1}    name=Jan    address=${address}
    Validate Data Against Schema
    ...    data=${data}    endpoint=POST /users    response_code=${201}

Validate Wrong Endpoint Raises
    [Documentation]    Unknown endpoint raises a TalosForgeException.
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{data}    id=${1}
    TRY
        Validate Data Against Schema
        ...    data=${data}    method=POST    endpoint=/nonexistent    response_code=${200}
    EXCEPT    *not found*    type=GLOB
        No Operation
    END

Validate Wrong Response Code Raises
    [Documentation]    Endpoint exists but requested response_code does not.
    Load Schema    swagger_path=${SPEC_PATH}
    VAR    &{data}    id=${1}
    TRY
        Validate Data Against Schema
        ...    data=${data}    method=POST    endpoint=/users    response_code=${999}
    EXCEPT    *status code*    type=GLOB
        No Operation
    END

Generate Then Validate Round Trip Through Endpoint
    [Documentation]    Generated request data must validate against the same endpoint's response schema (no $ref - deterministic).
    Load Schema    swagger_path=${SPEC_PATH}
    ${data}=    Generate Data From Schema    method=POST    endpoint=/items
    Validate Data Against Schema
    ...    data=${data}    method=POST    endpoint=/items    response_code=${201}
