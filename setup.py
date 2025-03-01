from setuptools import setup, find_packages

setup(
    name="monki",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "monki-node=monki.run_node:main",
            "monki=monki.cli:main",
        ],
    },
    python_requires=">=3.7",
)