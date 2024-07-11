import setuptools

setuptools.setup(
    name="pyagena",
    version="1.0.3",
    author="Erhan Pisirir, Eugene Dementiev",
    author_email="support@agenarisk.com",
    description="Python utility library for agena.ai to create Bayesian network models from scratch or import existing models and export to agena.ai cloud or local API for calculations.",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AgenaRisk/api-py",
    download_url="https://github.com/AgenaRisk/api-py/archive/refs/tags/1.0.3.tar.gz",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=['requests','pandas','networkx','matplotlib'],
    include_package_data=True
)
