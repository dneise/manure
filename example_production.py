#!/bin/env python
from os.path import join
from fact.path import tree_path
from functools import partial
import manure

input_dir = '/fact/foo'
out_dir = '/fact/bar'

manure.production_main(
    path_generators={
        'input_file_path':  partial(tree_path, input_dir, '.fits.fz'),
        'output_file_path': partial(tree_path, out_dir, '.csv'),
    },
    submission=partial(
        manure.qsub,
        binary_name='single_execution',
        args=['input_file_path', 'output_file_path'],
    ),
    runstatus_path=join(out_dir, 'runstatus.csv')
)
