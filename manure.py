from os import makedirs
from os import remove
from os.path import exists
from os.path import dirname
from shutil import which
from datetime import datetime
import pandas as pd
from tqdm import tqdm
from fact.credentials import create_factdb_engine
import numpy as np
import subprocess as sp

OBSERVATION_RUN_KEY = 1
SQL_QUERY = '''
SELECT
    fNight, fRunID, fNumEvents
FROM
    RunInfo
WHERE
    fRunTypeKey={0}
'''.format(OBSERVATION_RUN_KEY)


def qsub(
        job,
        binary_name,
        args=[
            'input_file_path',
            'output_file_path'],
        queue='fact_medium',
        o_path=None,
        e_path=None,
        ):

    o_path = getattr(job, o_path) if o_path is not None else '/dev/null'
    e_path = getattr(job, e_path) if e_path is not None else '/dev/null'

    for p in [o_path, e_path]:
        if p == '/dev/null':
            break
        if exists(p):
            remove(p)
        else:
            makedirs(dirname(p), exist_ok=True)

    cmd = [
        'qsub',
        '-q', queue,
        '-o', o_path,
        '-e', e_path,
        which(binary_name),
    ]
    cmd.extend([getattr(job, arg) for arg in args])

    sp.check_output(cmd, stderr=sp.STDOUT)


def single_check_is_input_complete(run):
    return exists(run.input_file_path)


def check_is_input_complete(runstatus, runcheck_function):
    is_input_complete = runstatus.is_input_complete.values.copy()
    to_check = runstatus[~runstatus.is_input_complete]
    for run in tqdm(
        to_check.itertuples(),
        desc='searching for input files',
        total=len(to_check)
    ):
        is_input_complete[run.Index] = runcheck_function(run)
    return is_input_complete


class RunStatus:

    def __init__(self, path, path_generators, sql_query):
        self.path = path
        self.path_generators = path_generators

        runstatus = pd.read_sql(sql_query, create_factdb_engine())
        if exists(self.path):
            old_runstatus = pd.read_csv(self.path)
            old_runstatus['submitted_at'] = pd.to_datetime(old_runstatus.submitted_at)
            runstatus = runstatus.merge(
                old_runstatus,
                on=list(runstatus.columns),
                how='outer',
            )
            runstatus.is_input_complete.fillna(False, inplace=True)
        else:
            runstatus['is_input_complete'] = False
            runstatus['submitted_at'] = pd.Timestamp('nat')

        self.runstatus = runstatus
        self._add_paths()

    def __enter__(self):
        return self.runstatus

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._remove_paths()

        makedirs(dirname(self.path), exist_ok=True)
        self.runstatus.to_csv(
            self.path,
            index=False,
            na_rep='nan',
        )

    def _add_paths(self):
        for row in tqdm(
            self.runstatus.itertuples(),
            desc='makings paths',
            total=len(self.runstatus)
        ):
            for name, path_gen in self.path_generators.items():
                self.runstatus.set_value(
                    row.Index,
                    name,
                    path_gen(row.fNight, row.fRunID)
                )

    def _remove_paths(self):
        self.runstatus.drop(
            labels=self.path_generators.keys(),
            axis=1,
            inplace=True,
        )


def production_main(
        path_generators,
        submission,
        runstatus_path,
):
    with RunStatus(runstatus_path, path_generators, SQL_QUERY) as runstatus:

        runstatus['is_input_complete'] = check_is_input_complete(
            runstatus,
            single_check_is_input_complete
        )

        runs_not_yet_submitted = runstatus[
            runstatus.is_input_complete &
            np.isnat(runstatus.submitted_at)
        ]

        submitted_at = runstatus.submitted_at.values.copy()
        for job in tqdm(
            runs_not_yet_submitted.itertuples(),
            desc='submitting',
            total=len(runs_not_yet_submitted)
        ):
            submission(job)
            submitted_at[job.Index] = datetime.utcnow()
        runstatus['submitted_at'] = submitted_at
