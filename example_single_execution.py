"""
Usage:
  single_execution <input_path> <output_path>

Does some kind of analyis on an input file and writes an output file.

"""
import docopt
from os.path import abspath
from os.path import dirname
from os import makedirs
import pandas as pd


def main():
    args = docopt.docopt(__doc__)
    # Using abspath here, is not needed by Manure, but by you :-D
    do_analyis(
        in_path=abspath(args['<input_path>']),
        out_path=abspath(args['<output_path>']),
    )


def do_analyis(in_path, out_path):
    results = {}
    with open(in_path) as input_file:
        # Here you would do your analysis of the input file
        # I just "measure" the length of every line of the file
        for line_number, line in enumerate(input_file):
            results[line_number] = len(line)

    # Always! make sure the output path exists, before trying to write there.
    makedirs(dirname(out_path), exist_ok=True)

    # Then store the outout file
    pd.DataFrame(results).to_csv(out_path)

if __name__ == '__main__':
    main()
