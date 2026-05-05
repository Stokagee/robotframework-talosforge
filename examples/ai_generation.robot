*** Settings ***
Documentation     AI Generation Examples with TalosForge
...               Tento soubor demonstruje AI generování pro složité scénáře:
...               - description field pro kontextová data
...               - složité regex patterny
...               - oneOf/anyOf konstrukce

Library            TalosForge
Library            Collections
Library            String

Suite Setup        Log    Starting AI Generation Examples
Suite Teardown     Log    AI Generation Examples Completed

*** Variables ***
# TalosForge AI Configuration
${OPENAI_API_KEY}     %{OPENAI_API_KEY}    # Přečte z environment proměnné
${TAOSFORGE_LOCALE}   cs_CZ
${TAOSFORGE_AI_PROVIDER}    openai

# Schema paths
${ARTICLE_SCHEMA}     ${CURDIR}/schemas/article.json
${COMPLEX_PATTERN_SCHEMA}    ${CURDIR}/schemas/complex_pattern.json
${ONEOF_SCHEMA}       ${CURDIR}/schemas/oneof_anyof.json
${CZECH_SCHEMA}       ${CURDIR}/schemas/czech_specific.json

*** Keywords ***
Generate With AI
    [Documentation]    Generate data using AI model
    [Arguments]    ${schema_path}    ${description}=Generated data
    Log    Generating ${description} with AI...
    ${data}=    Generate Data From Schema
    ...    schema_path=${schema_path}
    ...    use_ai=True
    Log    Generated data: ${data}
    RETURN    ${data}

Generate Without AI
    [Documentation]    Generate data using Faker only (for comparison)
    [Arguments]    ${schema_path}
    Log    Generating with Faker only...
    ${data}=    Generate Data From Schema
    ...    schema_path=${schema_path}
    ...    use_ai=False
    Log    Generated data: ${data}
    RETURN    ${data}

Compare AI vs Faker
    [Documentation]    Generate same schema with AI and Faker, compare results
    [Arguments]    ${schema_path}
    Log    Comparing AI vs Faker generation...

    ${ai_result}=    Generate With AI    ${schema_path}    description=AI version
    ${faker_result}=    Generate Without AI    ${schema_path}

    Log    AI result: ${ai_result}
    Log    Faker result: ${faker_result}

    RETURN    ${ai_result}    ${faker_result}

Verify AI Is Used
    [Documentation]    Check if AI was actually used (look for realistic content)
    [Arguments]    ${data}    ${expected_keywords}    ${min_occurrences}=1
    [Documentation]    Verify that AI-generated content contains expected keywords
    ${combined}=    Set Variable    ${EMPTY}
    FOR    ${key}    IN    @{data.keys()}
        ${value}=    Get From Dictionary    ${data}    ${key}
        ${combined}=    Catenate    ${combined}    ${value}
    END

    ${count}=    Set Variable    0
    FOR    ${keyword}    IN    @{expected_keywords}
        ${contains}=    Run Keyword And Return If    '${combined}' contains '${keyword}'
        ...    Set Variable    1
        ...    ELSE    Set Variable    0
        ${count}=    Evaluate    ${count} + ${contains}
    END

    Log    Found ${count}/${expected_keywords.__len__()} expected keywords
    Should Be True    ${count} >= ${min_occurrences}

*** Test Cases ***
Generate Article With Description
    [Documentation]    Generate article using description field
    [Tags]    ai    description    content
    [Setup]    Log    Testing AI generation with description field

    ${article}=    Generate With AI    ${ARTICLE_SCHEMA}    description=blog article

    # Verify structure
    Should Contain    ${article}    title
    Should Contain    ${article}    content

    # Verify AI generated realistic content
    Should Be True    ${article}[content].__len__() > 100
    Log    Article title: ${article}[title]
    Log    Article content length: ${article}[content].__len__()} characters

Generate Complex Pattern With AI
    [Documentation]    Generate data matching complex regex pattern
    [Tags]    ai    pattern    complex
    [Setup]    Log    Testing AI generation with complex pattern

    ${pattern_data}=    Generate With AI
    ...    ${COMPLEX_PATTERN_SCHEMA}
    ...    description=complex pattern data

    # Verify structure
    Should Contain    ${pattern_data}    product_code
    Log    Generated product code: ${pattern_data}[product_code]

