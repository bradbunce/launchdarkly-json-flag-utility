from setuptools import setup, find_packages

setup(
    name="ld-json-flag-utility",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "jinja2>=3.1.0",
        "python-multipart>=0.0.7",
        "boto3>=1.34.0",
        "launchdarkly-server-sdk>=9.6.0",
        "launchdarkly-server-sdk-ai>=0.20.0",
    ],
    entry_points={
        "console_scripts": [
            "ld-json-flag=ld_json_flag.cli:main",
            "ld-json-flag-web=web.run:main",
        ],
    },
    author="Brad Bunce",
    author_email="bradbunce@yahoo.com",
    description=(
        "Utility to create and update LaunchDarkly feature flags "
        "with JSON variations"
    ),
    keywords="launchdarkly, feature-flag, json, cli",
    url="https://github.com/bradbunce/launchdarkly-json-flag-utility",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
    ],
    python_requires=">=3.9",
)
