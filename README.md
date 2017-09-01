# manure
Very lightweight, helps "production" as typically done in FACT. Be it analysis or simulation

# How to make use of manure:

## 1.) Write an **executable** analysis, taking at least two parameters

 * an input file name to be analysed
 * an output file name to write the output to

Look at `example_single_execution.py` to get the idea. Make sure the analysis
is executable and in the PATH. You can do so, by using the entry_points console_scripts
in your setup.py.
But it is also just fine to:

    chmod u+x example_single_execution.py
    mv example_single_execution.py ~/bin

This assumes you have a `~/bin` folder in your home, and that it is in your PATH.

**NOTE:** Make sure you play around with this (single file) analysis a bit
does it always write the outputfile? Even when the path to the outfile does not
yet exist? Great. That's what we want.

## 2.) Write a (small) production script

Have a look at `example_production.py`. It is also an executable file,
since we plan to have [cron](https://en.wikipedia.org/wiki/Cron) executing
our production script once per day (or per hour) to make sure not only those
files currently on disk are analysed, but also thos which are coming
in every day from the telescope.

For a certain analysis, often the
place where to find the input files is fixed for all times. So is the output.
So we write them into this file (and plan to check it in, so we document how and
where the production is writing its output to).

Next we call the `manure.production_main`. It will look at the FACT RunInfo DB
and start your analysis for all runs. Manure assumes your analysis is somehow
run based. So in order for manure to find your input files, you need to write
a function, that takes a (night, run) tuple and generates a path. You analysis
can depend on as many input files per job as you like and it can write as many output files
as it likes.

You have to provide one function per path your single_execution.py needs.
The names are basically up to you, but you have to provide at least `input_file_path`.

Next you'll have to provide a function, that takes a `job` and submits this job
to the scheduling system you wanna use. At ISDC we use *qsub* and manure brings
`manure.qsub` for you to use.

This README has a lot of text, nearly as much as manure has lines of code.
So from here on, I'd like to ask you to play around, ask me, or read the code.
Cheers
    Dom

### why the name?

I wanted to call it manufacture, but I don't like always adding the "fact" to all [fact related](https://github.com/fact-project/) software I write. So I took the fact out of manu-fact-ure, hence "manure". I hope it helps you growing your analysis results as much as it helped me.
