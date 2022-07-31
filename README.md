# MinecraftLauncherProgramingInterface(MLPI) #


MLPI is a general Minecraft launcher programming interface, it can work on any platform (currently only supports Windows), you only need to call the interface provided by MLPI, and you don't need to pay attention to how it is implemented 

### Table of Contents
- [Background](#background) 
- [Install](#install)
- [Usage](#usage)

## Background
MLPI originated from a project of the author (see [PMCL](https://github.com/MSWorkerl/PMCL)), but because it is too troublesome to start Minecraft, the author developed MLPI

## Install
MLPI does not have setup.py for now, so python setup.py install cannot be used, you can use this command to copy MLPI to the local
```
git clone https://github.com/MSWorkerl/MLPI.git
```
Then you can copy MLPI to your project directory and use it

## Usage

### search_java function
-Return value: a dictionary containing the Java version and the path to Java

### get_minecraft_version function
- Parameters: .minecraft path
- Return value: a dictionary containing Minecraft version and Minecraft version type
