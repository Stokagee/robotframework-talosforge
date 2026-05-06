*** Settings ***
Library     TalosForge
Library     Collections

*** Variables ***
${REGEX_SCHEMA}    ${CURDIR}/../fixtures/regex_patterns.json

*** Test Cases ***
Generate Data With Pure Regex Pattern
    [Documentation]    Test generovani s jednoduchym regex patternem
    ...    Pouziva rstr knihovnu pro presne generovani z regularnich vyrazu
    ...    Custom code pole neni v kontextovem parseru, takze se pouzije ciste rstr
    ${data}=    Generate Data From Schema    schema_path=${REGEX_SCHEMA}
    Log    ${data}
    Dictionary Should Contain Key    ${data}    custom_code
    # Verify pattern matches (e.g., AB1234)
    ${code}=    Get From Dictionary    ${data}    custom_code
    Should Match Regexp    ${code}    ^[A-Z]{2}\\d{4}$

Generate Data With Complex Regex Pattern
    [Documentation]    Test slozitejsi regex pattern pro custom ID
    ${data}=    Generate Data From Schema    schema_path=${REGEX_SCHEMA}
    Dictionary Should Contain Key    ${data}    custom_id
    ${id}=    Get From Dictionary    ${data}    custom_id
    Log    Generated ID: ${id}
    Length Should Be    ${id}    9
    Should Match Regexp    ${id}    ^ID-\\d{3}-[A-Z]{2}$

Generate Data With Regex And Constraints
    [Documentation]    Test regex s minLength/ maxLength omezenim
    ${data}=    Generate Data From Schema    schema_path=${REGEX_SCHEMA}
    Dictionary Should Contain Key    ${data}    username
    ${username}=    Get From Dictionary    ${data}    username
    ${len}=    Get Length    ${username}
    Should Be True    ${len} >= 5
    Should Be True    ${len} <= 15
    Should Match Regexp    ${username}    ^[a-zA-Z0-9_]+$

Regex Pattern Consistency
    [Documentation]    Overi ze se stejny pattern generuje konzistentni data
    ${data1}=    Generate Data From Schema    schema_path=${REGEX_SCHEMA}
    ${data2}=    Generate Data From Schema    schema_path=${REGEX_SCHEMA}
    ${code1}=    Get From Dictionary    ${data1}    custom_code
    ${code2}=    Get From Dictionary    ${data2}    custom_code
    # Both should match the pattern (but can be different values)
    Should Match Regexp    ${code1}    ^[A-Z]{2}\\d{4}$
    Should Match Regexp    ${code2}    ^[A-Z]{2}\\d{4}$

Rstr Fallback Behavior
    [Documentation]    Overi ze se neco vygeneruje i bez rstr
    ...    Testuje fallback chovani na puvodni heuristiky
    ${data}=    Generate Data From Schema    schema_path=${REGEX_SCHEMA}
    Dictionary Should Contain Key    ${data}    custom_code
    Dictionary Should Contain Key    ${data}    custom_id
    Dictionary Should Contain Key    ${data}    username

Context Parser Priority Over Pattern
    [Documentation]    Overi ze kontextovy parser ma prednost pred pattern
    ...    Pro zname pole jako postal_code se pouzije Faker misto rstr
    ${data}=    Generate Data From Schema    schema_path=${REGEX_SCHEMA}
    Dictionary Should Contain Key    ${data}    postal_code
    Dictionary Should Contain Key    ${data}    phone_number
    # Tyto hodnoty mohou obsahovat formatovani (napr. mezery)
    # protoze kontextovy parser ma prednost
    ${postal}=    Get From Dictionary    ${data}    postal_code
    Log    Postal code (may have formatting): ${postal}
