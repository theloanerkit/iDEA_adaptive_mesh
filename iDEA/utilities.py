"""Contains many utilities useful for efficient iDEA usage."""


import pickle


__all__ = [
    "Container",
    "ArrayPlaceholder",
    "Experiment",
    "save_experiment",
    "load_experiment",
]


class Container:
    r"""Empty container."""


class ArrayPlaceholder:
    r"""Array Placeholder."""


class Experiment(Container):
    r"""Container to hold all results, quantities and definitions for an experiment."""


def save_experiment(experiment: Experiment, file_name: str) -> None:
    r"""
    Save an experiment to an experiment file.

    | Args:
    |     experiment: iDEA.utilities.Experiment, Experiment object to save.
    |     file_name: str, file name.
    """
    pickle.dump(experiment, open(file_name, "wb"))


def load_experiment(file_name: str) -> Experiment:
    r"""
    Load an experiment from an experiment file.

    | Args:
    |     file_name: str, file name.

    | Returns
    |     experiment: iDEA.utilities.Experiment, Loaded Experiment object.
    """
    return pickle.load(open(file_name, "rb"))

def write_log(msg):
    with open("iDEA.log","a") as file:
        file.write(f"{msg}\n")

def fmt_log():
    with open("iDEA.log","r") as file:
        lines = [line.strip() for line in file.readlines()]
    count = 0
    with open("iDEA.log","w") as file:
        for line in lines:
            if "EXIT" in line:
                count -=1
            file.write(f"{"  "*count}{line}\n")
            if "ENTER" in line:
                count += 1