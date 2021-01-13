from zipfile import ZipFile
from git import Repo
from pprint import pprint
from pathlib import Path
import template as templateEngine
import click
import os
import requests
import json
import shutil
import stat
import config
import subprocess
from colorama import init
init()

@click.group()
def cli():
    pass


@click.command(name='create')
@click.argument('project')
@click.option('--path', '-p', default="D:/projects", help="path to store the project")
@click.option('--github/--no-github', default=True, help='Sets up a repository on github')
@click.option('--git/--no-git', default=True, help='sets up a local git instance')
@click.option('--public/--private', default=True, help='make github repo public or private')
@click.option('--local-branch', default='origin', help="the name of the local branch")
@click.option('--remote-branch', default='main', help="the name of the remote branch")
@click.option('--language', '-l', default="", help="The language you want to use")
@click.option('--gitignore', is_flag=True, help='Option to create a gitignore *depends on if --gitignore-template or --language is set')
@click.option('--gitignore-template', default=None, help='Template to select for the gitignore')
@click.option('--template', '-t', default=None, help='project template. if enabled it ignores the gitignore template')
@click.option('--editor', '-e', default=None, help='editor to open the project in')
def createProject(project, path, github, git, public, local_branch, remote_branch, language, gitignore, gitignore_template, template, editor):
    # create the correct path obj to save the project to by combining the
    # path to the projectfolder the language and the name of the project
    projectPath = os.path.join(path, language, project)

    # check if the path exists if it does exist throw an error else create it
    if not os.path.exists(projectPath):
        os.makedirs(projectPath)
    else:
        return print("\033[91m\033[1mthe project folder already has a file/folder named: \"{}\" \033[0m".format(project))

    # at this point the path to save the project is created and valid

    # when the folder is created we check if the user wants to open a editor in
    # the folder of the project. if they do want to we check if it exists in the config
    if not editor == None:
        editor_obj = config.Get(f'editors.{editor}')

        if not editor_obj == None:
            # if the editor has an entry in the config we get the command
            # to launch it add the path to the correct place in the command
            # and then we execute it in the terminal launching the editor
            cmd = editor_obj.format(projectPath)
            subprocess.Popen(cmd, shell=True)

    # we check if the user wants to use a template and if he dies we give
    # a call to the template engine to use the template
    if not template == None:
        templateEngine.use(template, projectPath)

    # we check if the user wants to create a git instance in the root of the project.
    # if the user doesnt want a git repo we exit out here because all
    # future options require a git repository to be usefull
    if not git:
        return print("The project was created succesfully")
    # initialize the git repo and create a instance to make git commands
    repo = Repo.init(projectPath)
    git = repo.git

    # we check if the folder has files.
    # if it doesnt have files we create a readme so we can make a commit
    if not any(Path(projectPath).iterdir()):
        with open(os.path.join(projectPath, 'README.md'), 'w') as f:
            f.write(f'# {project}')

    # we check if the user wants to use a gitignore file. but if the user is
    # using a template we dont want to create a gitignore because
    # the templates already have the needed gitignore file
    if gitignore and template == None:
        # here we want to test if the user has selected either a language ort a
        # gitignore template because we need to use that to create a good gitignore file
        # we dont require the user to use both because we can generate
        # templates based on either the language, template and both
        if language == None and gitignore_template == None:
            return print("\033[91m\033[1m neither language or gitignore template are set \033[0m")

        # at this point we create a gitignore file and 
        # fill it with data from the toptal gitignore api
        with open(os.path.join(projectPath, '.gitignore'), 'w') as f:

            user_template = f'{language},{gitignore_template}'
            r = requests.get(
                f'https://www.toptal.com/developers/gitignore/api/{user_template}')

            f.write(r.text)

    #at this point we are cetain that we have files in our project 
    # so we create a commit and the main branch
    git.execute('git add -A')
    git.commit(message="Initial commit")
    repo.create_head('main')

    # at this point we test if the user wants to create a github repository
    if not github:
        return print("\033[92m The Project has been created succesfully \033[0m")


    github_token = config.Get('github.token')
    if github_token == None: 
        return print ("failed to create a github repository. token not found at (github.token)")
    data = {
        "name": project,
        "private": not public,
        "auto_init": False,
    }
    r = requests.post(
        url="https://api.github.com/user/repos",
        data=json.dumps(data),
        auth=('', github_token),
        headers={"Content-Type": "application/json"})

    if not r.status_code == 201:
        return print("\033[91m\033[1m There was an error with the creation of the repository. the token is invalid or the repository already exists \033[0m")

    #once we succesfully create the repository we get the contents of the request as json 
    github_repo = r.json()

    #once we have the content of the repo we add a remote with the url to push to  
    repo.create_remote(local_branch, github_repo["ssh_url"],)
    git.execute(f"git push -u {local_branch} {remote_branch}")


