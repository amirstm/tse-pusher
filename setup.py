"""Building the library"""
import setuptools

setuptools.setup(
    name="tsetmc_pusher",
    version="1.0.9",
    author="Arka Equities & Securities",
    author_email="zare@arkaequities.com",
    description="Pusher for Tehran Stock Exchange data crawled from TSETMC website.",
    long_description="""\
This project uses the websocket technology to build a pusher around the realtime data \
for Tehran Stock Exchange. Source data is crawled from the TSETMC website on optimized \
intervals. Users can connect to the websocket server and subscribe to as many instruments \
as they like. Afterwards, each time data for the subscribed instruments is updated, the \
changes will be pushed to the clients.
""",
    packages=setuptools.find_packages(),
    install_requires=["httpx", "websockets", "python-dotenv", "tse-utils"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
)
