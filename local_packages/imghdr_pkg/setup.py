from setuptools import setup, find_packages

setup(
    name="imghdr-shim-local",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    description="Local imghdr shim package to satisfy hosted runtimes",
)