Generate OneOf Schema With AI
    [Documentation]    Generate data from oneOf schema using AI
    [Tags]    ai    oneof    composite
    [Setup]    Log    Testing AI generation with oneOf schema

    ${oneof_data}=    Generate With AI
    ...    ${ONEOF_SCHEMA}
    ...    description=oneOf/anyOf data

    Log    Generated oneOf data: ${oneof_data}

Generate Czech Specific Data
    [Documentation]    Generate Czech-specific data using AI
    [Tags]    ai    czech    locale
    [Setup]    Log    Testing AI generation for Czech-specific formats

    ${czech_data}=    Generate With AI
    ...    ${CZECH_SCHEMA}
    ...    description=Czech specific data

    Log    Generated Czech data: ${czech_data}

Compare AI vs Faker For Article
    [Documentation]    Compare article quality: AI vs Faker
    [Tags]    ai    comparison    faker
    [Setup]    Log    Comparing AI vs Faker for article generation

    ${ai_article}    ${faker_article}=    Compare AI vs Faker    ${ARTICLE_SCHEMA}

    # AI should generate longer, more realistic content
    ${ai_length}=    Get Length    ${ai_article}[content]
    ${faker_length}=    Get Length    ${faker_article}[content]

    Log    AI content length: ${ai_length}
    Log    Faker content length: ${faker_length}

    # AI content is typically much longer and more realistic
    # Note: This depends on the schema definition

Generate Multiple Articles With AI
    [Documentation]    Generate multiple articles, each with AI
    [Tags]    ai    multiple    bulk
    [Setup]    Log    Testing bulk AI generation

    ${articles}=    Generate Data From Schema
    ...    schema_path=${ARTICLE_SCHEMA}
    ...    amount=3
    ...    use_ai=True

    Log    Generated ${articles.__len__()} articles

    FOR    ${article}    IN    @{articles}
        Log    Article: ${article}[title]
        Log    Content preview: ${article}[content][:50]}...
    END

    Should Be Equal As Integers    ${articles.__len__()}    3

Test AI Fallback Behavior
    [Documentation]    Test what happens when AI is unavailable
    [Tags]    ai    fallback    error
    [Setup]    Log    Testing AI fallback behavior

    # This test demonstrates fallback behavior
    # If AI is unavailable, should fall back to Faker
    Log    Note: This test requires no valid API key to see fallback

    # Try to generate with AI (will fallback if no key)
    ${data}=    Generate Data From Schema
    ...    schema_path=${ARTICLE_SCHEMA}
    ...    use_ai=True

    # Should still return data (via Faker fallback)
    Should Not Be Empty    ${data}
    Log    Data generated (may be via fallback): ${data}

Generate Description In Czech
    [Documentation]    Generate content with Czech description
    [Tags]    ai    czech    description
    [Setup]    Log    Testing AI generation with Czech description

    # This would use a schema with Czech description
    # AI should respect the Czech context
    Log    Czech AI generation test
    # ${czech_article}=    Generate With AI    ${CZECH_ARTICLE_SCHEMA}

Generate Nested Object With AI
    [Documentation]    Generate nested object structure with AI
    [Tags]    ai    nested    complex
    [Setup]    Log    Testing AI generation with nested objects

    # Complex schema with nested objects using AI
    Log    Nested AI generation test

Test AI Response Time
    [Documentation]    Measure AI generation response time
    [Tags]    ai    performance    timing
    [Setup]    Log    Testing AI generation performance

    ${start_time}=    Get Time    epoch

    ${data}=    Generate With AI    ${ARTICLE_SCHEMA}    description=performance test

    ${end_time}=    Get Time    epoch
    ${elapsed}=    Evaluate    ${end_time} - ${start_time}

    Log    AI generation took: ${elapsed} seconds
    Log    Generated article title: ${data}[title]

Generate With AI And Validate
    [Documentation]    Generate with AI and validate constraints
    [Tags]    ai    validation    constraints
    [Setup]    Log    Testing AI generation with validation

    ${data}=    Generate With AI    ${ARTICLE_SCHEMA}    description=validated article

    # Validate constraints
    Should Not Be Empty    ${data}[title]
    Should Not Be Empty    ${data}[content]
    Should Be True    ${data}[content].__len__() > 50

    Log    Validation passed for AI-generated data
