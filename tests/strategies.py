import string

from hypothesis.strategies import (
    composite,
    integers,
    just,
    lists,
    one_of,
    sampled_from,
    text,
)

from parver import Version

num_int = integers(min_value=0)
num_str = num_int.map(str)


def epoch():
    epoch = num_str.map(lambda s: s + "!")
    return one_of(just(""), epoch)


@composite
def release(draw):
    return draw(
        num_str.map(lambda s: [s] + draw(lists(num_str.map(lambda s: "." + s)))).map(
            lambda parts: "".join(parts)
        )
    )


def separator(strict=False, optional=False):
    sep = ["."]

    if optional:
        sep.append("")

    if not strict:
        sep.extend(["-", "_"])

    return sampled_from(sep)


@composite
def pre(draw, strict=False):
    words = ["a", "b", "rc"]
    if not strict:
        words.extend(["c", "alpha", "beta", "pre", "preview"])

    blank = just("")

    sep1 = separator(strict=strict, optional=True)
    if strict:
        sep1 = blank

    word = sampled_from(words)

    if strict:
        sep2 = blank
    else:
        sep2 = separator(strict=strict, optional=True)

    num_part = sep2.map(lambda s: s + draw(num_str))
    if not strict:
        num_part = one_of(blank, num_part)

    nonempty = sep1.map(lambda s: s + draw(word) + draw(num_part))

    return draw(one_of(blank, nonempty))


@composite
def post(draw, strict=False):
    words = ["post"]
    if not strict:
        words.extend(["r", "rev"])

    sep1 = separator(strict=strict, optional=not strict)
    word = sampled_from(words)

    blank = just("")

    sep2 = separator(strict=strict, optional=True)
    if strict:
        sep2 = blank

    num_part = sep2.map(lambda s: s + draw(num_str))
    if not strict:
        num_part = one_of(blank, num_part)

    post = sep1.map(lambda s: s + draw(word) + draw(num_part))

    if strict:
        return draw(post)

    post_implicit = num_str.map(lambda s: "-" + s)

    return draw(one_of(blank, post_implicit, post))


@composite
def dev(draw, strict=False):
    sep = separator(strict=strict, optional=not strict)

    blank = just("")

    num_part = num_str
    if not strict:
        num_part = one_of(blank, num_part)

    return draw(one_of(blank, sep.map(lambda s: s + "dev" + draw(num_part))))


@composite
def local_segment(draw):
    alpha = (
        draw(one_of(just(""), integers(0, 9).map(str)))
        + draw(text(string.ascii_lowercase, min_size=1, max_size=1))
        + draw(text(string.ascii_lowercase + string.digits))
    )
    return draw(one_of(num_str, just(alpha)))


@composite
def local(draw, strict=False):
    if strict:
        sep = just(".")
    else:
        sep = sampled_from("-_.")

    part = local_segment()
    sep_part = sep.map(lambda s: s + draw(local_segment()))
    sep_parts = lists(sep_part).map(lambda parts: "".join(parts))

    return draw(one_of(just(""), part.map(lambda s: "+" + s + draw(sep_parts))))


whitespace = sampled_from(["", "\t", "\n", "\r", "\f", "\v"])


def vchar(strict=False):
    if strict:
        return just("")
    return sampled_from(["", "v"])


@composite
def version_string(draw, strict=False):
    return (
        draw(vchar(strict=strict))
        + draw(epoch())
        + draw(release())
        + draw(pre(strict=strict))
        + draw(post(strict=strict))
        + draw(dev(strict=strict))
        + draw(local(strict=strict))
    )


@composite
def version_strategy(draw, strict=False):
    return Version.parse(draw(version_string(strict=strict)))
