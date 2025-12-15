from collections.abc import Iterator
from contextlib import contextmanager

import nox

nox.options.reuse_existing_virtualenvs = True
nox.options.default_venv_backend = "uv"

python_versions = ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]


@nox.session(python="3.13")
def docs(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-dev",
        "--group=docstest",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )

    temp_dir = session.create_tmp()
    session.run(
        "sphinx-build",
        "-W",
        "-b",
        "html",
        "-d",
        f"{temp_dir}/doctrees",
        "docs",
        "docs/_build/html",
    )
    session.run("doc8", "docs/")


@nox.session(python="3.13")
def typing(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--group=typing",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("mypy", "src/parver")


@nox.session(python=python_versions)
def tests(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )

    session.run(
        "coverage",
        "run",
        "-m",
        "pytest",
        *session.posargs,
    )


@nox.session(name="test-min-deps", python=python_versions)
def test_min_deps(session: nox.Session) -> None:
    with restore_file("uv.lock"):
        session.run_install(
            "uv",
            "sync",
            "--resolution=lowest-direct",
            f"--python={session.virtualenv.location}",
            env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        )

        session.run("pytest", *session.posargs)


@nox.session(name="test-latest", python=python_versions)
def test_latest(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--no-install-project",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run_install(
        "uv",
        "pip",
        "install",
        "--upgrade",
        ".",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )

    session.run("pytest", *session.posargs)


@contextmanager
def restore_file(path: str) -> Iterator[None]:
    with open(path, "rb") as f:
        original = f.read()
    try:
        yield
    finally:
        with open(path, "wb") as f:
            f.write(original)
