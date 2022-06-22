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
        "click",
        "ndspy>=4.0.0",
        "pydantic",
        "vidua",
        "zed @ git+https://github.com/phst-randomizer/zed.git",
    ],
)
