# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)


from spack.package import *


class PyChess(PythonPackage):
    """Python Chess: A chess library for Python."""

    homepage = "https://github.com/niklasf/python-chess"
    pypi = "chess/chess-1.11.0.tar.gz"

    license("GPL 3.0", checked_by="ashim-mahara")

    version("1.11.0", sha256="3c63cace177860987705b71dedcfab63fb1065186799a06db7eccd76e833b279")

    # Python version requirement
    depends_on("python@3.8:", type=("build", "run"))

    # Main dependencies
    depends_on("py-setuptools", type="build")
