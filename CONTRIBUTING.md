How to contribute
=================

Thanks for your interest in contributing to Kinto!

## Reporting Bugs

Report bugs at https://github.com/Kinto/kinto-http.py/issues/new

If you are reporting a bug, please include:

 - Any details about your local setup that might be helpful in troubleshooting.
 - Detailed steps to reproduce the bug or even a PR with a failing tests if you can.


## Ready to contribute?

### System Requirements

Depending on the platform and chosen configuration, some libraries or extra services are required.

The following commands will install necessary tools for cryptography and Python packaging like Virtualenv.

#### Linux
On Debian / Ubuntu based systems:

```bash
apt-get install libffi-dev libssl-dev python-dev python-virtualenv
```

#### OS X
Assuming [brew](http://brew.sh/) is installed:

```bash
brew install libffi openssl pkg-config python

pip install virtualenv
```

### Getting Started

 -  Fork the repo on GitHub and clone locally:

```bash
git clone git@github.com:Kinto/kinto-http.py.git
git remote add {your_name} git@github.com:{your_name}/kinto-http.py.git
```

## Testing

 -  `make tests-once` to run the test with the current venv.
 -  `make tests` to run all the tests (with Py2 and Py3, flake8 and functional tests)

You may need to use `make run-kinto` before running the functional tests.
If you want to run the functional tests only, you can use `make functional`.

## Submitting Changes

```bash
git checkout master
git pull origin master
git checkout -b issue_number-bug-title
git commit # Your changes
git push -u {your_name} issue_number-bug-title
```

Then you can create a Pull-Request.
Please create your pull-request as soon as you have one commit even if it is only a failing tests. This will allow us to help and give guidance.

You will be able to update your pull-request by adding commit in your branch.
