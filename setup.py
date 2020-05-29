from setuptools import setup

setup(
    install_requires=["pandas","numpy","matplotlib","argparse"],
    entry_points={
        "console_scripts": [
            "gilot = app:main"
        ]
    }
)
