from setuptools import setup

setup(name='serdepa',
      version='0.2.0',
      description='Binary packet serialization and deserialization library.',
      url='https://github.com/thinnect/serdepa',
      author='Raido Pahtma, ...',
      author_email='github@thinnect.com',
      license='MIT',
      packages=['serdepa'],
      test_suite='nose.collector',
      tests_require=['nose'],
      zip_safe=False)
