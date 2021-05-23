"""Setup for the wrangling package."""

import setuptools

setuptools.setup(
    name="wrangling",
    version="2.1.1",
    url="https://github.com/ebentley17/Deniz_lab_code",
    author="Emily Bentley",
    author_email="ebentley@scripps.edu",
    description="Wrangling data output from Deniz lab instruments into useable formats.",
    long_description=open('README.md').read(),
    packages=setuptools.find_packages(),
    # testing packages not listed here
    install_requires=["pandas", "numpy", "bokeh", "xlrd"],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8.8',
    ],
    include_package_data=True,
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
)