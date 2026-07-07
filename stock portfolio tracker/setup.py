from setuptools import find_packages, setup

setup(
    name="stock-portfolio-tracker",
    version="1.0.0",
    author="Graftcode Demo",
    description=(
        "A plain Python class that tracks a stock portfolio, "
        "exposed as a remote service via Graftcode Gateway — "
        "no HTTP framework required."
    ),
    long_description=(
        "Demonstrates how Graftcode Gateway (`gg`) can wrap a plain "
        "Python class and make its public methods remotely callable "
        "without Flask, FastAPI, Django, or any other HTTP framework."
    ),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    keywords="stock, portfolio, tracker, graftcode, finance",
    install_requires=[],  # zero runtime dependencies — pure stdlib
    license="MIT",
)
