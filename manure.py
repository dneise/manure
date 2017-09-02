from os import makedirs
from os import remove
from os.path import exists
from os.path import dirname
from shutils import which
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
    args=['input_file_path', 'output_file_path'],
    queue='fact_medium',
    o_path=None,
    e_path=None,
):

    o_path = job[o_path] if o_path is not None else '/dev/null'
    e_path = job[e_path] if e_path is not None else '/dev/null'

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
    cmd.extend([job[arg] for arg in args])

    sp.check_output(cmd, stderr=sp.STDOUT)


def check_for_input_files(runstatus):
    input_file_exists = runstatus.input_file_exists.values.copy()
    to_check = runstatus[~runstatus.input_file_exists]
    for run in tqdm(
        to_check.itertuples(),
        desc='searching for input files',
        total=len(to_check)
    ):
        input_file_exists[run.Index] = exists(run.input_file_path)
    return input_file_exists


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
            runstatus.input_file_exists.fillna(False, inplace=True)
        else:
            runstatus['input_file_exists'] = False
            runstatus['submitted_at'] = pd.Timestamp('nat')

        self.runstatus = runstatus
        self._add_paths()

    def __enter__(self):
        return self.runstatus

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._remove_paths()

        makedirs(dirname(self.path), exist_ok=True)
        self.runstatus.to_csv(self.path)

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
        sql_query=None
):
    sql_query = sql_query if sql_query is not None else SQL_QUERY
    with RunStatus(runstatus_path, path_generators, sql_query) as runstatus:

        runstatus['input_file_exists'] = check_for_input_files(runstatus)

        runs_not_yet_submitted = runstatus[
            runstatus.input_file_exists &
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
