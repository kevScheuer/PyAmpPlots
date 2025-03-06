"""This script converts AmpTools .fit file(s) or its associated ROOT files into a csv.

This script is used for two fit result purposes:
1. To aggregate the AmpTools .fit files into a single .csv file for easier analysis.
2. To convert the ROOT files that the .fit files are based off of into a .csv file.
Behind the scenes, this script calls a ROOT macro for either situation.
"""

import argparse
import os
import re
import subprocess
import tempfile


def main(args: dict) -> None:

    # Error / value handling
    if not os.environ["ROOTSYS"]:
        raise EnvironmentError(
            "ROOTSYS path is not loaded. Make sure to run 'source setup_gluex.csh'\n"
        )

    if args["output"] and not args["output"].endswith(".csv"):
        args["output"] = args["output"] + ".csv"

    # args["input"] can be a file containing a list of result files, so save the list of
    # files to input_files. Otherwise, input_files is just args["input"]
    input_files = []
    if (
        len(args["input"]) == 1
        and os.path.isfile(args["input"][0])
        and not args["input"][0].endswith(".fit")
        and not args["input"][0].endswith(".root")
    ):
        with open(args["input"][0], "r") as file:
            input_files = [line.strip() for line in file if line.strip()]
    else:
        input_files = args["input"]

    # Check if all input files exist, and expand to its absolute path
    print("Checking if all input files exist...")
    for file in input_files:
        if not os.path.exists(file):
            raise FileNotFoundError(f"The file {file} does not exist")
        if not os.path.isabs(file):
            input_files[input_files.index(file)] = os.path.abspath(file)

    if all(file.endswith(".fit") for file in input_files):
        file_type = "fit"
    elif all(file.endswith(".root") for file in input_files):
        file_type = "root"
    else:
        raise ValueError(
            "All input files must be of the same type: either .fit or .root files"
        )

    # sort the input files
    input_files = (
        sort_input_files(input_files, args["sort_index"])
        if args["sorted"]
        else input_files
    )

    if args["preview"]:
        print("Files that will be processed:")
        for file in input_files:
            print(f"\t{file}")
        return

    # get the script directory to properly call the script with the right path
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # hand off the files to the macro as a tempfile, where each file is on a newline
    # this seems to improve the speed of subprocess.Popen
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp_file:
        temp_file.write("\n".join(input_files))
        temp_file_path = temp_file.name
    print(f"Temp file created at {temp_file_path}")

    # convert this flag into bool integers for the ROOT macro to interpret
    is_acceptance_corrected = 1 if args["acceptance_corrected"] else 0

    # setup ROOT command with appropriate arguments
    package = ""
    if file_type == "fit":
        output_file_name = "fits.csv" if not args["output"] else args["output"]
        command = (
            f'{script_dir}/extract_fit_results.cc("{temp_file_path}",'
            f' "{output_file_name}", {is_acceptance_corrected})'
        )
        package = "loadAmpTools.C"
    elif file_type == "root":
        output_file_name = "data.csv" if not args["output"] else args["output"]
        if args["fsroot"]:
            command = (
                f'{script_dir}/extract_bin_info_fsroot.cc("{temp_file_path}",'
                f" \"{output_file_name}\", \"{args['tree_name']}\","
                f" \"{args['meson_index']}\")\n "
            )
            package = "$FSROOT/rootlogon.FSROOT.C"
        else:
            command = (
                f'{script_dir}/extract_bin_info.cc("{temp_file_path}",'
                f" \"{output_file_name}\", \"{args['mass_branch']}\")"
            )
    else:
        raise ValueError("Invalid type. Must be either 'fit' or 'root'")

    command = ["root", "-n", "-l", "-b", "-q", package, command]

    print("Running ROOT macro...")
    # call the ROOT macro
    proc = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # print the output of the ROOT macro as it runs
    if args["verbose"]:
        for line in iter(proc.stdout.readline, ""):
            print(line, end="")
    proc.wait()  # wait for the process to finish and update the return code
    if proc.returncode != 0:
        print("Error while running ROOT macro:")
        for line in iter(proc.stderr.readline, ""):
            print(line, end="")
    else:
        print("ROOT macro completed successfully")

    return


def parse_args() -> dict:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-i",
        "--input",
        help=(
            "Input file(s). Also accepts path(s) with a wildcard '*' and finds all"
            " matching files. Can also accept a file containing a list of files"
        ),
        nargs="+",
    )
    parser.add_argument(
        "-s",
        "--sorted",
        type=bool,
        default=True,
        help=(
            "Sort the input files by last number in the file name or path. Defaults"
            " to True, so that the index of each csv row matches the ordering of the"
            " input files"
        ),
    )
    parser.add_argument(
        "--sort-index",
        type=int,
        default=-1,
        help=(
            "Determines what number in the file path is used for sorting. Defaults to"
            " -1, so that the last number in the path is used."
        ),
    )
    parser.add_argument(
        "-o", "--output", default="", help="File name of output .csv file"
    )
    parser.add_argument(
        "-a",
        "--acceptance-corrected",
        action="store_true",
        help=(
            "When passed, the amplitude intensities are corrected for acceptance. These"
            " are the true 'generated' values with no detector effects. Defaults to"
            " False, or the 'reconstructed' values"
        ),
    )
    parser.add_argument(
        "-m",
        "--mass-branch",
        type=str,
        default="M4Pi",
        help=(
            "Name of branch for the final invariant mass combo of interest in the"
            " Amplitude Analysis. Note this is only applicable when attempting to"
            " create csv's for ROOT data files. Defaults to M4Pi"
        ),
    )
    parser.add_argument(
        "-p",
        "--preview",
        action="store_true",
        help=("When passed, print out the files that will be processed and exit."),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print out more information while running the script",
    )
    parser.add_argument(
        "-f",
        "--fsroot",
        action="store_true",
        help=(
            "Indicates that the data input file is in FSRoot format. Needs to be used"
            " in conjunction with -nt and -mi arguments"
        ),
    )
    parser.add_argument(
        "-nt",
        "--tree-name",
        type=str,
        default="ntFSGlueX_100_221",
        help=("FSRoot tree name"),
    )
    parser.add_argument(
        "-mi",
        "--meson-index",
        type=str,
        default="2,3,4,5",
        help=(
            "Indices of the particles coming from the meson vertex. Only relevant for"
            " FSRoot formatted data files"
        ),
    )
    return vars(parser.parse_args())


def sort_input_files(input_files: list, position: int = -1) -> list:
    """Sort the input files based off the last number in the file name or path

    Args:
        input_files (list): input files to be sorted
        position (int, optional): Index position of the number to be sorted on in the
            full path. Defaults to -1, meaning the last number is used for sorting. Be
            careful using this, as it will assume all path names have the same amount of
            distinct numbers, and thus the same indices.

    Returns:
        list: sorted list of files
    """

    def extract_last_number(full_path: str) -> float:
        numbers = re.findall(r"(?:\d*\.*\d+)", full_path)
        return float(numbers[position]) if numbers else float("inf")

    return sorted(input_files, key=extract_last_number)


if __name__ == "__main__":
    args = parse_args()
    main(args)
