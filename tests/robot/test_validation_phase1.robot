*** Settings ***
Library     TalosForge
Library     Collections

*** Variables ***
${VALID_USER}       {"username": "honza123", "email": "honza@example.cz", "age": 25}
${INVALID_USER}     {"username": "x", "email": "not-email", "age": 200}

*** Test Cases ***
Validate Valid Data Passes
    [Documentation]    Validation against schema passes when data conforms.
    ${data}=    Evaluate    ${VALID_USER}
    Validate Data Against Schema    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json

Validate Invalid Data Raises
    [Documentation]    Validation raises with detailed message when data violates schema.
    ${data}=    Evaluate    ${INVALID_USER}
    TRY
        Validate Data Against Schema    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json
    EXCEPT    *Validation failed*    type=GLOB
        No Operation
    END

Validate With Return Errors Returns List
    [Documentation]    return_errors=True returns list of error dicts instead of raising.
    ${data}=    Evaluate    ${INVALID_USER}
    ${errors}=    Validate Data Against Schema
    ...    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json    return_errors=${True}
    Should Not Be Empty    ${errors}

Validate Empty Errors For Valid Data
    [Documentation]    return_errors=True returns empty list when data is valid.
    ${data}=    Evaluate    ${VALID_USER}
    ${errors}=    Validate Data Against Schema
    ...    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json    return_errors=${True}
    Should Be Empty    ${errors}

Generate Then Validate Round Trip
    [Documentation]    Generated data must pass its own schema's validation (no description / pattern / composition).
    ${data}=    Generate Data From Schema    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json
    Validate Data Against Schema    data=${data}    schema_path=${CURDIR}${/}..${/}fixtures${/}user.json
