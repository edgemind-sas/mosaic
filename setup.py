from setuptools import setup, find_packages
import os

version = "0.0.3"

setup(name='mosaic',
      version=version,
      url='https://github.com/edgemind-sas/mosaic',
      author='Roland Donat',
      author_email='roland.donat@gmail.com, roland.donat@edgemind.fr, roland.donat@alphabayes.fr',
      maintainer='Roland Donat',
      maintainer_email='roland.donat@gmail.com',
      keywords='pronostic datascience machine-learning ',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: MIT License',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 3.7',
          'Topic :: Scientific/Engineering :: Artificial Intelligence'
      ],
      packages=find_packages(
          exclude=[
              "*.tests",
              "*.tests.*",
              "tests.*",
              "tests",
              "log",
              "log.*",
              "*.log",
              "*.log.*"
          ]
      ),
      description='',
      license='GPL V3',
      platforms='ALL',
      python_requires='>=3.7',
      install_requires=[
          "pydantic",
          "pyyaml",
          "kafka-python",
          "influxdb-client",
          "pandas",
          "ccxt"
      ],
      zip_safe=False,
      )
