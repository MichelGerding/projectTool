from zipfile import ZipFile
from time import sleep
import config
import subprocess
import shutil
import os
import lzma
import glob
import pathlib
import json
import tarfile

#function
def use(template, projectPath):
    """ 
    create a new project using the supplied template

    Input:
        template: the name of the template speciefied in config.json 
        projectPath: the path for the project to be created with the project.

    Output: 
        Boolean: a boolean if the template is loaded correctly
    """
    temp = config.Get(f'template.templates.{template}')

    # test if the template exists
    if not temp == None:
        try:
            # get the correct path to the template file
            template_folder_location = config.Get('template.folder_path')
            template_location = os.path.join(template_folder_location, temp["location"])

            #unpack the template to the project folder
            shutil.unpack_archive(template_location, projectPath)
            print("template has been extracted")
            if len(cmd:=temp["cmd"]) > 0:
                # if there are commands needed to setup the template execute them
                for command in cmd:
                    subprocess.Popen(command,cwd=projectPath, shell=True)
                print("commands have been executed")
            
            return True # template was loaded
        except:
            pass
    return False # there was an error or no template found


def convert_templates_to_xztar(config_path_to_templates="template.templates"):
    """ convert templates with different compression types to xztar for optimale storage. """

    template_folder = config.Get('template.folder_path')
    templates = config.Get(config_path_to_templates)
    
    #check if there are templates in the template folder
    if templates == None or len(templates) <= 0 :
        return 

    #loop throug all templates
    for template_name in templates:
        template = templates[template_name]
        location, extension = os.path.splitext(template["location"])

        # if the extension is not a .xz file it gets turned into one
        if not extension == ".xz":
            zip_location = os.path.join(template_folder, template["location"])

            temp_folder = os.path.join(pathlib.Path(__file__).parent.absolute(), '.tmp')
            shutil.unpack_archive(zip_location, temp_folder)

            # generate the correct name for the folder etc c:/path/to/template/react
            # we leave the .tar.xz from the end because it will be added when archiving it
            save_folder = os.path.join(template_folder, location)[:-4]
            shutil.make_archive(save_folder, 'xztar', temp_folder)

            #create the correct realtive path from the templates folder to add as location 
            config_location = save_folder.split('/')[-1] + ".tar.xz"
            config.Set(f'template.templates.{template_name}.location', config_location)


            # empty the .tmp folder so there are no files to dirty up the next templates
            list_dir = os.listdir(temp_folder)
            for filename in list_dir:
                file_path = os.path.join(temp_folder, filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    print("deleting file:", file_path)
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    print("deleting folder:", file_path)
                    shutil.rmtree(file_path)


def create_from_folder(name, commands=[], folder_path=None, folder_blacklist=[], file_blacklist = [], extension_blacklist=[], update=False):
    """ 
    a function to create a new template fromm the folder the file is called from or the folder given in the function call.
    if the name of the tempalte exists it will cancel the creation of the template
    
    Input:
        name: thename for the template you want to create
        commands: a list of commands you need to set up the template
        folder_path: the path to the folder the template is in. if not given it will take the folder from where the script is called
        folder_blacklist: a list of folders you dont want to include in the template
        file_blacklist: a list of filenames with exstension you dont want to include in the template
        extension_blacklist: a list of extensions you dont want to include in the template
        update: if true it skips the check if the template already exists
    """
    if name in config.Get('template.templates') and not update:
        print("The template already exists")
        return False

    # if there is no path given for the folder grab the folder the command is run from\
    if folder_path == None:
        folder_path = pathlib.Path().absolute()

    # get the folder to save the template to after compression
    template_folder = os.path.join(config.Get('template.folder_path'), name)

    # create a tarfile with xz compression
    with tarfile.open(template_folder + ".tar.xz", "w:xz") as tar:

        # walk throug the folders in the template to save all but the blacklisted 
        # folders,files and extensions
        for dirname, subdirs, files in os.walk(folder_path):
            # chekc if the file is not in the folder blacklisst
            for folder in folder_blacklist:
                if folder in subdirs:
                    subdirs.remove(folder)

            for filename in files:

                # check if the extension of the file is in the blacklist
                extension = os.path.splitext(filename)[1]
                if extension in extension_blacklist:
                    continue

                # check if the file is in the extension blacklist
                if filename in file_blacklist:
                    continue
                # if it reaches this point the file is not in any blakclist and 
                # will be saved to the tarfile

                # here we get the path of the file in the tarfile by 
                # taking the path to the file and removing the path to the 
                # root of the new template and a extra character for the /.
                file_path = os.path.join(dirname,filename)
                arcname = file_path[len(str(folder_path)) +1:]

                tar.add(file_path, arcname=arcname)
        
        print(f"Template: \"{name}\" created succesfully")
    # Add the template to the config file and add any necesary commands
    config.Set(f'template.templates.{name}.location', f"{name}.tar.xz")
    config.Set(f'template.templates.{name}.cmd', commands)

    
if __name__== "__main__":
    pass