# Copyright CEA
# Authors: Pierre Duperray <pierre.duperray@cea.fr>, Jordan Galby
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
"""Test spack preset command."""

import json
import os
import pathlib

import pytest
import spack.main
from spack import environment as ev
from spack.spec import Spec

from preset.cmd.preset import escape_cmake_macros

install = spack.main.SpackCommand("install")
env = spack.main.SpackCommand("env")
add = spack.main.SpackCommand("add")
spack_preset = spack.main.SpackCommand("preset")


@pytest.fixture()
def test_env(mock_stage, mock_fetch, install_mockery):
    """Create and return a test spack-env."""
    e = ev.create("preset-test-env", with_view=False)
    with e:
        yield e


def test_preset_simple(tmpdir: pathlib.Path, mock_stage, mock_fetch, install_mockery):
    """Test."""
    CMakeUserPresets_filepath = tmpdir / "CMakeUserPresets.json"
    log = "test"
    install("--fake", "cmake-client")
    spack_preset("-o", str(CMakeUserPresets_filepath), "cmake-client")

    with CMakeUserPresets_filepath.open("r") as json_file:
        presets = json.load(json_file)

    assert (
        presets["configurePresets"][0]["environment"]["SPACK_ROOT"]
        == os.environ["SPACK_ROOT"]
    )


def test_preset_from_env(
    tmpdir: pathlib.Path,
    mutable_mock_env_path,
    mock_packages,
    mock_fetch,
    install_mockery,
):
    env("create", "test", view=False)
    with ev.read("test"):
        add("cmake-client")
        install("--fake", "--test", "all")
        CMakeUserPresets_filepath = tmpdir / "CMakeUserPresets.json"

        spack_preset(
            "-o",
            str(CMakeUserPresets_filepath),
            "--build-dir",
            r"build/${sourceDirName}/${presetName}",
            "--with-name",
            "mypreset",
        )

    with CMakeUserPresets_filepath.open("r") as json_file:
        presets = json.load(json_file)

    assert presets["configurePresets"][0]["name"] == "mypreset"
    assert (
        presets["configurePresets"][0]["binaryDir"]
        == "build/${sourceDirName}/${presetName}"
    )


def test_escape_cmake_macros(mock_packages):
    spec = Spec("multivalue-variant")

    fmts = [
        # input, expected escape_cmake_macros, expected spec.format(escape_cmake_macros)
        (r"{name}", r"{name}", "multivalue-variant"),
        (r"${macro}", r"$\{macro\}", r"${macro}"),
        (r"$penv{macro}", r"$penv\{macro\}", r"$penv{macro}"),
        (r"\{name\}", r"\{name\}", r"{name}"),
        (r"\${name}", r"\${name}", r"$multivalue-variant"),  # Dubious...
    ]
    for fmt, expected, expected_spack in fmts:
        fmt_escaped = escape_cmake_macros(fmt)
        assert fmt_escaped == expected
        assert spec.format(fmt_escaped) == expected_spack

    # Test combinations
    combis = [
        lambda elems: elems,
        lambda elems: elems + elems,
        lambda elems: list(reversed(elems)),
        lambda elems: list(reversed(elems + elems)),
    ]

    fmts_transpose = list(zip(*fmts))
    for combi in combis:
        for sep, sep_spack in [("", ""), ("sep", "sep"), ("\\\\", "\\")]:
            fmt = sep.join(combi(list(fmts_transpose[0])))
            expected = sep.join(combi(list(fmts_transpose[1])))
            expected_spack = sep_spack.join(combi(list(fmts_transpose[2])))
            fmt_escaped = escape_cmake_macros(fmt)
            assert fmt_escaped == expected
            assert spec.format(fmt_escaped) == expected_spack
