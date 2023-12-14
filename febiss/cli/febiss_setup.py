#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__copyright__ = """
This code is licensed under the MIT license.
Copyright University Innsbruck, Institute for General, Inorganic, and Theoretical Chemistry, Podewitz Group
See LICENSE for details
"""

import os
import stat
import subprocess
import sys
import yaml

from febiss import SETTINGS_FILE, SETTINGS

default = {'installation_path': '~/.dependencies_febiss', 'openmp': True, 'cuda': True}


def help_message():
    print('This setup program installs this dependency for you and sets the global variables.')
    print('If you already have the sufficient software, you can skip this setup and write the path in \n'
          + SETTINGS_FILE + ' yourself like so:')
    print("CPPTRAJ_BIN: '/path/to/the/cpptraj/binary'\n")
    print('If you want to install the needed CPPTRAJ version with this program, you can give a yaml file\n'
          'with the wanted installation path and CPPTRAJ specifications.')
    print('An example with all possible settings:\n')
    print(yaml.dump(default))
    print("If you want to use these default options, you can also give 'default' as an argument to the program.\n")
    sys.exit()


def main():
    if len(sys.argv) != 2:
        help_message()
    arg = sys.argv[1]
    if arg.lower() in ['-h', '--help']:
        help_message()
    if arg == 'default':
        param = default
    else:
        # get settings from yamlfile given as command line argument
        if not os.path.exists(arg):
            raise RuntimeError("Could not find given yaml file " + arg)
        with open(arg, 'r') as yamlfile:
            param = yaml.safe_load(yamlfile.read().replace("\t", "  ").replace("    ", "  "))
    cwd = os.getcwd()
    # install dependencies
    inst_path = param["installation_path"]
    if '~' in inst_path:
        inst_path = os.path.expanduser(inst_path)
    # Create target directory if don't exist
    if not os.path.exists(inst_path):
        os.mkdir(inst_path)
    os.chdir(inst_path)
    subprocess.call(['git', 'clone', 'https://github.com/maberl1/cpptraj.git'])
    # change CPPTRAJ to working version
    os.chdir('cpptraj')
    # # save directories for rc file
    cpptraj_home = os.path.join(inst_path, 'cpptraj')
    os.chdir(os.path.join(inst_path, 'cpptraj'))
    # build command for configure of cpptraj and binary name based on given yaml
    configure = ['yes | bash ./configure'] #yes command downloads and installs fftw3. LM&RT20231214.
    bin_string = 'cpptraj'
    # dict.get returns None if not present, otherwise value
    if param.get('openmp'):
        configure.append("-openmp")
        bin_string += '.OMP'
    if param.get('cuda'):
        configure.append("-cuda")
        bin_string += '.cuda'
    configure.append("gnu")
    # install cpptraj
    subprocess.run(" ".join(configure), shell=True) #changed from subprocess.call. LM&RT20231214
    try:
        n_cores = os.environ['OMP_NUM_THREADS']
        subprocess.call(['make', '-j', str(n_cores)])
    except KeyError:
        subprocess.call(['make'])
    cpptraj_home = {'CPPTRAJ_BIN':os.path.join(cpptraj_home, 'bin', bin_string)}
    if not os.path.exists(cpptraj_home['CPPTRAJ_BIN']):
        raise FileNotFoundError('ERROR, the binary ' + bin_string + ' does not exist, check ' +
                                cpptraj_home['CPPTRAJ_BIN'] + ' or output above for possible reasons')
    # save settings in rc file in home
    if os.path.exists(SETTINGS_FILE):
        print('WARNING: Overwriting existing rc file.')
        while True:
            inp = input("Are you sure? [y/n] ")
            if inp.strip().lower() in ['y', 'yes']:
                break
            elif inp.strip().lower() in ['n', 'no']:
                print('Keeping old rc info. This could be wrong, please check ' + SETTINGS_FILE)
                os.chdir(cwd)
                sys.exit()
            else:
                print("Sorry wrong input, just 'y' or 'n'.")
    with open(SETTINGS_FILE, 'w') as outfile:
        yaml.dump(cpptraj_home, outfile, default_flow_style=False, allow_unicode=True)
    # move back to previous working directory
    os.chdir(cwd)
    print('\nInstallation successful, these are the saved settings:')
    print(open(SETTINGS_FILE, 'r').read())


if __name__ == '__main__':
    main()
