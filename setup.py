from setuptools import setup

with open('requirements.txt') as file:
    requirements = [line.strip() for line in file.readlines()]

setup(
    name='telegram_bot',
    version='0.1',
    description='A (very) hacky and minimal telegram bot interface for Python.',
    url='https://github.com/ylytkin/telegram-bot',
    author='Yura Lytkin',
    author_email='jurasicus@gmail.com',
    license='MIT',
    packages=['telegram_bot'],
    install_requires=requirements,
    zip_safe=False,
)
