"""
SYSMIND Setup Script

Installation:
    pip install -e .

Or:
    python setup.py install
"""

from setuptools import setup, find_packages

setup(
    name='sysmind',
    version='1.0.0',
    author='SmartStudent.ai',
    author_email='contact@smartstudent.ai',
    description='System Intelligence & Automation CLI',
    long_description=open('README.md', 'r', encoding='utf-8').read() if __import__('os').path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/smartstudent-ai/sysmind',
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=[],  # No external dependencies - uses only stdlib
    entry_points={
        'console_scripts': [
            'sysmind=sysmind.cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    keywords='system monitor cli process disk network diagnostics',
)
