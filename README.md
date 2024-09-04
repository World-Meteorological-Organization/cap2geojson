# The CAP to GeoJSON Converter

### The Python package for making CAP alerts visualizable

<div align="center">

  <a href="https://github.com/wmo-im/cap2geojson/blob/main/LICENSE" alt="License" ><img src="https://img.shields.io/badge/License-Apache_2.0-blue" alt="License Badge"></img></a>
  [![Super-Linter](https://github.com/wmo-im/cap2geojson/actions/workflows/test-code-quality.yml/badge.svg)](https://github.com/marketplace/actions/super-linter)
  ![Unit-Tests](https://github.com/wmo-im/cap2geojson/actions/workflows/unit-tests.yml/badge.svg)
  ![Publish-To-PyPI](https://github.com/wmo-im/cap2geojson/actions/workflows/publish-to-pypi.yml/badge.svg)

</div>

## Features

- **GeoJSON Creation**: Visualize your alerts in the [GeoJSON format](https://datatracker.ietf.org/doc/html/rfc7946).

## Getting Started

### 1. Installation

```bash
pip install cap2geojson
```

### 2A. Using the API

We can convert the CAP XML to GeoJSON using the `transform(cap)` method:

- `cap`: The CAP alert XML string contents.

```python
from cap2geojson import transform

with open(<cap-alert-directory>, 'r') as f:
    cap = f.read()

result = transform(cap)
```

### 2B. Using the CLI

We can convert a CAP alert directly to a GeoJSON file using the following command:

```bash
cap2geojson transform <cap-alert-directory>
```

## Bugs and Issues

All bugs, enhancements and issues are managed on [GitHub](https://github.com/wmo-im/cap2geojson/issues).

## Contact

* [Rory Burke](https://github.com/RoryPTB)
