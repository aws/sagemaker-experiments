# Contributing Guidelines

Thank you for your interest in contributing to our project. Whether it's a bug report, new feature, correction, or additional
documentation, we greatly value feedback and contributions from our community.

Please read through this document before submitting any issues or pull requests to ensure we have all the necessary
information to effectively respond to your bug report or contribution.

## Table of Contents

* [Table of Contents](#table-of-contents)
* [Reporting Bugs/Feature Requests](#reporting-bugsfeature-requests)
* [Contributing via Pull Requests (PRs)](#contributing-via-pull-requests-prs)
  * [Setting up Your Development Environment *[Optional, but Recommended]*](#setting-up-your-development-environment-optional-but-recommended)  
  * [Pulling Down the Code](#pulling-down-the-code)
  * [Running the Unit Tests](#running-the-unit-tests)
  * [Running the Integration Tests](#running-the-integration-tests)
  * [Making and Testing Your Change](#making-and-testing-your-change)
  * [Committing Your Change](#committing-your-change)
  * [Sending a Pull Request](#sending-a-pull-request)
* [Finding Contributions to Work On](#finding-contributions-to-work-on)
* [Code of Conduct](#code-of-conduct)
* [Security Issue Notifications](#security-issue-notifications)
* [Licensing](#licensing)

## Reporting Bugs/Feature Requests

We welcome you to use the GitHub issue tracker to report bugs or suggest features.

When filing an issue, please check [existing open](https://github.com/aws/amazon-sagemaker-experiment-tracking/issues), or [recently closed](https://github.com/aws/amazon-sagemaker-experiment-tracking/issues?utf8=%E2%9C%93&q=is%3Aissue%20is%3Aclosed%20), issues to make sure somebody else hasn't already
reported the issue. Please try to include as much information as you can. Details like these are incredibly useful:

* A reproducible test case or series of steps
* The version of our code being used
* Any modifications you've made relevant to the bug
* Anything unusual about your environment or deployment


## Contributing via Pull Requests
Contributions via pull requests are much appreciated. Before sending us a pull request, please ensure that:

1. You are working against the latest source on the *master* branch.
2. You check existing open, and recently merged, pull requests to make sure someone else hasn't addressed the problem already.
3. You open an issue to discuss any significant work - we would hate for your time to be wasted.

To send us a pull request, please:

1. Fork the repository.
2. Modify the source; please focus on the specific change you are contributing. If you also reformat all the code, it will be hard for us to focus on your change.
3. Ensure local tests pass.
4. Commit to your fork using clear commit messages.
5. Send us a pull request, answering any default questions in the pull request interface.
6. Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

GitHub provides additional document on [forking a repository](https://help.github.com/articles/fork-a-repo/) and
[creating a pull request](https://help.github.com/articles/creating-a-pull-request/).

### Setting Up Your Development Environment 
1. all supported versions of python installed
1. pip installed
1. tox installed `pip install tox`

### Pulling Down the Code

1. If you do not already have one, create a GitHub account by following the prompts at [Join Github](https://github.com/join).
1. Create a fork of this repository on GitHub. You should end up with a fork at `https://github.com/<username>/sagemaker-experiments`.
   1. Follow the instructions at [Fork a Repo](https://help.github.com/en/articles/fork-a-repo) to fork a GitHub repository.
1. Clone your fork of the repository: `git clone https://github.com/<username>/sagemaker-experiments` where `<username>` is your github username.

### Running the Unit Tests

1. cd into the sagemaker-experiments folder: `cd sagemaker-experiments` or `cd /environment/sagemaker-experiments`
1. Run the following tox command and verify that all code checks and unit tests pass: `tox -- tests/unit`

You can also run a single test with the following command: `tox -e py36 -- -s -vv <path_to_file><file_name>::<test_function_name>`  
  * Note that the coverage test will fail if you only run a single test, so make sure to surround the command with `export IGNORE_COVERAGE=-` and `unset IGNORE_COVERAGE`
  * Example: `export IGNORE_COVERAGE=- ; tox -e py36 -- -s -vv tests/unit/test_experiment.py::test_processing_job_environment ; unset IGNORE_COVERAGE`

### Running the Integration Tests

Our CI system runs integration tests (the ones in the `tests/integ` directory), in parallel, for every Pull Request.  
You should only worry about manually running any new integration tests that you write, or integration tests that test an area of code that you've modified.  

1. Follow the instructions at [Set Up the AWS Command Line Interface (AWS CLI)](https://docs.aws.amazon.com/polly/latest/dg/setup-aws-cli.html).
1. To run a test, specify the test file and method you want to run per the following command: `tox -e py36 -- -s -vv <path_to_file><file_name>::<test_function_name>`
   * Note that the coverage test will fail if you only run a single test, so make sure to surround the command with `export IGNORE_COVERAGE=-` and `unset IGNORE_COVERAGE`
   * Example: `export IGNORE_COVERAGE=- ; tox -e py36 -- -s -vv tests/integ/test_tf_script_mode.py::test_mnist ; unset IGNORE_COVERAGE`
1. optionally run slow tests `tox -e slow-tests`

### Making and Testing Your Change

1. Create a new git branch:
     ```shell
     git checkout -b my-fix-branch master
     ```
1. Make your changes, **including unit tests** and, if appropriate, integration tests.
   1. Include unit tests when you contribute new features or make bug fixes, as they help to:
      1. Prove that your code works correctly.
      1. Guard against future breaking changes to lower the maintenance cost.
   1. Please focus on the specific change you are contributing. If you also reformat all the code, it will be hard for us to focus on your change.
1. Run all the unit tests as per [Running the Unit Tests](#running-the-unit-tests), and verify that all checks and tests pass.
1. Run ```tox -e black-format``` to format your code according to black. 

### Sending a Pull Request

GitHub provides additional document on [Creating a Pull Request](https://help.github.com/articles/creating-a-pull-request/).

Please remember to:
* Use commit messages (and PR titles) that follow the guidelines under [Committing Your Change](#committing-your-change).
* Send us a pull request, answering any default questions in the pull request interface.
* Pay attention to any automated CI failures reported in the pull request, and stay involved in the conversation.

### Committing Your Change

Prefix your commit message with one of the following to indicate the version part incremented in the next release:

| Commit Message Prefix | Version Part Incremented
| --- | ---
| break, breaking | major
| feat, feature | minor
| depr, deprecation | minor
| change, fix | patch
| doc, documentation | patch
| default | patch 

For the message use imperative style and keep things concise but informative. See [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/) for guidance.


## Finding contributions to work on
Looking at the existing issues is a great way to find something to contribute on. As our projects, by default, use the default GitHub issue labels (enhancement/bug/duplicate/help wanted/invalid/question/wontfix), looking at any ['help wanted'](https://github.com/aws/amazon-sagemaker-experiment-tracking/labels/help%20wanted) issues is a great place to start.


## Code of Conduct
This project has adopted the [Amazon Open Source Code of Conduct](https://aws.github.io/code-of-conduct).
For more information see the [Code of Conduct FAQ](https://aws.github.io/code-of-conduct-faq) or contact
opensource-codeofconduct@amazon.com with any additional questions or comments.


## Security issue notifications
If you discover a potential security issue in this project we ask that you notify AWS/Amazon Security via our [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public github issue.


## Licensing

See the [LICENSE](https://github.com/aws/amazon-sagemaker-experiment-tracking/blob/master/LICENSE) file for our project's licensing. We will ask you to confirm the licensing of your contribution.

We may ask you to sign a [Contributor License Agreement (CLA)](http://en.wikipedia.org/wiki/Contributor_License_Agreement) for larger changes.
