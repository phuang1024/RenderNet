import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="brn",
    description="Render farm system for Blender",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/phuang1024/RenderNet",
    author="Patrick Huang",
    author_email="phuang1024@gmail.com",
    license="GPL-3.0",
    packages=setuptools.find_packages(),
    install_requires=[
        "bcon",
    ],
    entry_points={
        "console_scripts": [
            "brn=brn.__main__:main",
        ],
    },
)
