# Copyright 2013-2023 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
import os
import shutil

import pytest

import spack.cmd.compiler
import spack.compilers
import spack.main
import spack.spec
import spack.util.pattern
import spack.version

compiler = spack.main.SpackCommand("compiler")


@pytest.fixture
def compilers_dir(mock_executable):
    """Create a directory with some mock compiler scripts in it.

    Scripts are:
      - clang
      - clang++
      - gcc
      - g++
      - gfortran-8

    """
    clang_path = mock_executable(
        "clang",
        output="""
if [ "$1" = "--version" ]; then
    echo "clang version 11.0.0 (clang-1100.0.33.16)"
    echo "Target: x86_64-apple-darwin18.7.0"
    echo "Thread model: posix"
    echo "InstalledDir: /dummy"
else
    echo "clang: error: no input files"
    exit 1
fi
""",
    )
    shutil.copy(clang_path, clang_path.parent / "clang++")

    gcc_script = """
if [ "$1" = "-dumpversion" ]; then
    echo "8"
elif [ "$1" = "-dumpfullversion" ]; then
    echo "8.4.0"
elif [ "$1" = "--version" ]; then
    echo "{0} (GCC) 8.4.0 20120313 (Red Hat 8.4.0-1)"
    echo "Copyright (C) 2010 Free Software Foundation, Inc."
else
    echo "{1}: fatal error: no input files"
    echo "compilation terminated."
    exit 1
fi
"""
    mock_executable("gcc-8", output=gcc_script.format("gcc", "gcc-8"))
    mock_executable("g++-8", output=gcc_script.format("g++", "g++-8"))
    mock_executable("gfortran-8", output=gcc_script.format("GNU Fortran", "gfortran-8"))

    return clang_path.parent


@pytest.mark.not_on_windows("Cannot execute bash script on Windows")
@pytest.mark.regression("11678,13138")
def test_compiler_find_without_paths(no_compilers_yaml, working_env, mock_executable):
    """Tests that 'spack compiler find' looks into PATH by default, if no specific path
    is given.
    """
    gcc_path = mock_executable("gcc", output='echo "0.0.0"')

    os.environ["PATH"] = str(gcc_path.parent)
    output = compiler("find", "--scope=site")

    assert "gcc" in output


@pytest.mark.regression("17589")
def test_compiler_find_no_apple_gcc(no_compilers_yaml, working_env, mock_executable):
    """Tests that Spack won't mistake Apple's GCC as a "real" GCC, since it's really
    Clang with a few tweaks.
    """
    gcc_path = mock_executable(
        "gcc",
        output="""
if [ "$1" = "-dumpversion" ]; then
    echo "4.2.1"
elif [ "$1" = "--version" ]; then
    echo "Configured with: --prefix=/dummy"
    echo "Apple clang version 11.0.0 (clang-1100.0.33.16)"
    echo "Target: x86_64-apple-darwin18.7.0"
    echo "Thread model: posix"
    echo "InstalledDir: /dummy"
else
    echo "clang: error: no input files"
fi
""",
    )

    os.environ["PATH"] = str(gcc_path.parent)
    output = compiler("find", "--scope=site")

    assert "gcc" not in output


@pytest.mark.regression("37996")
def test_compiler_remove(mutable_config, mock_packages):
    """Tests that we can remove a compiler from configuration."""
    assert spack.spec.CompilerSpec("gcc@=4.5.0") in spack.compilers.all_compiler_specs()
    args = spack.util.pattern.Bunch(all=True, compiler_spec="gcc@4.5.0", add_paths=[], scope=None)
    spack.cmd.compiler.compiler_remove(args)
    assert spack.spec.CompilerSpec("gcc@=4.5.0") not in spack.compilers.all_compiler_specs()


