*** Settings ***
Documentation     Shared keywords for the local Mock OpenAPI server used by URL-spec
...               validation tests. The server is a 'python -m http.server' instance
...               rooted at tests/fixtures, serving YAML fixtures over localhost.
...
...               Suites that import this resource typically use:
...                 Suite Setup       Start Mock OpenAPI Server
...                 Suite Teardown    Stop Mock OpenAPI Server
...
...               The default port is 18080. Override via the 'port' argument if a
...               suite needs to run in parallel with another suite using this
...               resource (Robot runs suites sequentially by default, so the
...               default port is fine for single-threaded execution).

Library     Process

*** Variables ***
${MOCK_PORT}    18080
${MOCK_BASE}    http://127.0.0.1:${MOCK_PORT}

*** Keywords ***
Start Mock OpenAPI Server
    [Documentation]    Spustí python -m http.server v tests/fixtures adresáři.
    ...                Servíruje YAML fixture přes localhost na zadaném portu.
    [Arguments]    ${port}=${MOCK_PORT}
    VAR    ${fixtures_dir}    ${CURDIR}${/}..${/}..${/}fixtures
    ${process}=    Start Process    python    -m    http.server    ${port}
    ...    cwd=${fixtures_dir}    stdout=${TEMPDIR}${/}mock_server_${port}.log    stderr=STDOUT
    Set Suite Variable    ${MOCK_PROCESS}    ${process}
    # Krátké čekání, aby se server stihl bindnout na port
    Sleep    1s

Stop Mock OpenAPI Server
    [Documentation]    Ukončí mock server spuštěný v Suite Setup.
    Terminate Process    ${MOCK_PROCESS}    kill=True
