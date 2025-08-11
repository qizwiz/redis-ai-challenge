"""
Setup script for redis-ai-patterns library
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="redis-ai-patterns",
    version="0.1.0",
    author="Redis AI Challenge Team",
    author_email="challenge@example.com",
    description="Redis-based AI coordination patterns for intelligent systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/redis-ai-challenge/redis-ai-patterns",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "redis>=4.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "ai": [
            "requests>=2.28.0",  # For AI API integration
            "numpy>=1.21.0",  # For tensor operations
        ],
        "emacs": [
            "subprocess32; python_version<'3.0'",  # Better subprocess for Python 2.7
        ],
    },
    entry_points={
        "console_scripts": [
            "redis-ai-demo=redis_ai_patterns.demo:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/redis-ai-challenge/redis-ai-patterns/issues",
        "Source": "https://github.com/redis-ai-challenge/redis-ai-patterns",
        "Documentation": "https://redis-ai-patterns.readthedocs.io/",
    },
    keywords="redis ai machine-learning streams homoiconic coordination patterns",
    zip_safe=False,
    include_package_data=True,
)
