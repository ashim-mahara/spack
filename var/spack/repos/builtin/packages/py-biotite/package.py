# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *

class PyBiotite(PythonPackage):
    """Biotite is your Swiss army knife for bioinformatics. Whether you want to identify homologous sequence regions in a protein family or you would like to find disulfide bonds in a protein structure: Biotite has the right tool for you. This package bundles popular tasks in computational molecular biology into a uniform Python library."""

    homepage = "https://www.biotite-python.org/latest/"
    pypi = "biotite/biotite-1.0.1.tar.gz"

    license("BSD-3-Clause")

    version("1.0.1", sha256="7012158431fd488c26d78d33032550eea1d7af7afd01b48549a7fd239f63dab5")

    depends_on("py-python-dotenv", type="build")
    depends_on("py-hatch-vcs", type="build")
    depends_on("py-hatchling", type="build")
    depends_on("py-hatch", type="build")
    depends_on("py-hatch-cython", type="build")

    depends_on("py-numpy", type=("build", "run"))
    depends_on("py-msgpack", type=("build", "run"))
    depends_on("py-biotraj", type=("build", "run"))
    depends_on("py-requests", type=("build", "run"))
    depends_on("py-networkx", type=("build", "run"))