@click.command('archive')
@click.argument('project')
@click.option('--path', '-p', default="D:/projects", help="path to the project folder")
@click.option('--name', '-n')
@click.option('--format', '-f', default='zip', help='the format to zip the project to')
def archiveProject(project, path, name, format):
    # we get the path of the project and compress it with the give compression algorithm 
    projectFolder = os.path.join(path, project)
    shutil.make_archive(projectFolder, format, projectFolder)


@click.command('delete')
@click.argument('project')
@click.option('--path', '-p', default="D:/projects", help="path to the project folder")
@click.option('--delete-github', is_flag=True, help="delete the github repositiory")
@click.option('--delete-files', is_flag=True, help="delete the local files")
@click.option('--archive-files', default=False, help="archive files before deleting. accepts the compression algorithm")
def deleteProject(project, path, delete_files, delete_github, archive_files):
    # this command is for the  user to delete a project. 
    # with this command the user can delete the files, github repo 
    # and create a archive of the project to store somewhere else.

    #we check if the user wants to delete the github repo.
    if delete_github:

        # we get the token displayed in the repo to get the username of the github 
        # user so we can delete the repo without asking for the users username
        github_token = config.Get("github.token")
        if github_token == None:
            return print("there was an error getting the token")
        repo_owner = get_repo_owner(github_token)

        # once we have the token and the username we make a call 
        # to the github api to delete the repo
        r = requests.delete(
            url=f"https://api.github.com/repos/{repo_owner}/{project}",
            auth=('', github_token))

        # we check if the status code is 204 which means there is no 
        # content which means it is deleted succesfully
        if not r.status_code == 204:
            print(r.status_code)
            return print("there was an error")

    # after we deleted the github repo we check if the user wants to 
    # create a archive of the files so we can archive it for the user.= 
    projectDir = os.path.join(path, project) + "/"
    if archive_files:
        shutil.make_archive(projectDir, archive_files, projectDir)

    # after we have archived the project we check if the user wants to delete the
    # files and if he does we remove all of the files except the archive
    if delete_files:
        shutil.rmtree(projectDir, onerror=on_rm_error)


@click.command('set')
@click.argument('path')
@click.argument('value')
def set_config(path, value):
    # this is a command to set the fields of the setup so you dont have to do it manualy
    config.Set(path, value)


@click.command('create-from-folder')
@click.option('--path', '-p', default=None, help="Path at which the folder is located")
def create_template_from_folder():
    pass


@click.command('convert-templates')
def convert_templates():
    # this is a command to covert all the templates to a tar archive compressed with 
    # the lzma algorithm 
    templateEngine.convert_templates_to_xztar()

# HELPER FUNCTIONS
def on_rm_error(func, path, exc_info):
    # helpre function to remove the files
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def get_repo_owner(token):
    #function to get the owner of a repository
    r = requests.get('https://api.github.com/user', auth=('', token))

    if r.status_code == 200:
        return r.json()["login"]
    return None


cli.add_command(createProject)
cli.add_command(archiveProject)
cli.add_command(deleteProject)
cli.add_command(set_config)
cli.add_command(convert_templates)
cli.add_command(create_template_from_folder)
if __name__ == "__main__":
    cli()
    # pass
