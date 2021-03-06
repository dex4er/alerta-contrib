
from setuptools import setup, find_packages

version = '0.3.1'

setup(
    name="alerta-twilio",
    version=version,
    description='Alerta plugin for Twilio SMS',
    url='https://github.com/alerta/alerta-contrib',
    license='Apache License 2.0',
    author='Nick Satterly',
    author_email='nick.satterly@theguardian.com',
    packages=find_packages(),
    py_modules=['alerta_twilio_sms'],
    install_requires=[
        'twilio'
    ],
    include_package_data=True,
    zip_safe=True,
    entry_points={
        'alerta.plugins': [
            'twilio_sms = alerta_twilio_sms:SendSMSMessage'
        ]
    }
)
