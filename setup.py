from setuptools import setup

setup(
    name='Trellis2 API Server',
    version='0.1',
    long_description=__doc__,
    packages=['trellis_api'],
    # Must be set to True to pull in globs listed in MANIFEST.in
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask']
)
