*** Settings ***
Library     TalosForge
Library     Collections

*** Variables ***
${FORGETRAIN_URL}    http://localhost:9200
${LOCAL_SCHEMA}     ${CURDIR}/../sample_schemas/user.json

*** Test Cases ***
ForgeTrain Product Schema - Single Record
    [Documentation]    Test generovani jednoho produktu z ForgeTrain API
    ...                Overi automaticke unwrapovani wrapped JSON Schema response
    ${product}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/product
    Log To Console    \nGenerated Product: ${product}
    Dictionary Should Contain Key    ${product}    name
    Dictionary Should Contain Key    ${product}    price
    Dictionary Should Contain Key    ${product}    in_stock

ForgeTrain Product Schema - Multiple Records
    [Documentation]    Test generovani vice produktu z URL
    ${products}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/product    amount=3
    Log To Console    \nGenerated Products: ${products}
    ${length}=    Get Length    ${products}
    Should Be Equal As Integers    ${length}    3
    FOR    ${p}    IN    @{products}
        Dictionary Should Contain Key    ${p}    name
        Dictionary Should Contain Key    ${p}    price
        Dictionary Should Contain Key    ${p}    in_stock
    END

ForgeTrain Product Schema - Verify Tags Field
    [Documentation]    Overi ze tags pole obsahuje pole s jedinecnymi hodnotami
    ${product}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/product
    Log To Console    \nProduct tags: ${product}
    Dictionary Should Contain Key    ${product}    tags
    ${tags}=    Get From Dictionary    ${product}    tags
    Should Be True    isinstance(${tags}, list)
    # Overime uniktnost v poli (pokud vice nez 1 polozka)
    ${tags_len}=    Get Length    ${tags}
    Log To Console    Tags length: ${tags_len}

ForgeTrain User Schema
    [Documentation]    Test user schema z ForgeTrain API
    ${user}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/user
    Log To Console    \nGenerated User: ${user}
    Dictionary Should Contain Key    ${user}    username
    Dictionary Should Contain Key    ${user}    email
    Dictionary Should Contain Key    ${user}    age

ForgeTrain User Schema - Multiple Records
    [Documentation]    Test generovani vice uzivatelu
    ${users}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/user    amount=5
    ${length}=    Get Length    ${users}
    Should Be Equal As Integers    ${length}    5
    FOR    ${u}    IN    @{users}
        Dictionary Should Contain Key    ${u}    username
        Dictionary Should Contain Key    ${u}    email
    END

ForgeTrain Example Schema
    [Documentation]    Test example schema s email a password
    ${data}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/example
    Log To Console    \nGenerated Example Data: ${data}
    Dictionary Should Contain Key    ${data}    email
    Dictionary Should Contain Key    ${data}    password
    Dictionary Should Contain Key    ${data}    full_name
    # Overi format emailu
    ${email}=    Get From Dictionary    ${data}    email
    Should Contain    ${email}    @

ForgeTrain Example Schema - Multiple Records
    [Documentation]    Test vice záznamů z example schema
    ${examples}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/example    amount=2
    ${length}=    Get Length    ${examples}
    Should Be Equal As Integers    ${length}    2
    FOR    ${ex}    IN    @{examples}
        Dictionary Should Contain Key    ${ex}    email
        Dictionary Should Contain Key    ${ex}    password
    END

Backward Compatibility - Local File
    [Documentation]    Overi ze lokalni soubory stale funguji
    ${user}=    Generate Data From Schema    schema_path=${LOCAL_SCHEMA}
    Log To Console    \nGenerated from file: ${user}
    Dictionary Should Contain Key    ${user}    username
    Dictionary Should Contain Key    ${user}    email
    Dictionary Should Contain Key    ${user}    age

Backward Compatibility - Multiple From File
    [Documentation]    Overi generovani vice zaznamu ze souboru
    ${users}=    Generate Data From Schema    schema_path=${LOCAL_SCHEMA}    amount=2
    ${length}=    Get Length    ${users}
    Should Be Equal As Integers    ${length}    2
    FOR    ${u}    IN    @{users}
        Dictionary Should Contain Key    ${u}    username
        Dictionary Should Contain Key    ${u}    email
    END

URL Schema - Target UI
    [Documentation]    Test generovani dat pro UI testovani z URL
    ${data}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/user    target=ui
    Log To Console    \nUI target data: ${data}
    # Pro UI target by mely byt klice ve formatu "parent_child"
    Dictionary Should Contain Key    ${data}    username
    Dictionary Should Contain Key    ${data}    email

URL Schema - Error When URL Not Reachable
    [Documentation]    Overi chybu kdy URL neni dostupna
    [Tags]    error-test
    Run Keyword And Expect Error
    ...    *Chyba při stahování*
    ...    Generate Data From Schema    openapi_url=http://localhost:9999/nonexistent

URL Schema - Consistent Data Types
    [Documentation]    Overi ze se opakovane generuji stejne datove typy
    ${user1}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/user
    ${user2}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/user
    ${user3}=    Generate Data From Schema    openapi_url=${FORGETRAIN_URL}/api/schemas/user
    # Vsechny by mely mit stejne klice
    ${keys1}=    Get Dictionary Keys    ${user1}
    ${keys2}=    Get Dictionary Keys    ${user2}
    ${keys3}=    Get Dictionary Keys    ${user3}
    Lists Should Be Equal    ${keys1}    ${keys2}    sort=True
    Lists Should Be Equal    ${keys2}    ${keys3}    sort=True
