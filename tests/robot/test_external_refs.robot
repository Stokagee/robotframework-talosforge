*** Settings ***
Library     TalosForge
Library     Collections

*** Variables ***
${MAIN_SCHEMA}    ${CURDIR}/../fixtures/external_refs_main.yaml

*** Test Cases ***
Load Schema Without External Refs Default
    [Documentation]    Test nacteni schematu bez externich refs (vychozi)
    ...    Tento test by mel fungovat i bez prance knihovny
    Load Schema    swagger_path=${MAIN_SCHEMA}
    ${order}=    Generate Data From Schema    method=POST    endpoint=/orders
    Log    ${order}
    Dictionary Should Contain Key    ${order}    user_id
    Dictionary Should Contain Key    ${order}    product_id

Load Schema With External Refs Enabled
    [Documentation]    Test nacteni schematu s povolenymi externimi refs
    ...    Vyaduje nainstalovanou prance knihovnu
    [Tags]    prance
    Load Schema    swagger_path=${MAIN_SCHEMA}    allow_external_refs=${TRUE}
    ${user}=    Generate Data From Schema    method=POST    endpoint=/users
    Log    ${user}
    Dictionary Should Contain Key    ${user}    name
    Dictionary Should Contain Key    ${user}    email

Load Schema With External Refs For Products
    [Documentation]    Test externi refs pro produkt endpoint
    [Tags]    prance
    Load Schema    swagger_path=${MAIN_SCHEMA}    allow_external_refs=${TRUE}
    ${product}=    Generate Data From Schema    method=POST    endpoint=/products
    Log    ${product}
    Dictionary Should Contain Key    ${product}    name
    Dictionary Should Contain Key    ${product}    price

Load Schema With External Refs Force Reload
    [Documentation]    Test force_reload s externimi refs
    [Tags]    prance
    Load Schema    swagger_path=${MAIN_SCHEMA}    allow_external_refs=${TRUE}
    Load Schema    swagger_path=${MAIN_SCHEMA}    allow_external_refs=${TRUE}    force_reload=${TRUE}
    ${user}=    Generate Data From Schema    method=POST    endpoint=/users
    Log    ${user}
    Dictionary Should Contain Key    ${user}    name

External Refs Fallback Without Prance
    [Documentation]    Overi chovani kdy prance neni nainstalovano
    ...    Pokud prance chybi, mel by se pouzit fallback na zakladni loader
    Load Schema    swagger_path=${MAIN_SCHEMA}    allow_external_refs=${TRUE}
    # Internal refs should still work
    ${order}=    Generate Data From Schema    method=POST    endpoint=/orders
    Dictionary Should Contain Key    ${order}    user_id
    Dictionary Should Contain Key    ${order}    product_id

Multiple Calls With External Refs
    [Documentation]    Test vicenasobne volani se stejnym schematem
    [Tags]    prance
    Load Schema    swagger_path=${MAIN_SCHEMA}    allow_external_refs=${TRUE}
    ${user1}=    Generate Data From Schema    method=POST    endpoint=/users
    ${user2}=    Generate Data From Schema    method=POST    endpoint=/users
    Dictionary Should Contain Key    ${user1}    name
    Dictionary Should Contain Key    ${user2}    name
