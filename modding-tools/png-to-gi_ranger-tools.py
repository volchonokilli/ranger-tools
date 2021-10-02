import argparse
import sys
import traceback
from pathlib import Path

# External
from PIL import Image
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


parser = _Parser(prog = "PNG to GI (ranger-tools)",
                 description = "Small command-line tool that converts image from PNG to GI using ranger-tools library",
                 epilog = "Example:\npython " + Path(__file__).name + " test.png test_folder/test2.png test_folder2 "
                                                              " -o folder/example  -t 0_32",
                 formatter_class = argparse.RawTextHelpFormatter)

current_directory = Path().resolve()

parser.add_argument( "i", type = str, default = current_directory,
                    help = "List of file names or folders with files to convert", nargs = '*',)
parser.add_argument("-o", type = str, default = current_directory,
                    help = "Output directory to save converted files to (preserving input folder structure "
                           "and replacing files if they exist)")
parser.add_argument("-t", type = str, default = '2', choices = ["0_32", "0_16", '2'],
                    help = "Type of conversion:\n"
                           "  0_32 - GI type 0, 32 bit: ARGB8888\n"
                           "  0_16 - GI type 0, 16 bit:  RGB 565\n"
                           "  2    - GI type 2: GBRG3553 on two layers + alpha reduced to 6 bit on third layer")

arguments = parser.parse_args()

output_directory = Path(arguments.o)

default_input  = arguments.i == current_directory

if arguments.t == "0_32":
    type_choice = "32 bit GI type 0"
    GI_type = 0
    GI_bits = 32
elif arguments.t == "0_16":
    type_choice = "16 bit GI type 0"
    GI_type = 0
    GI_bits = 16
elif arguments.t == '2':
    type_choice = "GI type 2"
    GI_type = 2
    GI_bits = None

input_arguments = []

if default_input:
    input_arguments.append(current_directory)
else:
    input_arguments = arguments.i

files = []

for string in input_arguments:
    path = Path(string)

    if path.is_file():
        if path.suffix != ".png":
            print("Warning: instead of PNG, input file extension is " +
                  ("empty" if path.suffix == '' else path.suffix))

        files.append((path, None))
    elif path.is_dir():
        print("Recursively scanning folder " + str(path) + " for PNG files")

        globbed = path.rglob("*.png")

        for path_ in globbed:
            if path_.is_file():
                files.append((path_, path_.relative_to(path if default_input else path.parent)))
    else:
        print("Warning: unexpected input path: " + string)

if default_input or len(input_arguments) > 1 or len(files) > 100:
    answer = input("Found " + str(len(files)) + " files. Proceed with conversion to " + type_choice + "? y/n\n")
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
            out_file = relative.with_suffix(".gi")
        else:
            out_file =     file.with_suffix(".gi").name

        out_file = output_directory.joinpath(out_file)

        print("Output: " + str(out_file.resolve()))

        if out_file.is_file():
            print("Warning: in output folder, rewriting file " + str(out_file.relative_to(output_directory)))
            #answer = input("Proceed? y/n\n")
            #if answer.lower() not in ['y', "yes"]:
            #    continue

        image = Image.open(file.resolve())
        with out_file.open("wb") as output:
            output.write(GI.from_image(image, GI_type, GI_bits).to_bytes())
    except Exception:
        print(traceback.format_exc())