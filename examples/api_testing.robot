*** Settings ***
Documentation     API Testing Examples with TalosForge
...               Tento soubor demonstruje integraci TalosForge s RequestsLibrary
...               pro testování REST API.

Library            TalosForge
Library            RequestsLibrary
Library            Collections
Library            String

Suite Setup        Initialize Test Environment
Suite Teardown     Cleanup Test Environment

*** Variables ***
# API Configuration
${BASE_URL}           https://jsonplaceholder.typicode.com
${API_SESSION}        jsonplaceholder_api

# TalosForge Configuration
${TAOSFORGE_LOCALE}   en_US

# Schema paths
${USER_SCHEMA}        ${CURDIR}/schemas/user.json
${POST_SCHEMA}        ${CURDIR}/schemas/post.json
${SWAGGER_PATH}       ${CURDIR}/schemas/petstore.yaml

*** Keywords ***
Initialize Test Environment
    [Documentation]    Setup API session and log configuration
    Log    Starting API Testing Suite
    Log    Base URL: ${BASE_URL}
    Log    Locale: ${TAOSFORGE_LOCALE}
    Create Session    ${API_SESSION}    ${BASE_URL}
    Log    API session created successfully

Cleanup Test Environment
    [Documentation]    Cleanup after all tests
    Log    Cleaning up test environment
    Delete All Sessions

Generate User Data
    [Documentation]    Generate user data using TalosForge
    [Arguments]    ${use_ai}=${False}
    ${user}=    Generate Data From Schema
    ...    schema_path=${USER_SCHEMA}
    ...    use_ai=${use_ai}
    Log    Generated user: ${user}
    RETURN    ${user}

Create User Via API
    [Documentation]    Send generated user data to API
    [Arguments]    ${user_data}
    ${response}=    POST On Session
    ...    ${API_SESSION}
    ...    /users
    ...    json=${user_data}
    Log    Response status: ${response.status_code}
    Log    Response body: ${response.content}
    RETURN    ${response}

*** Test Cases ***
Generate User With Faker
    [Documentation]    Generate user data using Faker (fast, offline)
    [Tags]    faker    smoke
    ${user}=    Generate User Data    use_ai=${False}
    Should Contain    ${user}    email
    Should Contain    ${user}    username
    Log    Successfully generated user with Faker

Generate User With AI
    [Documentation]    Generate user data using AI (if API key available)
    [Tags]    ai    regression
    ${user}=    Generate User Data    use_ai=${True}
    Should Contain    ${user}    email
    Should Contain    ${user}    username
    Log    Successfully generated user with AI

Generate Multiple Users
    [Documentation]    Generate multiple user records at once
    [Tags]    bulk    multiple
    ${users}=    Generate Data From Schema
    ...    schema_path=${USER_SCHEMA}
    ...    amount=5
    Log    Generated ${users.__len__()} users
    FOR    ${user}    IN    @{users}
        Log    User: ${user}[username] - ${user}[email]
    END
    Should Be Equal As Integers    ${users.__len__()}    5

Generate And Send To API
    [Documentation]    Generate user data and send to real API
    [Tags]    integration    api
    [Setup]    Log    Starting integration test with real API

    # Generate data
    ${user_data}=    Generate User Data

    # Send to API
    ${response}=    Create User Via API    ${user_data}

    # Verify response
    Status Should Be    201    ${response.status_code}

    # Verify returned data contains our input
    ${response_json}=    Set Variable    ${response.json()}
    Should Be Equal    ${response_json}[username]    ${user_data}[username]
    Should Be Equal    ${response_json}[email]    ${user_data}[email]

    Log    Integration test passed - user created via API

Generate Post With Nested Structure
    [Documentation]    Generate post with nested user object
    [Tags]    nested    complex
    ${post}=    Generate Data From Schema
    ...    schema_path=${POST_SCHEMA}
    Log    Generated post: ${post}
    Should Contain    ${post}    title
    Should Contain    ${post}    body
    Log    Successfully generated post with nested structure

Load OpenAPI And Generate
    [Documentation]    Load OpenAPI schema and generate data for endpoint
    [Tags]    openapi    swagger
    [Setup]    Log    Loading OpenAPI schema from ${SWAGGER_PATH}

    # Note: This example assumes you have a valid OpenAPI schema
    # Load Schema    swagger_path=${SWAGGER_PATH}
    # ${pet_data}=    Generate Data From Schema    endpoint=POST /pet
    # Log    Generated pet data: ${pet_data}

    Log    OpenAPI example - add your own swagger.yaml file

Generate For Different Locales
    [Documentation]    Demonstrate locale-specific generation
    [Tags]    locale    i18n
    [Setup]    Log    Testing with different locales

    # Generate with default locale (en_US from Variables)
    ${user_en}=    Generate Data From Schema    schema_path=${USER_SCHEMA}
    Log    English locale user: ${user_en}[username]

    Log    Locale test completed
