import argparse
import sys
import traceback
from pathlib import Path

# External
from ranger_tools.graphics.gi import GI


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        self._print_message(self.prog + " error:\n  " + message + "\n\n\n")
        self.print_help()
        self.exit(2)


def create_directory(directory: Path):
    if not directory.is_dir():
        if directory.exists():
            print("Error: Unexpected path for directory: " + str(directory.resolve()))
        else:
            try:
                directory.mkdir(parents = True)
            except Exception as exception:
                print("Error: tried creating directory " + str(directory.resolve()) + ":\n" + repr(exception))

            print("Created directory " + str(directory.resolve()))


parser = _Parser(prog = "GI to PNG (ranger-tools)",
                 description = "Small command-line tool that converts image from GI to PNG using ranger-tools library",
                 epilog = "Example:\npython " + Path(__file__).name + " test.gi test_folder/test2.gi test_folder2 "
                                                              " -o folder/example",
                 formatter_class = argparse.RawTextHelpFormatter)

current_directory = Path().resolve()

parser.add_argument( "i", type = str, default = current_directory,
                    help = "List of file names or folders with files to convert", nargs = '*',)
parser.add_argument("-o", type = str, default = current_directory,
                    help = "Output directory to save converted files to (preserving input folder structure "
                           "and replacing files if they exist)")

arguments = parser.parse_args()

output_directory = Path(arguments.o)

default_input  = arguments.i == current_directory

input_arguments = []

if default_input:
    input_arguments.append(current_directory)
else:
    input_arguments = arguments.i

files = []

for string in input_arguments:
    path = Path(string)

    if path.is_file():
        if path.suffix != ".gi":
            print("Warning: instead of GI, input file extension is " +
                  ("empty" if path.suffix == '' else path.suffix))

        files.append((path, None))
    elif path.is_dir():
        print("Recursively scanning folder " + str(path) + " for GI files")

        globbed = path.rglob("*.gi")

        for path_ in globbed:
            if path_.is_file():
                files.append((path_, path_.relative_to(path if default_input else path.parent)))
    else:
        print("Warning: unexpected input path: " + string)

if default_input or len(input_arguments) > 1 or len(files) > 100:
    answer = input("Found " + str(len(files)) + " files. Proceed with conversion to PNG? y/n\n")
    if answer.lower() not in ['y', "yes"]:
        sys.exit()

create_directory(output_directory)
if not output_directory.is_dir():
    sys.exit()

for file, relative in files:
    try:
        print("Input : " + str(file.resolve()))

        if relative is not None:
            create_directory(output_directory.joinpath(relative.parent))
            out_file = relative.with_suffix(".png")
        else:
            out_file =     file.with_suffix(".png").name

        out_file = output_directory.joinpath(out_file)

        print("Output: " + str(out_file.resolve()))

        if out_file.is_file():
            print("Warning: in output folder, rewriting file " + str(out_file.relative_to(output_directory)))
            #answer = input("Proceed? y/n\n")
            #if answer.lower() not in ['y', "yes"]:
            #    continue

        image = GI.from_gi(file.resolve()).to_image()
        image.save(out_file.resolve())
    except Exception:
        print(traceback.format_exc())