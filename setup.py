from setuptools import setup, find_packages

setup(
    name="ld-json-flag-utility",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "python-dotenv>=0.15.0",
    ],
    entry_points={
        "console_scripts": [
            "ld-json-flag=ld_json_flag.cli:main",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="Utility to create and update LaunchDarkly feature flags with JSON variations",
    keywords="launchdarkly, feature-flag, json, cli",
    url="https://github.com/yourusername/launchdarkly-json-flag-utility",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
)