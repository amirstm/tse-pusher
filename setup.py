"""Building the library"""
import setuptools

setuptools.setup(
    name="tse_utils",
    version="1.0.0",
    author="Arka Equities & Securities",
    author_email="zare@arkaequities.com",
    description="Pusher for Tehran Stock Exchange data crawled from TSETMC website.",
    long_description="",  # TODO : Add long description
    packages=setuptools.find_packages(),
    install_requires=["httpx", "websockets", "tse-utils"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)
