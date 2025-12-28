=============
API Reference
=============

.. module:: parver

.. testsetup::

   from parver import Version

.. py:type:: ImplicitZero
   :canonical: Literal[""]

   A version component that is implicitly zero and represented by ``""``.

.. py:type:: Separator
   :canonical: Literal[".", "-", "_"]

   A version separator.

.. py:type:: NonEmptyTuple[T]
   :canonical: tuple[T, *tuple[T, ...]]

   A tuple of one or more items

.. autoclass:: Version
   :members:

.. autoclass:: ParseError
   :show-inheritance:

.. autoclass:: NoLeadingNumberError
   :show-inheritance:

.. autoclass:: UnexpectedInputError
   :show-inheritance:

.. autoclass:: LocalEmptyError
   :show-inheritance:

.. autoclass:: StrictParseError
   :show-inheritance:

.. autoclass:: StrictPreTagError
   :show-inheritance:

.. autoclass:: StrictSegmentError
   :show-inheritance:

.. autoclass:: VPrefixNotAllowedError
   :show-inheritance:

.. autoclass:: LeadingZerosError
   :show-inheritance:

.. autoclass:: ImplicitNumberError
   :show-inheritance:

.. autoclass:: InvalidLocalError
   :show-inheritance:
