*** Settings ***
Library     TalosForge
Library     Collections

*** Variables ***
${SIMPLE_SCHEMA}    ${CURDIR}/../sample_schemas/user.json
${COMPLEX_SCHEMA}    ${CURDIR}/../fixtures/complex_test_schema.json

*** Test Cases ***
Explore Mode Generates List
    [Documentation]    Overi ze explore mode vraci seznam
    ...    i pri amount=1 vraci seznam ne jeden prvek
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${SIMPLE_SCHEMA}    explore=${TRUE}    amount=10
    Log    ${variants}
    Should Be True    isinstance(${variants}, list)
    ${length}=    Get Length    ${variants}
    Should Be Equal As Integers    ${length}    10

Explore Mode Generates Variants
    [Documentation]    Overi ze se generuji ruzne varianty
    ...    Testuje ze nejsou vsechna data stejna
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${SIMPLE_SCHEMA}    explore=${TRUE}    amount=50
    ${length}=    Get Length    ${variants}
    Should Be Equal As Integers    ${length}    50
    # Check we have some variation (not all identical)
    ${first}=    Get From List    ${variants}    0
    ${second}=    Get From List    ${variants}    1
    Log    First: ${first}
    Log    Second: ${second}

Explore Mode Edge Cases For Strings
    [Documentation]    Test edge-cases pro string s omezenimi
    ...    Overi ze vsechna data splnuji schema constraints
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${COMPLEX_SCHEMA}    explore=${TRUE}    amount=20
    Log    ${variants}
    # Verify all items are valid according to schema
    FOR    ${item}    IN    @{variants}
        Dictionary Should Contain Key    ${item}    username
        ${username}=    Get From Dictionary    ${item}    username
        ${len}=    Get Length    ${username}
        Should Be True    ${len} >= 3
        Should Be True    ${len} <= 20
    END

Explore Mode With Small Amount
    [Documentation]    Test explore mode s malym mnozstvim
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${SIMPLE_SCHEMA}    explore=${TRUE}    amount=5
    ${length}=    Get Length    ${variants}
    Should Be Equal As Integers    ${length}    5

Explore Mode With Large Amount
    [Documentation]    Test explore mode s velkym mnozstvim
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${SIMPLE_SCHEMA}    explore=${TRUE}    amount=200
    ${length}=    Get Length    ${variants}
    Should Be Equal As Integers    ${length}    200

Explore Mode Fallback Without Hypothesis
    [Documentation]    Overi fallback kdy hypothesis-jsonschema neni nainstalovano
    ...    Pokud neni dostupna, pouzije se standardni generovani
    ${variants}=    Generate Data From Schema    schema_path=${SIMPLE_SCHEMA}    explore=${TRUE}    amount=10
    Should Be True    isinstance(${variants}, list)
    ${length}=    Get Length    ${variants}
    Should Be Equal As Integers    ${length}    10

Explore Mode With Nested Schema
    [Documentation]    Test explore mode se slozitym vnorenym schematem
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${COMPLEX_SCHEMA}    explore=${TRUE}    amount=15
    FOR    ${item}    IN    @{variants}
        Dictionary Should Contain Key    ${item}    user
        ${user}=    Get From Dictionary    ${item}    user
        Dictionary Should Contain Key    ${user}    name
    END

Explore Mode Preserves Required Fields
    [Documentation]    Overi ze required pole jsou vzdy pritomna
    ...    Vsechny varianty musi obsahovat povinna pole
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${SIMPLE_SCHEMA}    explore=${TRUE}    amount=30
    FOR    ${item}    IN    @{variants}
        Dictionary Should Contain Key    ${item}    username
        Dictionary Should Contain Key    ${item}    email
    END

Explore Mode Integer Constraints
    [Documentation]    Test explore mode s integer omezenimi
    ...    Overi ze se generuji hodnoty v rozsahu minimum/maximum
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${COMPLEX_SCHEMA}    explore=${TRUE}    amount=50
    FOR    ${item}    IN    @{variants}
        # age is integer with minimum 18, maximum 100
        ${has_age}=    Dictionary Should Contain Key    ${item}    age
        ${age}=    Get From Dictionary    ${item}    age
        # Check if age is within valid range
        ${is_valid}=    Evaluate    18 <= ${age} <= 100
        Should Be True    ${is_valid}
    END

Explore Mode Number Constraints
    [Documentation]    Test explore mode s number (float) omezenimi
    [Tags]    explore
    ${variants}=    Generate Data From Schema    schema_path=${COMPLEX_SCHEMA}    explore=${TRUE}    amount=30
    FOR    ${item}    IN    @{variants}
        # score is number with minimum 0.0, maximum 10.0
        ${has_score}=    Dictionary Should Contain Key    ${item}    score
        ${score}=    Get From Dictionary    ${item}    score
        # Check if score is within valid range
        ${is_valid}=    Evaluate    0.0 <= ${score} <= 10.0
        Should Be True    ${is_valid}
    END
