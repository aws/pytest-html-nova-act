# pytest-html-nova-act

pytest-html-nova-act is a [pytest](https://pytest.org) plugin that integrates HTML test reporting with [Amazon Nova Act SDK](https://github.com/aws/nova-act) capabilities. This plugin enhances [pytest-html](https://pytest-html.readthedocs.io) reports by adding Nova Act-specific features and metadata.

# Usage

## Requirements

- Python 3.11+
- pytest 8.0+
- pytest-html 4.0+
- nova-act 1.0+
- Nova Act API key
    - Visit [Nova Act home page](https://nova.amazon.com/act) to generate your API key and set it to the `NOVA_ACT_API_KEY` environment variable

## Installation

Install via pip:

```bash
pip install nova-act pytest pytest-html pytest-html-nova-act
```

## Configuration

Add to `pytest.ini`:

```
[pytest]
addopts = --html=reports/report.html --self-contained-html --add-nova-act-report
```

## Pytest Example

The below sample code shows how to create a pytest fixture which instantiates the Nova Act client, starts it, and stops it after the test completes. It also includes an example test.

```python
import pytest
from nova_act import NovaAct, BOOL_SCHEMA

@pytest.fixture()
def nova_session():
    nova = NovaAct(
        starting_page="https://amazon.com",
        headless=True
    )
    nova.start()
    yield nova
    nova.stop()

def test_example(nova_session):
    nova_session.act("Search for a coffee maker")
    expected = True
    result = nova_session.act("Am I on the coffee maker search results page?", schema=BOOL_SCHEMA)
    actual = result.matches_schema and result.parsed_response
    assert expected == actual
```

## Usage

```bash
pytest
```

Running the `pytest` command in a valid pytest project and using the pytest configuration and sample code mentioned above will result in:

1. Run tests using Nova Act
2. Embed Nova Act SDK logs and screenshots in the `pytest-html` report file in `reports/report.html`

## Resources

- [Amazon Nova Act SDK](https://github.com/aws/nova-act)