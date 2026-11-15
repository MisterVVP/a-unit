"""Restrict wheel modules to the public runtime, even in a dirty checkout."""
from setuptools.command.build_py import build_py


class PublicBuild(build_py):
    def find_package_modules(self, package, package_dir):
        return [entry for entry in super().find_package_modules(package, package_dir)
                if entry[1] in {"__init__", "__main__", "aunit"}]
