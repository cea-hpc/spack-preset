"""Test spack preset command."""

import pytest

import spack.main
from spack import environment as ev

from preset.cmd.preset import escape_cmake_macros
from spack.spec import Spec

# everything here uses the mock_env_path
pytestmark = pytest.mark.usefixtures("mutable_mock_env_path", "mutable_config", "mutable_mock_repo")

spack_preset = spack.main.SpackCommand("preset")


def _read(path):
    """Read the whole file."""
    with open(path, "r") as f:
        return f.read()


@pytest.fixture()
def test_env(mock_stage, mock_fetch, install_mockery):
    """Create and return a test spack-env."""
    e = ev.create("preset-test-env", with_view=False)
    with e:
        yield e


def test_preset_simple(tmpdir, mock_stage, mock_fetch, install_mockery):
    """Test."""
    src = str(tmpdir.mkdir("src"))
    preset = str(tmpdir.join("CMakeUserPresets.json"))
    args = ["-d", src, "-o", preset]

    spec = "cmake-client@=develop"
    print(spack_preset(*(args + [spec])))
    assert spec in _read(preset)


def test_preset_from_env(tmpdir, test_env):
    """Test."""
    test_env.add("cmake-client@=develop")
    test_env.concretize()

    src = str(tmpdir.mkdir("src"))
    preset = str(tmpdir.join("CMakePresets.json"))
    args = ["-d", src, "-o", preset]

    spack_preset(
        *(
            args
            + [
                "--build-dir",
                r"$penv{HOME}/build/${sourceDirName}/${presetName}",
                "--with-name",
                "mypreset",
                "cmake-client@develop",
            ]
        )
    )
    specstr = list(test_env.roots())[0]
    assert specstr.dag_hash() in _read(preset)


# def test_preset_from_root(tmpdir, test_env):
#     """Test."""
#     test_env.add('cmake-client@develop')
#     test_env.add('cmake-client@develop single=red')
#     test_env.concretize()

#     src = str(tmpdir.mkdir('src'))
#     preset = str(tmpdir.join('preset.cmake'))
#     args = ['-d', src, '-o', preset]

#     spack_preset(*(args + ['--from-env', 'cmake-client@develop']))
#     assert 'single=blue' in _read(preset)
#     assert 'single=red' not in _read(preset)

#     spack_preset(*(args + ['--from-root', 'cmake-client single=red',
#                                 'cmake-client@develop']))
#     assert 'single=blue' not in _read(preset)
#     assert 'single=red' in _read(preset)

#     # Test failure on multiple matches of --from-root
#     with pytest.raises(SpackCommandError):
#         spack_preset(*(args + ['--from-root', 'cmake-client',
#                                     'cmake-client@develop']))
#     # assert 'can only match a single root' in e


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
