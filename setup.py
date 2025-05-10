from setuptools import setup, find_packages

setup(
    name="crypto-news-reporter",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "schedule>=1.2.1",
        "pandas>=2.1.4",
        "newsapi-python>=0.2.7",
        "python-dateutil>=2.8.2",
        "typing-extensions>=4.9.0",
    ],
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="A cryptocurrency news and market data reporter that sends daily email updates",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 