*** Settings ***
Library     TalosForge
Library     Collections
Library     OperatingSystem

*** Variables ***
${SCHEMA_PATH}    ${CURDIR}/../sample_schemas/user.json
${CONFIG_EN_US}   ${CURDIR}/../fixtures/test_config_en_US.yml

*** Test Cases ***
Generate Data With English Locale
    [Documentation]    Test locale en_US generates data
    [Setup]    Setup Test Config
    ${user}=    Generate Data From Schema    schema_path=${SCHEMA_PATH}
    Log    ${user}
    Dictionary Should Contain Key    ${user}    username
    Dictionary Should Contain Key    ${user}    email
    [Teardown]    Teardown Test Config

Generate Data With Default Czech Locale
    [Documentation]    Test default locale cs_CZ generates data
    ${user}=    Generate Data From Schema    schema_path=${SCHEMA_PATH}
    Log    ${user}
    Dictionary Should Contain Key    ${user}    username
    Dictionary Should Contain Key    ${user}    email

Generate Data Nested Structure
    [Documentation]    Test generating nested user data structure
    ${user}=    Generate Data From Schema    schema_path=${SCHEMA_PATH}
    Log    ${user}
    # Ověřit základní pole (dle user.json schema: username, email, age)
    Dictionary Should Contain Key    ${user}    username
    Dictionary Should Contain Key    ${user}    email
    Dictionary Should Contain Key    ${user}    age

Generate Data For Multiple Fields
    [Documentation]    Test generating data with multiple field types
    ${user}=    Generate Data From Schema    schema_path=${SCHEMA_PATH}
    Log    ${user}
    # Ověřit různé typy polí
    Dictionary Should Contain Key    ${user}    username
    Dictionary Should Contain Key    ${user}    email
    Dictionary Should Contain Key    ${user}    age

*** Keywords ***
Setup Test Config
    [Documentation]    Copy test config to current directory
    Copy File    ${CONFIG_EN_US}    ${CURDIR}/talosforge.yml

Teardown Test Config
    [Documentation]    Remove test config from current directory
    Remove File    ${CURDIR}/talosforge.yml
