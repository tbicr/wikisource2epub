from setuptools import setup, find_packages


setup(
    name='wikisource2epub',
    version='0.0.1',
    description='wikisource to epub converter',
    author='Pavel Tyslacki',
    author_email='pavel.tyslacki@gmail.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    scripts=['wikisource2epub.py'],
    install_requires=open('requirements.txt').read().strip().splitlines(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
