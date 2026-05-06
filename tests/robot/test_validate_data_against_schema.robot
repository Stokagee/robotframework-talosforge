*** Settings ***
Documentation     Functional acceptance test for keyword 'Validate Data Against Schema' (v0.4.0).
...               Mirrors 1:1 the unit test scenarios from:
...                 - tests/unit/test_validator.py
...                 - tests/unit/test_validator_with_refs.py
...                 - tests/integration/test_validation_url.py (selected source-validation cases)
...               Existing test_validation_phase{1,2,3}.robot files remain as TDD smoke tests
...               and are not modified.

Library     TalosForge
Library     Collections

*** Variables ***
${USER_SCHEMA}          ${CURDIR}${/}..${/}fixtures${/}user.json
${OPENAPI_SPEC}         ${CURDIR}${/}..${/}fixtures${/}test_api_responses.yaml
${ARRAY_SCHEMA}         ${CURDIR}${/}..${/}fixtures${/}array_of_objects.json
${NESTED_SCHEMA}        ${CURDIR}${/}..${/}fixtures${/}nested_object.json
${OAS_FEATURES_SPEC}    ${CURDIR}${/}..${/}fixtures${/}oas30_features.yaml
${REF_CHAIN_SPEC}       ${CURDIR}${/}..${/}fixtures${/}ref_chain_response.yaml

*** Test Cases ***
# ----------------------------------------------------------------------------
# Schema-path branch - happy path
# ----------------------------------------------------------------------------

Validate Schema Path Valid Simple Object
    [Documentation]    Valid data against a local JSON schema passes without exception.
    ...                Mirrors test_validator.py::TestSchemaValidatorHappyPath::test_valid_simple_object.
    [Tags]    validation    schema_path    happy_path
    ${data}=    Create Dictionary    username=honza123    email=honza@example.cz    age=${25}
    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path Without Optional Field
    [Documentation]    Optional fields (here 'age') may be omitted - validation still passes.
    ...                Mirrors test_validator.py::TestSchemaValidatorHappyPath::test_valid_with_optional_fields.
    [Tags]    validation    schema_path    happy_path
    ${data}=    Create Dictionary    username=honza123    email=honza@example.cz
    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path Valid Array Of Objects
    [Documentation]    A root-level array of objects passes when each item conforms to items schema.
    ...                Mirrors test_validator.py::TestSchemaValidatorHappyPath::test_valid_array_of_objects.
    [Tags]    validation    schema_path    happy_path    array
    ${data}=    Evaluate    [{"id": 1}, {"id": 2}]
    Validate Data Against Schema    data=${data}    schema_path=${ARRAY_SCHEMA}

# ----------------------------------------------------------------------------
# Schema-path branch - strict mode (always on)
# ----------------------------------------------------------------------------

Validate Schema Path Extra Field Raises
    [Documentation]    Strict mode - a field not declared in the schema raises DataValidationError.
    ...                Mirrors test_validator.py::TestSchemaValidatorStrictMode::test_extra_field_raises.
    [Tags]    validation    schema_path    strict_mode    negative
    ${data}=    Create Dictionary    username=honza123    email=honza@example.cz    extra_field=x
    Run Keyword And Expect Error    *extra_field*
    ...    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path Missing Required Field Raises
    [Documentation]    Missing required field raises an error mentioning the field and 'required'.
    ...                Mirrors test_validator.py::TestSchemaValidatorStrictMode::test_missing_required_raises.
    [Tags]    validation    schema_path    strict_mode    negative
    ${data}=    Create Dictionary    username=honza123
    Run Keyword And Expect Error    *email*required*
    ...    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path Wrong Type Raises
    [Documentation]    Value of wrong type (string instead of integer) raises an error.
    ...                Mirrors test_validator.py::TestSchemaValidatorStrictMode::test_wrong_type_raises.
    [Tags]    validation    schema_path    strict_mode    negative
    ${data}=    Create Dictionary    username=honza123    email=honza@example.cz    age=thirty
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path Invalid Email Format Raises
    [Documentation]    Value violating format=email raises an error.
    ...                Mirrors test_validator.py::TestSchemaValidatorStrictMode::test_invalid_format_email_raises.
    [Tags]    validation    schema_path    strict_mode    negative
    ${data}=    Create Dictionary    username=honza123    email=not-an-email
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path Below Minimum Raises
    [Documentation]    Number below 'minimum' raises (age=10 vs schema minimum=18).
    ...                Mirrors test_validator.py::TestSchemaValidatorStrictMode::test_below_minimum_raises.
    [Tags]    validation    schema_path    strict_mode    negative
    ${data}=    Create Dictionary    username=honza123    email=honza@example.cz    age=${10}
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path Above Maximum Raises
    [Documentation]    Number above 'maximum' raises (age=200 vs schema maximum=99).
    ...                Mirrors test_validator.py::TestSchemaValidatorStrictMode::test_above_maximum_raises.
    [Tags]    validation    schema_path    strict_mode    negative
    ${data}=    Create Dictionary    username=honza123    email=honza@example.cz    age=${200}
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path String Too Short Raises
    [Documentation]    String shorter than 'minLength' raises (username='ab' vs minLength=5).
    ...                Mirrors test_validator.py::TestSchemaValidatorStrictMode::test_string_too_short_raises.
    [Tags]    validation    schema_path    strict_mode    negative
    ${data}=    Create Dictionary    username=ab    email=honza@example.cz
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema    data=${data}    schema_path=${USER_SCHEMA}

