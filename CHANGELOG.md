# Change Log

## [Unreleased][unreleased]
N/A

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

[unreleased]: https://github.com/RazerM/parver/compare/0.1.1...HEAD
[0.1.1]: https://github.com/RazerM/parver/compare/0.1...0.1.1
[0.1]: https://github.com/RazerM/parver/compare/f69c63c52604823653ad2a24651bcaab3de1cce8...0.1
