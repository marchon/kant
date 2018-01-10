from setuptools import setup


setup(
    name='eventstore',
    version='0.1.0',
    description='The CQRS and Event Sourcing components for Python',
    url='http://github.com/patrickporto/eventstore',
    author='Patrick Porto',
    author_email='patrick.s.porto@gmail.com',
    license='MIT',
    packages=['eventstore'],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pytest-pycodestyle',
        'pytest-cov',
    ],
    zip_safe=False,
)