Validate Schema Path Strict Applies To Nested Objects
    [Documentation]    Strict mode also applies to nested objects in a local schema (no $ref).
    ...                Extra field inside the nested 'user' object is rejected.
    ...                Mirrors test_validator.py::TestSchemaValidatorStrictMode::test_strict_applies_to_nested_objects.
    [Tags]    validation    schema_path    strict_mode    negative
    ${user}=    Create Dictionary    name=Jan    extra=x
    ${data}=    Create Dictionary    user=${user}
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema    data=${data}    schema_path=${NESTED_SCHEMA}

# ----------------------------------------------------------------------------
# Schema-path branch - return_errors=True
# ----------------------------------------------------------------------------

Validate Schema Path Return Errors Empty For Valid Data
    [Documentation]    return_errors=True returns an empty list when data is valid.
    ...                Mirrors test_validator.py::TestSchemaValidatorReturnErrors::test_return_errors_empty_on_valid.
    [Tags]    validation    schema_path    return_errors
    ${data}=    Create Dictionary    username=honza123    email=honza@example.cz
    ${errors}=    Validate Data Against Schema
    ...    data=${data}    schema_path=${USER_SCHEMA}    return_errors=${True}
    Should Be Empty    ${errors}

Validate Schema Path Return Errors Lists All Failures
    [Documentation]    return_errors=True aggregates all schema violations into a single list.
    ...                Data here violates: minLength (username), format (email), maximum (age).
    ...                Mirrors test_validator.py::TestSchemaValidatorReturnErrors::test_return_errors_lists_all_failures.
    [Tags]    validation    schema_path    return_errors    negative
    ${data}=    Create Dictionary    username=x    email=bad    age=${200}
    ${errors}=    Validate Data Against Schema
    ...    data=${data}    schema_path=${USER_SCHEMA}    return_errors=${True}
    ${count}=    Get Length    ${errors}
    Should Be True    ${count} >= 3

Validate Schema Path Error Dict Structure
    [Documentation]    Each error entry exposes path / message / validator (and validator_value, instance).
    ...                Mirrors test_validator.py::TestSchemaValidatorReturnErrors::test_error_dict_structure.
    [Tags]    validation    schema_path    return_errors    error_format
    ${data}=    Create Dictionary    username=honza123    email=bad
    ${errors}=    Validate Data Against Schema
    ...    data=${data}    schema_path=${USER_SCHEMA}    return_errors=${True}
    Should Not Be Empty    ${errors}
    ${first}=    Set Variable    ${errors}[0]
    Dictionary Should Contain Key    ${first}    path
    Dictionary Should Contain Key    ${first}    message
    Dictionary Should Contain Key    ${first}    validator
    Dictionary Should Contain Key    ${first}    validator_value
    Dictionary Should Contain Key    ${first}    instance

# ----------------------------------------------------------------------------
# Loaded-OpenAPI branch - $ref resolution + strict mode through references
# ----------------------------------------------------------------------------

Validate Endpoint With Nested Ref Happy Path
    [Documentation]    Valid data against a response schema that resolves through a nested $ref.
    ...                Mirrors test_validator_with_refs.py::TestSchemaValidatorWithRegistry::test_top_level_ref_resolves_via_registry.
    [Tags]    validation    endpoint    ref_resolution    happy_path
    Load Schema    swagger_path=${OPENAPI_SPEC}
    ${address}=    Create Dictionary    city=Praha    country=CZ
    ${data}=    Create Dictionary    id=${1}    name=Jan    address=${address}
    Validate Data Against Schema
    ...    data=${data}    method=POST    endpoint=/users    response_code=${201}

Validate Endpoint Nested Ref Missing Required Raises
    [Documentation]    Missing required field 'city' inside the $ref'd Address raises an error.
    ...                Mirrors test_validator_with_refs.py::TestSchemaValidatorWithRegistry::test_nested_ref_in_property_resolves.
    [Tags]    validation    endpoint    ref_resolution    strict_mode    negative
    Load Schema    swagger_path=${OPENAPI_SPEC}
    ${address}=    Create Dictionary    country=CZ
    ${data}=    Create Dictionary    id=${1}    name=Jan    address=${address}
    Run Keyword And Expect Error    *city*required*
    ...    Validate Data Against Schema
    ...    data=${data}    method=POST    endpoint=/users    response_code=${201}

