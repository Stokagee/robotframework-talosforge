*** Settings ***
Library     TalosForge
Library     Collections

*** Variables ***
${SCHEMA_PATH}      ${CURDIR}${/}..${/}sample_schemas${/}user.json
${REF_TEST_PATH}    ${CURDIR}${/}..${/}fixtures${/}ref_test.yaml

*** Test Cases ***
Test Import And Initialization
    [Documentation]    Ověří, že se TalosForge dá importovat a inicializovat
    No Operation

Test Generate Data From Schema Path
    [Documentation]    Ověří generování dat z lokálního JSON schématu (Fáze 1 - placeholder)
    ${user}=    Generate Data From Schema    schema_path=${SCHEMA_PATH}
    Log    ${user}
    ${keys}=    Get Dictionary Keys    ${user}
    Should Contain    ${keys}    username
    Should Contain    ${keys}    email
    Should Contain    ${keys}    age

Test Generate Multiple Records
    [Documentation]    Ověří generování více záznamů
    ${users}=    Generate Data From Schema    schema_path=${SCHEMA_PATH}    amount=3
    Log    ${users}
    Length Should Be    ${users}    3

Test Error When No Source Specified
    [Documentation]    Ověří chybu, když není specifikován žádný zdroj
    TRY
        Generate Data From Schema
    EXCEPT    *Musí být specifikován alespoň jeden zdroj dat*    type=GLOB
        No Operation
    END

Test Error When Multiple Sources Specified
    [Documentation]    Ověří chybu, když je specifikováno více zdrojů
    TRY
        Generate Data From Schema    schema_path=${SCHEMA_PATH}    endpoint=POST /users
    EXCEPT    *Musí být specifikován právě jeden zdroj dat*    type=GLOB
        No Operation
    END

Test Generate With Ref Resolution
    [Documentation]    Ověří generování dat z OpenAPI s $ref referencemi
    Load Schema    swagger_path=${REF_TEST_PATH}
    ${user}=    Generate Data From Schema    endpoint=POST /users
    Log    ${user}
    ${keys}=    Get Dictionary Keys    ${user}
    Should Contain    ${keys}    name
    Should Contain    ${keys}    email
    # age je volitelné

Test Generate With Ref Resolution Method Parameter
    [Documentation]    Ověří generování dat s novým parametrem method= a $ref
    Load Schema    swagger_path=${REF_TEST_PATH}
    ${product}=    Generate Data From Schema    method=POST    endpoint=/products
    Log    ${product}
    ${keys}=    Get Dictionary Keys    ${product}
    Should Contain    ${keys}    name

Test Generate With Recursive Ref Resolution
    [Documentation]    Ověří rekurzivní rozlišení $ref (schéma obsahuje další $ref)
    Load Schema    swagger_path=${REF_TEST_PATH}
    ${extended}=    Generate Data From Schema    method=POST    endpoint=/nested
    Log    ${extended}
    ${keys}=    Get Dictionary Keys    ${extended}
    Should Contain    ${keys}    id
    Should Contain    ${keys}    username
