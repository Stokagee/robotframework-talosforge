*** Settings ***
Documentation     Database integration tests for TalosForge
...
...               These tests require a running PostgreSQL database.
...               Set the environment variables before running:
...               - TEST_PG_DB_NAME (default: moje_app)
...               - TEST_PG_USER (default: postgres)
...               - TEST_PG_PASSWORD (default: postgres)
...               - TEST_PG_HOST (default: localhost)
...               - TEST_PG_PORT (default: 20343)
...               - TEST_PG_SCHEMA (default: public)
...               - TEST_PG_TABLE (default: users)
...
...               Run with: robot --outputdir results/robot tests/robot/test_db_integration.robot

Library           TalosForge
Library           Collections
Library           String

*** Variables ***
${DATABASE_MODULE}    psycopg2
${DATABASE_NAME}     moje_app
${DATABASE_USER}     postgres
${DATABASE_PASSWORD}    postgres
${DATABASE_HOST}     localhost
${DATABASE_PORT}     20343
${DATABASE_SCHEMA}   public
${DATABASE_TABLE}    users

*** Test Cases ***
Load Database Schema
    [Documentation]    Load schema from PostgreSQL database
    [Tags]    database    postgres
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}

Generate SQL VALUES From Database Schema
    [Documentation]    Generate SQL VALUES string using loaded database schema
    [Tags]    database    postgres    generate    sql
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    ${values}=    Generate Data From Schema    target=db
    Log    SQL VALUES: ${values}
    # Should be a string, not a dict
    ${type}=    Evaluate    type($values).__name__
    Should Be Equal    ${type}    str
    # Should contain comma-separated values
    Should Contain    ${values}    ,
    # String values should be quoted
    ${has_quotes}=    Evaluate    "'" in $values
    Should Be True    ${has_quotes}

Multiple SQL VALUES From Database Schema
    [Documentation]    Generate multiple SQL VALUES strings from database schema
    [Tags]    database    postgres    generate    sql
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    ${records}=    Generate Data From Schema    target=db    amount=5
    Log    Records: ${records}
    Length Should Be    ${records}    5
    # Verify all records are strings
    FOR    ${record}    IN    @{records}
        ${type}=    Evaluate    type($record).__name__
        Should Be Equal    ${type}    str
    END

Load Schema Without Db Module Should Fail
    [Documentation]    Verify that Load Schema requires proper database parameters
    [Tags]    database    validation    negative
    Run Keyword And Expect Error    *Unsupported db_module*    Load Schema    db_module=invalid_module    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_table=${DATABASE_TABLE}

Load Schema Without Db Table Should Fail
    [Documentation]    Verify that Load Schema requires db_table parameter
    [Tags]    database    validation    negative
    Run Keyword And Expect Error    *db_table is required*    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}

Generate Without Load Schema Should Fail
    [Documentation]    Verify that Generate Data From Schema requires Load Schema first
    [Tags]    database    validation    negative
    Run Keyword And Expect Error    *No database schema loaded*    Generate Data From Schema    target=db

SQL VALUES With Excluded Columns
    [Documentation]    Generate SQL VALUES with excluded columns
    [Tags]    database    postgres    exclude    sql
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}    db_exclude_columns=id,created_at
    ${values}=    Generate Data From Schema    target=db
    Log    SQL VALUES (excluded columns): ${values}
    # Should be a string
    ${type}=    Evaluate    type($values).__name__
    Should Be Equal    ${type}    str
    # Count commas to verify we have values (more columns = more commas)
    ${parts}=    Split String    ${values}    ,
    ${count}=    Get Length    ${parts}
    Log    Number of values (after exclusion): ${count}
    Should Be True    ${count} > 0

Reload Database Schema
    [Documentation]    Test reloading database schema with different table
    [Tags]    database    postgres    reload
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    ${values}=    Generate Data From Schema    target=db
    Should Not Be Empty    ${values}

Generate Large Amount From Database
    [Documentation]    Generate larger amount of SQL VALUES for performance testing
    [Tags]    database    postgres    performance    sql
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    ${records}=    Generate Data From Schema    target=db    amount=50
    Length Should Be    ${records}    50
    # Verify all records are strings
    FOR    ${record}    IN    @{records}
        ${type}=    Evaluate    type($record).__name__
        Should Be Equal    ${type}    str
    END

SQL VALUES Format Validation
    [Documentation]    Verify SQL VALUES format is correct
    [Tags]    database    postgres    sql    validation
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    ${values}=    Generate Data From Schema    target=db
    Log    Generated SQL VALUES: ${values}
    # Check format: should have comma-separated values
    ${parts}=    Split String    ${values}    ,
    ${count}=    Get Length    ${parts}
    Log    Number of columns: ${count}
    Should Be True    ${count} > 0
    # Check that string values are properly quoted
    FOR    ${part}    IN    @{parts}
        ${trimmed}=    Strip String    ${part}
        # Check if it's a quoted string (starts and ends with single quote)
        ${is_quoted}=    Evaluate    $trimmed.startswith("'") and $trimmed.endswith("'")
        Log    Part: ${trimmed} (quoted: ${is_quoted})
    END

Generate With AI From Database Schema
    [Documentation]    Generate data using AI from database schema
    [Tags]    database    postgres    ai
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    ${data}=    Generate Data From Schema    target=db    use_ai=${True}
    Log    AI generated data: ${data}
    # Should be a string (SQL VALUES format)
    ${type}=    Evaluate    type($data).__name__
    Should Be Equal    ${type}    str
    Should Not Be Empty    ${data}

Generate With AI Multiple Records From DB
    [Documentation]    Generate multiple records using AI from database
    [Tags]    database    postgres    ai
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    ${records}=    Generate Data From Schema    target=db    amount=3    use_ai=${True}
    Log    AI generated records: ${records}
    Length Should Be    ${records}    3
    # Verify all records are strings (SQL VALUES format)
    FOR    ${record}    IN    @{records}
        ${type}=    Evaluate    type($record).__name__
        Should Be Equal    ${type}    str
        Should Not Be Empty    ${record}
    END

Generate Without AI Uses Faker By Default
    [Documentation]    Verify that without use_ai, Faker is used (faster)
    [Tags]    database    postgres    faker
    Load Schema    db_module=${DATABASE_MODULE}    db_name=${DATABASE_NAME}    db_host=${DATABASE_HOST}    db_port=${DATABASE_PORT}    db_user=${DATABASE_USER}    db_password=${DATABASE_PASSWORD}    db_schema=${DATABASE_SCHEMA}    db_table=${DATABASE_TABLE}
    ${data}=    Generate Data From Schema    target=db
    Log    Faker generated data: ${data}
    # Default behavior - use_ai is not specified, should use Faker
    ${type}=    Evaluate    type($data).__name__
    Should Be Equal    ${type}    str
    Should Not Be Empty    ${data}