Validate Endpoint Strict Applies To Refd Component
    [Documentation]    Strict mode applies to components reached via $ref:
    ...                an extra field inside Address (referenced from User) is rejected.
    ...                Mirrors test_validator_with_refs.py::TestSchemaValidatorRegistryStrictMode::test_referenced_object_rejects_extra_field.
    [Tags]    validation    endpoint    ref_resolution    strict_mode    negative
    Load Schema    swagger_path=${OPENAPI_SPEC}
    ${address}=    Create Dictionary    city=Praha    extra=foo
    ${data}=    Create Dictionary    id=${1}    name=Jan    address=${address}
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema
    ...    data=${data}    method=POST    endpoint=/users    response_code=${201}

Validate Endpoint Ref Chain Resolves
    [Documentation]    Response schema with a 3-link $ref chain (A -> B -> C) resolves correctly.
    ...                'hello' satisfies the chain's terminal constraint (string, minLength 2).
    ...                Mirrors test_validator_with_refs.py::TestSchemaValidatorWithRegistry::test_ref_chain_resolves.
    [Tags]    validation    endpoint    ref_resolution    happy_path
    Load Schema    swagger_path=${REF_CHAIN_SPEC}
    Validate Data Against Schema
    ...    data=hello    method=GET    endpoint=/chain    response_code=${200}

Validate Endpoint Ref Chain Violation Raises
    [Documentation]    Violation at the terminal of a $ref chain (minLength=2 vs 'x') raises.
    ...                Mirrors test_validator_with_refs.py::TestSchemaValidatorWithRegistry::test_ref_chain_violation_raises.
    [Tags]    validation    endpoint    ref_resolution    negative
    Load Schema    swagger_path=${REF_CHAIN_SPEC}
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema
    ...    data=x    method=GET    endpoint=/chain    response_code=${200}

# ----------------------------------------------------------------------------
# Loaded-OpenAPI branch - OAS 3.0 specifics (nullable, int32) + enum
# ----------------------------------------------------------------------------

Validate Endpoint Nullable True Accepts None
    [Documentation]    OAS 3.0 'nullable: true' permits None on a typed property.
    ...                Mirrors test_validator.py::TestSchemaValidatorOAS30Specifics::test_nullable_true_accepts_none.
    [Tags]    validation    endpoint    oas30    happy_path
    Load Schema    swagger_path=${OAS_FEATURES_SPEC}
    ${data}=    Create Dictionary    lat=${None}
    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/location    response_code=${200}

Validate Endpoint Nullable False Rejects None
    [Documentation]    Without 'nullable: true', None violates a typed property and raises.
    ...                Mirrors test_validator.py::TestSchemaValidatorOAS30Specifics::test_nullable_false_rejects_none.
    [Tags]    validation    endpoint    oas30    negative
    Load Schema    swagger_path=${OAS_FEATURES_SPEC}
    ${data}=    Create Dictionary    lat=${None}
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/point    response_code=${200}

Validate Endpoint Int32 Format Accepts Integer
    [Documentation]    OAS 3.0 'format: int32' accepts a regular integer value.
    ...                Mirrors test_validator.py::TestSchemaValidatorOAS30Specifics::test_int32_format_accepts_integer.
    [Tags]    validation    endpoint    oas30    happy_path
    Load Schema    swagger_path=${OAS_FEATURES_SPEC}
    ${data}=    Create Dictionary    id=${42}
    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/entity    response_code=${200}

Validate Endpoint Valid Enum Value
    [Documentation]    Value matching an 'enum' constraint passes.
    ...                Mirrors test_validator.py::TestSchemaValidatorEnum::test_valid_enum_value.
    [Tags]    validation    endpoint    enum    happy_path
    Load Schema    swagger_path=${OAS_FEATURES_SPEC}
    ${data}=    Create Dictionary    role=admin
    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/membership    response_code=${200}

Validate Endpoint Invalid Enum Value Raises
    [Documentation]    Value outside an 'enum' constraint raises.
    ...                Mirrors test_validator.py::TestSchemaValidatorEnum::test_invalid_enum_value_raises.
    [Tags]    validation    endpoint    enum    negative
    Load Schema    swagger_path=${OAS_FEATURES_SPEC}
    ${data}=    Create Dictionary    role=superadmin
    Run Keyword And Expect Error    *Validation failed*
    ...    Validate Data Against Schema
    ...    data=${data}    method=GET    endpoint=/membership    response_code=${200}

# ----------------------------------------------------------------------------
# Source-argument validation - error before any HTTP call
# ----------------------------------------------------------------------------

Validate Openapi URL Without Endpoint Raises
    [Documentation]    openapi_url without endpoint raises TalosForgeException
    ...                before any HTTP fetch is attempted.
    ...                Mirrors test_validation_url.py::TestValidateAgainstURL::test_validate_without_endpoint_raises.
    [Tags]    validation    openapi_url    negative
    ${data}=    Create Dictionary    id=${1}
    Run Keyword And Expect Error    *endpoint*
    ...    Validate Data Against Schema
    ...    data=${data}    openapi_url=http://nonexistent.invalid/openapi.yaml