@pytest.mark.regression("37996")
def test_removing_compilers_from_multiple_scopes(mutable_config, mock_packages):
    # Duplicate "site" scope into "user" scope
    site_config = spack.config.get("compilers", scope="site")
    spack.config.set("compilers", site_config, scope="user")

    assert spack.spec.CompilerSpec("gcc@=4.5.0") in spack.compilers.all_compiler_specs()
    args = spack.util.pattern.Bunch(all=True, compiler_spec="gcc@4.5.0", add_paths=[], scope=None)
    spack.cmd.compiler.compiler_remove(args)
    assert spack.spec.CompilerSpec("gcc@=4.5.0") not in spack.compilers.all_compiler_specs()


@pytest.mark.not_on_windows("Cannot execute bash script on Windows")
def test_compiler_add(mutable_config, mock_packages, mock_executable):
    """Tests that we can add a compiler to configuration."""
    expected_version = "4.5.3"
    gcc_path = mock_executable(
        "gcc",
        output=f"""\
for arg in "$@"; do
    if [ "$arg" = -dumpversion ]; then
        echo '{expected_version}'
    fi
done
""",
    )
    bin_dir = gcc_path.parent
    root_dir = bin_dir.parent

    compilers_before_find = set(spack.compilers.all_compiler_specs())
    args = spack.util.pattern.Bunch(
        all=None, compiler_spec=None, add_paths=[str(root_dir)], scope=None, mixed_toolchain=False
    )
    spack.cmd.compiler.compiler_find(args)
    compilers_after_find = set(spack.compilers.all_compiler_specs())

    compilers_added_by_find = compilers_after_find - compilers_before_find
    assert len(compilers_added_by_find) == 1
    new_compiler = compilers_added_by_find.pop()
    assert new_compiler.version == spack.version.Version(expected_version)


@pytest.mark.not_on_windows("Cannot execute bash script on Windows")
@pytest.mark.regression("17590")
@pytest.mark.parametrize("mixed_toolchain", [True, False])
def test_compiler_find_mixed_suffixes(
    mixed_toolchain, no_compilers_yaml, working_env, compilers_dir
):
    """Ensure that we'll mix compilers with different suffixes when necessary."""
    os.environ["PATH"] = str(compilers_dir)
    output = compiler(
        "find", "--scope=site", "--mixed-toolchain" if mixed_toolchain else "--no-mixed-toolchain"
    )

    assert "clang@11.0.0" in output
    assert "gcc@8.4.0" in output

    config = spack.compilers.get_compiler_config("site", False)
    clang = next(c["compiler"] for c in config if c["compiler"]["spec"] == "clang@=11.0.0")
    gcc = next(c["compiler"] for c in config if c["compiler"]["spec"] == "gcc@=8.4.0")

    gfortran_path = str(compilers_dir / "gfortran-8")

    assert clang["paths"] == {
        "cc": str(compilers_dir / "clang"),
        "cxx": str(compilers_dir / "clang++"),
        "f77": gfortran_path if mixed_toolchain else None,
        "fc": gfortran_path if mixed_toolchain else None,
    }

    assert gcc["paths"] == {
        "cc": str(compilers_dir / "gcc-8"),
        "cxx": str(compilers_dir / "g++-8"),
        "f77": gfortran_path,
        "fc": gfortran_path,
    }


@pytest.mark.not_on_windows("Cannot execute bash script on Windows")
@pytest.mark.regression("17590")
def test_compiler_find_prefer_no_suffix(no_compilers_yaml, working_env, compilers_dir):
    """Ensure that we'll pick 'clang' over 'clang-gpu' when there is a choice."""
    clang_path = compilers_dir / "clang"
    shutil.copy(clang_path, clang_path.parent / "clang-gpu")
    shutil.copy(clang_path, clang_path.parent / "clang++-gpu")

    os.environ["PATH"] = str(compilers_dir)
    output = compiler("find", "--scope=site")

    assert "clang@11.0.0" in output
    assert "gcc@8.4.0" in output

    config = spack.compilers.get_compiler_config("site", False)
    clang = next(c["compiler"] for c in config if c["compiler"]["spec"] == "clang@=11.0.0")

    assert clang["paths"]["cc"] == str(compilers_dir / "clang")
    assert clang["paths"]["cxx"] == str(compilers_dir / "clang++")


