from setuptools import setup
from setuptools import find_packages

setup(
    install_requires=["GitPython", "datetime", "seaborn", "pandas", "numpy", "matplotlib", "argparse"],
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "gilot = gilot.app:main"
        ]
    },
    name="gilot",
    version="0.1.2",
    license="MIT LICENSE",
    description="a git log visual analyzer",
    author="hirokidaichi",
    url="https://github.com/hirokidaichi/gilot",
)
