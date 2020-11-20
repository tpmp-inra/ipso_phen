import pathlib
from setuptools import find_packages, setup
from ipso_phen import version

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "readme.md").read_text()

# This call to setup() does all the work
setup(
    name="ipso_phen",
    version=version,
    description="IPSO Phen an image processing toolbox for mass phenotyping",
    long_description=README,
    long_description_content_type="text/markdown",
    url="http://github.com/tpmp-inra/ipso_phen",
    author="Felicia Antoni Maviane Macia",
    author_email="ipsophen@inra.fr",
    license="GPL v3",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: UI",
        "Intended Audience :: Developers",
        "Intended Audience :: Researchers",
        "License :: GPL v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    platforms=["Any"],
    keywords="image processing Python OpenCV",
    packages=find_packages(exclude=("tests", "docs", "video")),
    include_package_data=True,
    install_requires=[
        "matplotlib",
        "numpy==1.19.2",
        "opencv-contrib-python",
        "pandas",
        "paramiko",
        "psutil",
        "psycopg2-binary",
        "PySide2",
        "scikit-image",
        "scikit-learn",
        "seaborn",
        "SQLAlchemy",
        "SQLAlchemy-Utils",
        "tqdm",
        "Unidecode",
    ],
    entry_points={"console_scripts": ["ipso_phen=ipso_phen.__main__:main"]},
)