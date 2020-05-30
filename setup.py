from setuptools import setup

setup(
    install_requires=["GitPython","datetime","seaborn","pandas","numpy","matplotlib","argparse"],
    entry_points={
        "console_scripts": [
            "gilot = app:main"
        ]
    },
    name="gilot",
    version="0.1.0",
    license="MIT LICENSE",
    description="a git log visual analyzer",
    author="hirokidaichi",
    url="https://github.com/hirokidaichi/gilot",
)
