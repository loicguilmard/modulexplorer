from importlib import import_module
from importlib.metadata import version
from inspect import getmodule
from pkgutil import walk_packages
from sys import argv
from pandas import DataFrame, concat
from pickle import dump, load as pkload
from os.path import isfile


def addpathtoname(grandparent, dictionary):
    """
    it add grandparent. str in front of the string of the name key
    :param grandparent:
    :param dictionary:
    :return: dict
    """
    dictionary["name"] = grandparent+"."+dictionary["name"]
    return dictionary


def moduledict(objectvariable):
    """
    This function generate the top dictionnary for a module
    :param objectvariable: is a python object
    :return: dict of name, type, child
    """
    return {"name": objectvariable.__name__,
            #"type": type(objectvariable),
            "child": [name for name in dir(objectvariable) if not name.startswith('__')]
            }


def generator_subtyping(path, parent):
    """
    This generator explore the subitems and return the classes or functions
    :param path:
    :param parent:
    :return: fullpath, type
    """
    attribute = getattr(import_module(path), parent)
    if callable(attribute):
        children = addpathtoname(path, moduledict(attribute))
        for kinder in children["child"]:
            for item in generator_subtyping(children["name"], kinder):
                print(item)
        yield addpathtoname(path, moduledict(attribute))


def pkg_submodules(package, recursive=True):
    """ Return a list of all submodules in a given package, recursively by default """

    if isinstance(package, str):
        try:
            package = import_module(package)
        except ImportError:
            return []

    submodules = []
    for _loader, name, is_pkg in walk_packages(package.__path__):
        full_name = package.__name__ + "." + name

        try:
            submodules.append(import_module(full_name))
        except ImportError:
            continue

        if recursive and is_pkg:
            submodules += pkg_submodules(full_name)

    return submodules


def frommergedlisttolistbycategory(mergedlist, category):
    """
    From the pandas frame with column "path" "items" to [{item, path}] that start with category (ie: pymodaq. or pymodaq_)
    :param mergedlist:
    :param category:
    :return: currentlist:
    """
    currentlist=[]
    for children in mergedlist[mergedlist["name"].str.startswith(category)].itertuples():
        for child in children.child:
            insertindex = [index for index, item in enumerate(currentlist) if item["item"] == child]
            if len(insertindex) == 0:
                currentlist.append({"item": child, "called": [children.name]})
            else:
                currentlist[insertindex[0]]["called"].append(children.name)
    return currentlist


modulelist: list
COLUMN_NAMES = ["name", "child"]
fulllist = DataFrame(columns=COLUMN_NAMES)
LASTPYMODAQ5INSTALLEDVERSION = "5.0.0"
LASTPYMODAQ4INSTALLEDVERSION = "4.4.6"

try:
    pymodaqversion = version("pymodaq")
except:
    pass

if __name__ == "__main__":
    if len(argv) < 2:
        if pymodaqversion.startswith("5"):
            moduleslist = ["pymodaq_gui", "pymodaq_utils", "pymodaq_data"]
        elif pymodaqversion.startswith("4"):
            moduleslist = ["pymodaq"]
        else:
            raise ("ArgumentError", "Please provide the module you want to list")
    else:
        moduleslist = argv[1:]

    fulllist = concat([fulllist,
                       DataFrame([moduledict(submodule)
                                  for module in [pkg_submodules(modulename) for modulename in moduleslist]
                                  for submodule in module])
                       ], ignore_index=True)


    # fulllist = [moduledict(submodule) for submodule in [pkg_submodules(modulename) for modulename in moduleslist]]
    #favorite_color = pickle.load(open("save.p", "rb"))
    # crappy move
    mergelist = DataFrame(columns=COLUMN_NAMES)
    if pymodaqversion.startswith("5") and isfile(LASTPYMODAQ4INSTALLEDVERSION):
        filename = LASTPYMODAQ4INSTALLEDVERSION
    elif pymodaqversion.startswith("4") and isfile(LASTPYMODAQ5INSTALLEDVERSION):
        filename = LASTPYMODAQ5INSTALLEDVERSION
    else:
        dump(fulllist, open(version("pymodaq"), "wb"))
        # insert your dump if it's not pymodaq
        exit()
    if not isfile("merged"):
        mergedlist = concat([fulllist, pkload(open(filename, "rb"))], ignore_index=True)
        dump(mergedlist, open("merged", "wb"))
    else:
        mergedlist = pkload(open("merged", "rb"))


    # matching 4 and 5
    # testmerge=list(mergedlist["name"])
    # [index for index, values in mergedlist["child"].items() if "Config" in row]
    # for children in mergedlist[mergedlist["name"].str.startswith("pymodaq.")].itertuples():
    #     for child in children.child:
    #         try:
    #             print(mergedlist.loc[[index for index, row in mergedlist["child"].items() if "Config" in row]])
    #         except:
    #             print(".", end="")
    #
    # getmodule(mergedlist.loc[[idx for idx, rw in
    #                                   mergedlist.loc[
    #                                       [index for index, row in mergedlist["child"].items() if "Config" in row]][
    #                                       "name"].str.contains("pymodaq_").items() if rw]]['name'].iloc[-1])
    listpm4 = frommergedlisttolistbycategory(mergedlist, "pymodaq.")
    listpm5 = frommergedlisttolistbycategory(mergedlist, "pymodaq_")
    # testdict = {}
    # for children in mergedlist[mergedlist["name"].str.startswith("pymodaq.")].itertuples():
    #     for child in children.child:
    #         testlist.append({"item": child, "called": children.name})
    # for children in mergedlist[mergedlist["name"].str.startswith("pymodaq.")].itertuples():
    #     for child in children.child:
    #         insertindex = [index for index, item in enumerate(testlist) if item["item"] == child]
    #         if len(insertindex) == 0:
    #             testlist.append({"item": child, "called": [children.name]})
    #         else:
    #             testlist[insertindex[0]]["called"].append(children.name)

    pymodaq4df = DataFrame(listpm4)
    pymodaq5df = DataFrame(listpm5)
    with open("callablesfrom4to5.csv", "w") as lastouput:
        lastouput.write("Object full path in v4, Object full path in v5\n")
        for lin in pymodaq4df.itertuples():
            try:
                if len(pymodaq5df[pymodaq5df['item'] == lin.item]['called']) == 0:
                    lastouput.write(str(lin.called[0])+"."+str(lin.item)+", didnt move\n")
                else:
                    shortpath = getmodule(
                        getattr(import_module(pymodaq5df[pymodaq5df['item'] == lin.item]['called'].values[0][0]),
                                lin.item)).__name__
                    if shortpath.startswith("pymodaq"):
                        lastouput.write(str(lin.called[0])+"."+str(lin.item)+", "+shortpath+"."+str(lin.item)+"\n")
            except AttributeError:
                lastouput.write(str(lin.called[0])+"."+str(lin.item)+", didnt move\n")
            except ImportError:
                print("totally changed between versions ...")

    print('test')
#[type(pymodaq_gui.utils.file_io), dir(pymodaq_gui.utils.file_io)]
#modules1 = import_module("pymodaq_gui")
# [print(item) for item in fulllist]

#dir(modules1)
