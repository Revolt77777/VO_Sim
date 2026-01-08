"""Setup script for VO_Sim."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="vo-sim",
    version="0.1.0",
    description="Virtual Onsite Simulator - L3-L4 AI Interview Agent",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.11",
    # Runtime dependencies
    install_requires=[
        "click>=8.1.7",
        "rich>=13.7.0",
        "pydantic>=2.5.0",
    ],
    # Development dependencies (install with: pip install -e ".[dev]")
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "mypy>=1.7.0",
            "ruff>=0.1.6",
        ],
    },
    # CLI command: 'vo-sim'
    entry_points={
        "console_scripts": [
            "vo-sim=vo_sim.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
)