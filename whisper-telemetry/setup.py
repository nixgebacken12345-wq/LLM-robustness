from setuptools import setup, find_packages

setup(
    name="whisper-telemetry",
    version="2.0.0",
    author="IT Diagnostics Team",
    author_email="it-diagnostics@company.com",
    description="Enterprise keyboard telemetry collector",
    long_description=open("README.md").read(),
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=[
        "pynput>=1.7.6",
        "psutil>=5.9.0",
        "requests>=2.31.0",
        "pywin32>=306",
        "cryptography>=41.0.0"
    ],
    entry_points={
        "console_scripts": [
            "whisper=main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3.9",
    ],
)