@pytest.mark.not_on_windows("Cannot execute bash script on Windows")
def test_compiler_find_path_order(no_compilers_yaml, working_env, compilers_dir):
    """Ensure that we look for compilers in the same order as PATH, when there are duplicates"""
    new_dir = compilers_dir / "first_in_path"
    new_dir.mkdir()
    for name in ("gcc-8", "g++-8", "gfortran-8"):
        shutil.copy(compilers_dir / name, new_dir / name)
    # Set PATH to have the new folder searched first
    os.environ["PATH"] = "{}:{}".format(str(new_dir), str(compilers_dir))

    compiler("find", "--scope=site")

    config = spack.compilers.get_compiler_config("site", False)
    gcc = next(c["compiler"] for c in config if c["compiler"]["spec"] == "gcc@=8.4.0")
    assert gcc["paths"] == {
        "cc": str(new_dir / "gcc-8"),
        "cxx": str(new_dir / "g++-8"),
        "f77": str(new_dir / "gfortran-8"),
        "fc": str(new_dir / "gfortran-8"),
    }


def test_compiler_list_empty(no_compilers_yaml, working_env, compilers_dir):
    """Spack should not automatically search for compilers when listing them and none are
    available. And when stdout is not a tty like in tests, there should be no output and
    no error exit code.
    """
    os.environ["PATH"] = str(compilers_dir)
    out = compiler("list")
    assert not out
    assert compiler.returncode == 0


def test_compilers_shows_packages_yaml(no_compilers_yaml, working_env, compilers_dir):
    """Spack should see a single compiler defined from packages.yaml"""
    gcc_entry = {
        "externals": [
            {
                "spec": "gcc@=7.7.7 os=foobar target=x86_64",
                "prefix": "/path/to/fake",
                "modules": ["gcc/7.7.7", "foobar"],
                "extra_attributes": {
                    "paths": {
                        "cc": "/path/to/fake/gcc",
                        "cxx": "/path/to/fake/g++",
                        "fc": "/path/to/fake/gfortran",
                        "f77": "/path/to/fake/gfortran",
                    },
                    "flags": {"fflags": "-ffree-form"},
                },
            }
        ]
    }

    packages = spack.config.get("packages")
    packages["gcc"] = gcc_entry
    spack.config.set("packages", packages)

    out = compiler("list")
    assert out.count("gcc foobar-x86_64") == 1
    assert out.count("gcc@7.7.7") == 1

    out = compiler("info", "gcc@7.7.7")
    expected = """gcc@7.7.7:
	paths:
		cc = /path/to/fake/gcc
		cxx = /path/to/fake/g++
		f77 = /path/to/fake/gfortran
		fc = /path/to/fake/gfortran
	flags:
		fflags = ['-ffree-form']
	modules  = ['gcc/7.7.7', 'foobar']
	operating system  = foobar
"""

    assert out == expected


def test_compilers_shows_packages_yaml_minimal(no_compilers_yaml, working_env, compilers_dir):
    """Spack should see a single compiler defined from packages.yaml"""
    gcc_entry = {
        "externals": [
            {
                "spec": "gcc@=7.7.7",
                "prefix": str(compilers_dir),
                "modules": ["gcc/7.7.7", "foobar"],
                "extra_attributes": {"flags": {"fflags": "-ffree-form"}},
            }
        ]
    }

    packages = spack.config.get("packages")
    packages["gcc"] = gcc_entry
    spack.config.set("packages", packages)

    out = compiler("list")
    assert out.count("gcc@7.7.7") == 1

    out = compiler("info", "gcc@7.7.7")
    expected = f"""gcc@7.7.7:
	paths:
		cc = {compilers_dir}/gcc-8
		cxx = {compilers_dir}/g++-8
		f77 = {compilers_dir}/gfortran-8
		fc = {compilers_dir}/gfortran-8
	flags:
		fflags = ['-ffree-form']
	modules  = ['gcc/7.7.7', 'foobar']
	operating system  = debian6
"""

    assert out == expected
