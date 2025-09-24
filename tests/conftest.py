"""Conftest."""
import os.path

import pytest

import spack.config

# https://docs.pytest.org/en/7.1.x/how-to/fixtures.html#using-fixtures-from-other-projects
pytest_plugins = "spack.test.conftest"


@pytest.fixture(autouse=True, scope="function")
def this_extension(mutable_config):
    """Add ourselves as extension."""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    spack.config.set("config:extensions", [path])
