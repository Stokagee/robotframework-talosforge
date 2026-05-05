*** Settings ***
Documentation     UI Testing Examples with TalosForge
...               Tento soubor demonstruje integraci TalosForge s Browser library
...               pro vyplňování formulářů v UI testech.

Library            TalosForge
Library            Browser
Library            Collections

Suite Setup        Set Browser Timeout    30 seconds

*** Variables ***
# TalosForge Configuration
${TAOSFORGE_LOCALE}   cs_CZ

# Schema paths
${LOGIN_SCHEMA}       ${CURDIR}/schemas/login.json
${REGISTER_SCHEMA}    ${CURDIR}/schemas/registration.json
${USER_PROFILE_SCHEMA}    ${CURDIR}/schemas/user_profile.json

# Test URLs
${LOGIN_URL}          https://example.com/login
${REGISTER_URL}       https://example.com/register

*** Keywords ***
Generate Form Data
    [Documentation]    Generate form data using TalosForge with target=ui
    [Arguments]    ${schema_path}
    ${form_data}=    Generate Data From Schema
    ...    schema_path=${schema_path}
    ...    target=ui
    Log    Generated form data: ${form_data}
    RETURN    ${form_data}

Fill Login Form
    [Documentation]    Fill login form with generated data
    [Arguments]    ${form_data}
    Fill Text    id=username    ${form_data}[username]
    Fill Text    id=password    ${form_data}[password]
    Log    Login form filled with username: ${form_data}[username]

Fill Registration Form
    [Documentation]    Fill complete registration form
    [Arguments]    ${form_data}
    Fill Text    id=first_name    ${form_data}[first_name]
    Fill Text    id=last_name     ${form_data}[last_name]
    Fill Text    id=email         ${form_data}[email]
    Fill Text    id=username      ${form_data}[username]
    Fill Text    id=password      ${form_data}[password]
    Fill Text    id=confirm_password    ${form_data}[password]
    Log    Registration form filled

Fill Profile Form
    [Documentation]    Fill user profile form with nested data
    [Arguments]    ${form_data}
    Fill Text    id=full_name    ${form_data}[full_name]
    Fill Text    id=bio          ${form_data}[bio]
    Fill Text    id=website      ${form_data}[website]
    Fill Text    id=location     ${form_data}[location]
    Log    Profile form filled

Verify Form Submission
    [Documentation]    Verify form was submitted successfully
    Get Url    ==    ${SUCCESS_URL}    # Adjust to actual success URL
    Log    Form submitted successfully

*** Test Cases ***
Generate Login Form Data
    [Documentation]    Generate login form data with target=ui
    [Tags]    login    form    ui
    ${form_data}=    Generate Form Data    ${LOGIN_SCHEMA}
    Should Contain    ${form_data}    username
    Should Contain    ${form_data}    password
    Log    Generated login form data: ${form_data}[username]

Generate Registration Form Data
    [Documentation]    Generate registration form with all fields
    [Tags]    registration    form    complex
    ${form_data}=    Generate Form Data    ${REGISTER_SCHEMA}
    Should Contain    ${form_data}    first_name
    Should Contain    ${form_data}    last_name
    Should Contain    ${form_data}    email
    Should Contain    ${form_data}    username
    Should Contain    ${form_data}    password
    Log    Generated registration form for: ${form_data}[email]

Generate Profile Form Data
    [Documentation]    Generate user profile form data
    [Tags]    profile    form    ui
    ${form_data}=    Generate Form Data    ${USER_PROFILE_SCHEMA}
    Should Contain    ${form_data}    full_name
    Should Contain    ${form_data}    bio
    Log    Generated profile data for: ${form_data}[full_name]

API vs UI Target Comparison
    [Documentation]    Compare target=api vs target=ui output
    [Tags]    comparison    target
    ${api_data}=    Generate Data From Schema
    ...    schema_path=${LOGIN_SCHEMA}
    ...    target=api
    ${ui_data}=    Generate Data From Schema
    ...    schema_path=${LOGIN_SCHEMA}
    ...    target=ui
    Log    API target: ${api_data}
    Log    UI target: ${ui_data}
    # Both should have same keys
    Should Be Equal    ${api_data.keys()}    ${ui_data.keys()}
    Log    API and UI targets produce same structure

Generate Multiple Form Data Sets
    [Documentation]    Generate multiple form datasets
    [Tags]    multiple    bulk    form
    ${forms}=    Generate Data From Schema
    ...    schema_path=${REGISTER_SCHEMA}
    ...    target=ui
    ...    amount=3
    Log    Generated ${forms.__len__()} form datasets
    Should Be Equal As Integers    ${forms.__len__()}    3
    FOR    ${form}    IN    @{forms}
        Log    Form dataset: ${form}[email]
    END

Mock Login Flow
    [Documentation]    Simulate login flow with generated data
    [Tags]    login    mock    flow
    [Setup]    Log    Starting mock login flow test

    # Generate login credentials
    ${credentials}=    Generate Form Data    ${LOGIN_SCHEMA}

    # Simulate filling form (without actual browser)
    Log    Filling username field with: ${credentials}[username]
    Log    Filling password field with: [HIDDEN]

    # Verify we have required fields
    Should Not Be Empty    ${credentials}[username]
    Should Not Be Empty    ${credentials}[password]

    Log    Mock login flow completed successfully

Mock Registration Flow
    [Documentation]    Simulate complete registration flow
    [Tags]    registration    mock    flow
    [Setup]    Log    Starting mock registration flow test

    # Generate registration data
    ${reg_data}=    Generate Form Data    ${REGISTER_SCHEMA}

    # Simulate filling form step by step
    Log    Step 1: Filling personal info
    Log    First name: ${reg_data}[first_name]
    Log    Last name: ${reg_data}[last_name]

    Log    Step 2: Filling contact info
    Log    Email: ${reg_data}[email]

    Log    Step 3: Filling account info
    Log    Username: ${reg_data}[username]
    Log    Password: [HIDDEN]

    # Verify all required fields
    Should Not Be Empty    ${reg_data}[first_name]
    Should Not Be Empty    ${reg_data}[last_name]
    Should Not Be Empty    ${reg_data}[email]
    Should Not Be Empty    ${reg_data}[username]
    Should Not Be Empty    ${reg_data}[password]

    Log    Mock registration flow completed

Generate With Different Locales
    [Documentation]    Generate form data for different locales
    [Tags]    locale    i18n    form
    [Setup]    Log    Testing locale-specific form generation

    # Default locale (cs_CZ from Variables)
    ${form_cs}=    Generate Data From Schema
    ...    schema_path=${USER_PROFILE_SCHEMA}
    ...    target=ui
    Log    Czech locale name: ${form_cs}[full_name]

    Log    Locale test completed

Generate Nested Form Data
    [Documentation]    Generate form data with nested structure
    [Tags]    nested    complex    form
    [Setup]    Log    Testing nested form structure generation

    # This would work with a schema that has nested objects
    # The target=ui flattens the structure for form filling
    ${nested_form}=    Generate Data From Schema
    ...    schema_path=${USER_PROFILE_SCHEMA}
    ...    target=ui
    Log    Nested form data: ${nested_form}

    Log    Nested form data generated successfully
