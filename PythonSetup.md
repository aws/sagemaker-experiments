#### Init
You'll want to have pyenv init itself everytime you open a terminal. Assuming you're using bash, add the following to your `~/.bash_profile`:

```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bash_profile
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bash_profile
```

```
if which pyenv > /dev/null; then eval "$(pyenv init -)"; fi
```

#### Install python versions
We want to install Python 2.7.13 and Python 3.6.5 using pyenv.

```
pyenv install 2.7.13
pyenv install 3.6.5
```

You should also go ahead and activate these globally. Run:

```
pyenv global 3.6.5 2.7.13
```

## Install PyCharm
Get PyCharm CE (Community Edition) from https://www.jetbrains.com/pycharm/

## Configure PyCharm

### Fork and Clone sagemaker-experiment-tracking
Create a fork of sagemaker-experiment-tracking. Clone this to your development box:

```
git clone https://github.com/your_github_username/sagemaker-experiment-tracking.git
```

Checkout the eureka-master branch. 

```
git checkout eureka-master
```

### Create a PyCharm Project for sagemaker-experiment-tracking
The end state here is to have a PyCharm Project for sagemaker-experiment-tracking. This project uses Python 3.6.5 that you installed through pyenv. This project uses a virtualenv for Python 3.6.5 to manage project dependencies. 

1. Create new Project. Navigate to the sagemaker-experiment-tracking repo root directory.
2. Click Existing interpreter and pick whatever comes up. This doesn't matter because after you clear this dialog you'll get up a pop-up asking if you want to create from existing sources instead, which is what you want to do. Click Yes on this popup.
3. Configure environment. **Preferences** > **Project: sagemaker-experiment-tracking** > **Project Settings/Project Interpreter** > **Cog** (click the cog to the right of the Project Interpreter drop-down) >> **Add**
4. Create a new 3.6.5 virtual environment from the pyenv managed Python 3.6.5 interpreter.
5. Check: You should see a "venv" directory in your repository base directory.
6. Install dependencies. You should see a popup at the top of the editor asking to install package dependencies, do this. If you don't see this option, then you can open a terminal and do ``source venv/bin/activate; pip install -e .``
7. Check your venv/lib/python3.6/site-packages/ directory - you should see many packages installed in this folder.
8. Check your list of dependencies in **Preferences** > **Project: sagemaker-experiment-tracking** > **Project Settings/Project Interpreter**. You should see a list of dependent packages here containing a few dozen dependencies.

**Problem**: Pycharm doesn't index external dependencies. You see squigly red lines under 'numpy' or 'scipy'. **Follow guidance here**:  https://stackoverflow.com/questions/26069254/importerror-no-module-named-bottle-pycharm In particular try:
- File > Invalidate Cache. Invalidate the cache and restart. If that doesn't work then:
- In the left-hand-side navigation pane, open up venv/lib/python3.6/site-packages and mark the site-packages as a 'Sources Root' folder.
- Potentially invalidate the cache and repeat.

## Install tox
``pip install tox``

## Run unit tests with tox
This section demonstrates how to run unit tests through tox within a terminal. I haven't got tox tests running within PyCharm (through lack of trying). It's almost certainly possible to do this though. If you manage to get this going, please update this document with the steps to do so.

Open a new terminal. Within the sagemaker-experiment-tracking root directory, run:

```
tox -e py36,py27 -- tests/unit
```

## Run code style enforcers with tox
```
tox -e flake8
tox -e pylint
tox -e black-format
```

## Document Lifecycle
This document should be removed prior to GA and merge with master branch of sagemaker-experiment-tracking.