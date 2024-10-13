from warnings import warn

warn(
    f'The module {__name__} is a proof-of-concept implementation, '
    'and will likely be replaced entirely in the future.',
    DeprecationWarning,
    stacklevel=2,
)
