# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class PyBlosum(PythonPackage):
    """The BLOcks SUbstitution Matrices (BLOSUM) are used to score alignments between protein sequences and are therefore mainly used in bioinformatics.
Reading such matrices is not particularly difficult, yet most off the shelf packages are overloaded with strange dependencies. And why do we need to implement the same reader again if there is a simple module for that.
blosum offers a robust and easy-to-expand implementation without relying on third-party libraries."""

    homepage = "https://github.com/not-a-feature/blosum"
    pypi = "blosum/blosum-2.0.3.tar.gz"

    license("GPL-3.0", checked_by="ashim-mahara")

    version("2.0.3", sha256="6fee68975c04211fc7c298f58cbf1e5b021ea2879e51456d934238e89ea2ae9b")

    depends_on("py-setuptools@42:", type="build")
