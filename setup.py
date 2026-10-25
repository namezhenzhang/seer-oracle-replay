"""Compatibility entry point for hosts with older editable-install tooling."""

from setuptools import setup, find_packages

setup(
    name="seer-oracle-replay",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages("src"),
    python_requires=">=3.10",
    install_requires=["numpy==2.2.6", "matplotlib==3.10.9", "huggingface_hub==1.26.0"],
    entry_points={
        "console_scripts": [
            "seer-replay=seer_replay.__main__:main",
            "seer-download=seer_replay.download:main",
        ]
    },
)
