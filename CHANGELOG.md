# Change Log

## [Unreleased][unreleased]
N/A

## [0.3][] - 2020-02-20
### Added
- `Version.truncate` method to remove trailing zeros from the release segment.
- `Version` now validates each item in the release sequence.
- `Version.bump_epoch` method.
- Add `by` keyword argument to `bump_pre`, `bump_post`, and `bump_dev` methods,
  which e.g. `.bump_dev(by=-1)`.

### Changed
- **BREAKING CHANGE**. The `Version` constructor now uses an empty string to
  represent an implicit zero instead of `None`.

  ```python
  >>> Version(release=1, post='')
  <Version '1.post'>
  ```

### Removed
- **BREAKING CHANGE**. `Version.clear` is no longer necessary. Use
  `Version.replace(pre=None, post=None, dev=None)` instead.

### Fixed
- `Version` incorrectly allowed an empty release sequence.
- `Version` rejects `bool` for numeric components.
- `Version` rejects negative integers for numeric components.
- The strict parser no longer accepts local versions with `-` or `_` separators,
  or uppercase letters.
- The strict parser no longer accepts numbers with leading zeros.
- The local version was only being converted to lowercase when parsing with
  `strict=False`. It is now always converted.
- The local version separators were not being normalized to use `.`.

## [0.2.1][] - 2018-12-31
### Fixed
- On Python 2, `Version` was incorrectly rejecting `long` integer values.

## [0.2][] - 2018-11-21
### Added
- `Version.bump_release_to` method for control over the value to bump to, e.g.
  for [CalVer][].
- `Version.set_release` method for finer control over release values without
  resetting subsequent indices to zero.

### Changed
- **BREAKING CHANGE**. The argument to `Version.bump_release` is now a keyword
  only argument, e.g. `Version.bump_release(index=0)`.
- The `release` parameter to `Version` now accepts any iterable.

### Fixed
- Deprecation warnings about invalid escape sequences in `_parse.py`.

[CalVer]: (https://calver.org)

## [0.1.1][] - 2018-06-19
### Fixed
- `Version` accepted `pre=None` and `post_tag=None`, which produces an
  ambiguous version number. This is because an implicit pre-release
  number combined with an implicit post-release looks like a pre-release
  with a custom separator:

  ```python
    >>> Version(release=1, pre_tag='a', pre=None, post_tag=None, post=2)
    <Version '1a-2'>
    >>> Version(release=1, pre_tag='a', pre_sep2='-', pre=2)
    <Version '1a-2'>
  ```

  The first form now raises a `ValueError`.
- Don't allow `post=None` when `post_tag=None`. Implicit post releases
  cannot have implicit post release numbers.

## [0.1][] - 2018-05-20

First release.

[unreleased]: https://github.com/RazerM/parver/compare/0.3...HEAD
[0.3]: https://github.com/RazerM/parver/compare/0.2.1...0.3
[0.2.1]: https://github.com/RazerM/parver/compare/0.2...0.2.1
[0.2]: https://github.com/RazerM/parver/compare/0.1.1...0.2
[0.1.1]: https://github.com/RazerM/parver/compare/0.1...0.1.1
[0.1]: https://github.com/RazerM/parver/compare/f69c63c52604823653ad2a24651bcaab3de1cce8...0.1
