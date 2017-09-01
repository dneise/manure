from os import makedirs
from os.path import join
from os.path import exists
from datetime import datetime
import shutil
import pkg_resources
import pandas as pd
from tqdm import tqdm
from fact.credentials import create_factdb_engine
import numpy as np

OBSERVATION_RUN_KEY = 1
SQL_QUERY = '''
SELECT
    fNight, fRunID, fNumEvents
FROM
    RunInfo
WHERE
    fRunTypeKey={0}
'''.format(OBSERVATION_RUN_KEY)


def copy_top_level_readme_to(path):
    readme_res_path = pkg_resources.resource_filename(
        'fad_counters_to_gps_time', 'README.md'
    )
    shutil.copy(readme_res_path, path)


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

    def __init__(self, path, path_gens):
        self.path = path
        self.path_gens = path_gens

        runstatus = pd.read_sql(SQL_QUERY, create_factdb_engine())
        if exists(self.path):
            runstatus = runstatus.merge(
                pd.read_csv(self.path),
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
        self.runstatus.to_csv(self.path)

    def _add_paths(self):
        for row in tqdm(
            self.runstatus.itertuples(),
            desc='makings paths',
            total=len(self.runstatus)
        ):
            for name, path_gen in self.path_gens.items():
                self.runstatus.set_value(
                    row.Index,
                    name,
                    path_gen(row.fNight, row.fRunID)
                )

    def _remove_paths(self):
        self.runstatus.drop(
            labels=self.path_gens.keys(),
            axis=1,
            inplace=True,
        )


def production_main(
        path_gens,
        function_to_call_with_job,
        out_dir
):
    makedirs(out_dir, exist_ok=True)
    copy_top_level_readme_to(join(out_dir, 'README.md'))

    with RunStatus(join(out_dir, 'runstatus.csv'), path_gens) as runstatus:

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
            function_to_call_with_job(job)
            submitted_at[job.Index] = datetime.utcnow()
        runstatus['submitted_at'] = submitted_at
