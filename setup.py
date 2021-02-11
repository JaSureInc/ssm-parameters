import codecs
import re
import pathlib

from setuptools import find_packages, setup


INSTALL_REQUIRES = ["boto3-stubs[ssm]", "anytree>=2.8.0"]

EXTRAS_REQUIRE = {"docs": ["sphinx"], "tests": ["coverage[toml]", "pytest"]}

ROOT_DIR = pathlib.Path(__file__).parent


def read(path):
    with codecs.open(ROOT_DIR / path, "rb", "utf-8") as f:
        return f.read()


def get_version(package):
    ver_file = read(pathlib.Path("src") / package / "__init__.py")
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", ver_file).group(1)


version = get_version("ssm_params")

if __name__ == "__main__":
    setup(
        name="ssm_params",
        version=version,
        url="https://github.com/jasureinc/",
        license="BSD 3 Clause",
        description="AWS SSM Parameter Store Util",
        long_description=read("README.md"),
        long_description_content_type="text/markdown",
        author="Jason Paidoussi",
        author_email="jason@paidoussi.net",
        packages=find_packages(where="src"),
        package_dir={"": "src"},
        include_package_data=True,
        install_requires=INSTALL_REQUIRES,
        extras_require=EXTRAS_REQUIRE,
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "License :: OSI Approved :: BSD License",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    )
