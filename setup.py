from setuptools import setup, find_packages

# read version as __version__
exec(open('mosaic/version.py').read())


setup(name='mosaic',
      version=__version__,
      url='https://github.com/edgemind-sas/mosaic',
      author='Roland Donat',
      author_email='roland.donat@gmail.com, roland.donat@edgemind.net, roland.donat@alphabayes.fr',
      maintainer='Roland Donat',
      maintainer_email='roland.donat@gmail.com',
      keywords='trading machine-learning algorithmic backtesting',
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
      python_requires='>=3.10',
      install_requires=[
          "pydantic==1.10.4",
          "pyyaml==6.0",
          "pandas==1.5.3",
          "ccxt==2.7.12",
          "plotly==5.13.0",
          "pandas-ta==0.3.14b0",
          "tzlocal==5.0.1",
          "statsmodels==0.14.0",
          "tqdm==4.64.1",
          "colored==2.2.3",
          "pymongo==4.4.1",
          "influxdb==5.3.1",
          "scikit-learn==1.3.2",
      ],
      zip_safe=False,
      )
