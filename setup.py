from setuptools import find_packages, setup

setup(
    name="ph-randomizer",
    version="0.0.1",
    description="",
    long_description="",
    long_description_content_type="",
    license="",
    author="",
    author_email="",
    keywords="",
    classifiers=[],
    python_requires=">=3.10",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click==8.1.3",
        "inflection==0.5.1",
        "ndspy==4.0.0",
        "pydantic==1.9.1",
        "pyparsing==3.0.9",
        "vidua==0.4.4",
        "zed @ git+https://github.com/phst-randomizer/zed.git@657618af5a6bf52c690ffe4cd24b07124783b39b",
    ],
)
