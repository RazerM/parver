<p>
  <a href="https://pypi.org/project/parver/"><img src="https://img.shields.io/pypi/v/parver.svg" alt="PyPI" /></a>
  <a href="https://parver.readthedocs.io/en/stable/"><img src="https://img.shields.io/badge/docs-read%20now-blue.svg" alt="Documentation Status" /></a>
  <a href="https://github.com/RazerM/parver/actions?workflow=CI"><img src="https://github.com/RazerM/parver/actions/workflows/main.yml/badge.svg?branch=main" alt="CI Status" /></a>
  <a href="https://codecov.io/gh/RazerM/parver"><img src="https://codecov.io/gh/RazerM/parver/branch/main/graph/badge.svg" alt="Test coverage" /></a>
  <a href="https://raw.githubusercontent.com/RazerM/parver/main/LICENSE"><img src="https://img.shields.io/github/license/RazerM/parver.svg" alt="MIT License" /></a>
</p>

# parver

parver allows parsing and manipulation of [PEP 440](https://www.python.org/dev/peps/pep-0440/) version numbers.

# Example

```python
>>> Version.parse('1.3').bump_dev()
<Version '1.3.dev0'>
>>> v = Version.parse('v1.2.alpha-3')
>>> v.is_alpha
True
>>> v.pre
3
>>> v
<Version 'v1.2.alpha-3'>
>>> v.normalize()
<Version '1.2a3'>
```
