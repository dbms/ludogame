## Guidelines
1. Don't directly push to master branch.
2. Don't merge the PR to master approval.
3. Follow basic pep8 conventions and use pycharm.
4. Use Black for code formatting(later, we'll start using it).

## Project SETUP
1. $ mkdir ludoyug
2. $ cd ludoyug
3. $ virtualenv -p python3 venv
4. $ git clone https://github.com/dbms/ludoyug.git
5. $ source venv/bin/activate
6. $ cd ludoyug && pip install -r requirements.txt

## Branching Conventions
   
    Branch name should follow:
    - username/token/branch-name-by-hyphen
    WHERE
    1. username - your username
    
    2. token 
      feat - A feature branch (
      hotfix - Hotfix changes for production issues
      bugfix - A bugfix branch
      chore - Cleaning up / organizing the code
     
     3. branch-name-by-hyphen - name of the branch
     
