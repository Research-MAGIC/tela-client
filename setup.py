"""Setup script for tela-client package"""
from setuptools import setup, find_packages

# Read version from _version.py
version = {}
with open("tela/_version.py") as f:
    exec(f.read(), version)

# Read README for long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="tela-client",
    version=version["__version__"],
    description="The official Python library for the Tela API with chat, audio transcription, and text-to-speech capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="MAGIC Research",
    author_email="rodrigo@researchmagic.com",
    url="https://github.com/Research-MAGIC/tela-client",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.23.0,<1",
        "typing-extensions>=4.5,<5",
        "pydantic>=2.0,<3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.1.3,<8",
            "pytest-asyncio>=0.21.0,<1",
            "pytest-mock>=3.10.0,<4",
            "black>=22.3.0,<24",
            "mypy>=1.0,<2",
            "ruff>=0.1.0",
        ],
        "ui": [
            "nicegui>=1.4.0,<2",
            "python-dotenv>=1.0.0,<2",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="openai fabric llm api-client chat ai audio speech-to-text text-to-speech transcription tts stt",
    project_urls={
        "Documentation": "https://docs.telaos.com",
        "Repository": "https://github.com/Research-MAGIC/tela-client",
        "Bug Tracker": "https://github.com/Research-MAGIC/tela-client/issues",
    },
    license="MIT",
)