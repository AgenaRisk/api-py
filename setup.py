import setuptools

setuptools.setup(
    name="pyagena",
    version="1.0.0",
    author="Erhan Pisirir",
    author_email="erhanpisirir@gmail.com",
    description="Python wrapper for agena.ai to create Bayesian network models from scratch or import existing models and export to agena.ai cloud or local API for calculations.",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AgenaRisk/api-py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=['requests','pandas','networkx','matplotlib'],
    include_package_data=True
)