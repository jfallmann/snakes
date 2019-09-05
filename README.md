# snakes

Collection of snakemake workflows for NGS analysis from mapping to featurecount and track generation

## HowTo

For details on ```snakemake``` and it's features please refer to the [snakemake documentation](https://snakemake.readthedocs.io/en/stable/tutorial/tutorial.html).

In general it is necessary to write a configuration file containing information on paths, files to process and settings beyond default for mapping tools and others.
For examples on this please have a look into the ```config``` directory.

For ```snakemake``` to be fully FAIR, one needs to use ```conda``` or similar environment management systems. For details on ```conda``` please refer to the [conda manual](https://docs.conda.io/en/latest/).

This workflow collection makes heavy use of ```conda``` and especially the [bioconda](https://bioconda.github.io) channel.

For distribution of jobs one can either rely on local hardware, use scheduling software like the [SGE](https://docs.oracle.com/cd/E19957-01/820-0699/chp1-1/index.html) or [Slurm](https://slurm.schedmd.com/documentation.html).

This manual will only show examples on local and SGE usage, but more information on how to use other scheduling software is available elsewhere.

### Create config.json

TODO

### Mapping
#### No cluster
```
snakemake -j ${THREADS} --configfile config.json --snakefile workflows/mapping_qc.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/mapping.log
```
#### Cluster SGE
```
snakemake --cluster "qsub -q ${QUEUENAME} -e ${PWD}/sgeerror -o ${PWD}/sgeout -N ${JOBNAME}" --jobscript Workflow/cluster/sge.sh -j ${THREADS} --configfile config.json --snakefile workflows/mapping.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/mapping.log
```

### Generating UCSC tracks
#### No cluster
```
snakemake -j ${THREADS} --configfile config.json --snakefile workflows/ucsc.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/ucsc.log
```
#### Cluster SGE
```
snakemake --cluster "qsub -q ${QUEUENAME} -e ${PWD}/sgeerror -o ${PWD}/sgeout -N ${JOBNAME}" --jobscript Workflow/cluster/sge.sh -j ${THREADS} --configfile config.json --snakefile workflows/ucsc.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/ucsc.log
```

### Annotating Bed Files
#### No cluster
```
snakemake -j ${THREADS} --configfile config.json --snakefile workflows/annotatebed.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/annotate.log
```
#### Cluster SGE
```
snakemake --cluster "qsub -q ${QUEUENAME} -e ${PWD}/sgeerror -o ${PWD}/sgeout -N ${JOBNAME}" --jobscript Workflow/cluster/sge.sh -j ${THREADS} --configfile config.json --snakefile workflows/annotatebed.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/annotate.log
```

### Counting features
#### No cluster
```
snakemake -j ${THREADS} --configfile config.json --snakefile workflows/countreads.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/counting.log
```
#### Cluster SGE
```
snakemake --cluster "qsub -q ${QUEUENAME} -e ${PWD}/sgeerror -o ${PWD}/sgeout -N ${JOBNAME}" --jobscript Workflow/cluster/sge.sh -j ${THREADS} --configfile config.json --snakefile workflows/countreads.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/counting.log
```

### Simple Peak calling
#### No cluster
```
snakemake -j ${THREADS} --configfile config.json --snakefile workflows/peak_finding.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/peaks.log
```
#### Cluster SGE
```
snakemake --cluster "qsub -q ${QUEUENAME} -e ${PWD}/sgeerror -o ${PWD}/sgeout -N ${JOBNAME}" --jobscript Workflow/cluster/sge.sh -j ${THREADS} --configfile config.json --snakefile workflows/peak_finding.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/peaks.log
```

### DE analysis (upcoming)
#### No cluster
```
snakemake -j ${THREADS} --configfile config.json --snakefile workflows/de_analysis.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/de_analysis.log
```
#### Cluster SGE
```
snakemake --cluster "qsub -q ${QUEUENAME} -e ${PWD}/sgeerror -o ${PWD}/sgeout -N ${JOBNAME}" --jobscript Workflow/cluster/sge.sh -j ${THREADS} --configfile config.json --snakefile workflows/de_analysis.smk --use-conda --directory ${PWD} --printshellcmds &> LOGS/de_analysis.log
```

