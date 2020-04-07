DASBIN, DASENV = env_bin_from_config3(config,'DAS')
COUNTBIN, COUNTENV = ['featureCounts','countreads']#env_bin_from_config2(SAMPLES,config,'COUNTING')

outdir="DAS/EDGER/"
comparison=comparable_as_string(config,'DAS')

rule themall:
    input:  plot = expand("{outdir}{comparison}.png", outdir=outdir, comparison=comparison.split(",")),
            bcv = expand("{outdir}BCV.png", outdir=outdir),
            mds = expand("{outdir}MDS.png", outdir=outdir),
            tbl = expand("{outdir}normalized_table.tsv", outdir=outdir)

rule featurecount_unique:
    input:  reads = "UNIQUE_MAPPED/{file}_mapped_sorted_unique.bam"
    output: cts   = "COUNTS/Featurecounter_edger/{file}_mapped_sorted_unique.counts"
    log:    "LOGS/{file}/featurecount_edger_unique.log"
    conda:  "snakes/envs/"+COUNTENV+".yaml"
    threads: MAXTHREAD
    params: count = COUNTBIN,
            anno  = lambda wildcards: str.join(os.sep,[config["REFERENCE"],os.path.dirname(genomepath(wildcards.file, config)),tool_params(wildcards.file, None, config, 'DAS')['ANNOTATION']]),
            cpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(wildcards.file, None ,config, "DAS")['OPTIONS'][0].items()),
            paired   = lambda x: '-p' if paired == 'paired' else '',
            stranded = lambda x: '-s 1' if stranded == 'fr' else '-s 2' if stranded == 'rf' else ''
    shell:  "{params.count} -T {threads} {params.cpara} {params.paired} {params.stranded} -a <(zcat {params.anno}) -o {output.cts} {input.reads} 2> {log}"

rule prepare_count_table:
    input:   cnd  = expand(rules.featurecount_unique.output.cts, file=samplecond(SAMPLES,config))
    output:  tbl  = "DAS/Tables/EDGER/COUNTS.gz",
             anno = "DAS/Tables/EDGER/ANNOTATION.gz"
    log:     "LOGS/DAS/prepare_count_table.log"
    conda:   "snakes/envs/"+DASENV+".yaml"
    threads: 1
    params:  dereps = lambda wildcards, input: get_reps(input.cnd,config,'DAS'),
             bins = BINS
    shell: "{params.bins}/Analysis/DE/build_DESeq_table.py {params.dereps} --table {output.tbl} --anno {output.anno} --loglevel DEBUG 2> {log}"

rule run_edger:
    input:  tbl = rules.prepare_count_table.output.tbl,
            anno = rules.prepare_count_table.output.anno,
    output: rules.themall.input.plot,
            rules.themall.input.bcv,
            rules.themall.input.mds,
            rules.themall.input.tbl
    log:    "LOGS/DAS/run_edger.log"
    conda:  "snakes/envs/"+DASENV+".yaml"
    threads: 1
    params: bins   = str.join(os.sep,[BINS,DASBIN]),
            outdir = outdir,
            compare = comparison
    shell: "Rscript --no-environ --no-restore --no-save {params.bins} {input.tbl} {input.anno} {params.outdir} {params.compare} 2> {log} "


# rule run_script_edger:
#     input:  cnts = expand(rules.featurecount_unique.output, file=samplecond(SAMPLES,config)),
#             anno = expand("{ref}/{gen}/{anno}", ref=REFERENCE, gen=os.path.dirname(genomepath(SAMPLES[0],config)), anno=config['DAS']['ANNOTATION'])
#     output: rules.themall.input.all,
#             rules.themall.input.tbl,
#             rules.themall.input.plot,
#             rules.themall.input.bcv,
#             rules.themall.input.qld,
#             rules.themall.input.mds
#     log:    "LOGS/DAS/run_edger.log"
#     conda:  "snakes/envs/"+DASENV+".yaml"
#     threads:int(MAXTHREAD-1) if int(MAXTHREAD-1) >= 1 else 1
#     params: bins   = str.join(os.sep,[BINS,DASBIN]),
#             outdir = outdir,
#             compare = comparison,
#     shell:  "Rscript --no-environ --no-restore --no-save {params.bins} {params.outdir} {params.compare} {threads} {input.anno} {input.cnts} 2> {log} "



# rule prepare_count_annotation:
#     input:   anno   = expand("{ref}/{gen}/{anno}", ref=REFERENCE, gen=os.path.dirname(genomepath(SAMPLES[0],config)), anno=tool_params(SAMPLES[0], None, config, 'DAS')['ANNOTATION'])
#     output:  countgtf = expand("{ref}/{gen}/{countanno}", ref=REFERENCE, gen=os.path.dirname(genomepath(SAMPLES[0],config)), countanno=tool_params(SAMPLES[0], None, config, 'DAS')['ANNOTATION'].replace('.gtf','_fc_edger.gtf')),
#              deugtf   = expand("{ref}/{gen}/{deuanno}", ref=REFERENCE, gen=os.path.dirname(genomepath(SAMPLES[0],config)), deuanno=tool_params(SAMPLES[0], None, config, 'DAS')['ANNOTATION'].replace('.gtf','_edger.gtf'))
#     log:     "LOGS/featurecount_edger_unique.log"
#     conda:   "snakes/envs/"+COUNTENV+".yaml"
#     threads: MAXTHREAD
#     params:  bins = BINS,
#              countstrand = lambda x: '-s' if stranded == 'fr' or stranded == 'rf' else ''
#     shell:  "{params.bins}/Analysis/DEU/prepare_deu_annotation2.py -f {output.countgtf} {params.countstrand} {input.anno} {output.deugtf} 2>> {log}"
#
# rule featurecount_edger_unique:
#     input:  mapf = "UNIQUE_MAPPED/{file}_mapped_sorted_unique.bam",
#             countgtf = expand(rules.prepare_count_annotation.output.countgtf, ref=REFERENCE, gen=os.path.dirname(genomepath(SAMPLES[0],config)), countanno=tool_params(SAMPLES[0], None, config, 'DAS')['ANNOTATION'].replace('.gtf','_fc_edger.gtf')),
#             deugtf = expand(rules.prepare_count_annotation.output.deugtf, ref=REFERENCE, gen=os.path.dirname(genomepath(SAMPLES[0],config)), deuanno=tool_params(SAMPLES[0], None, config, 'DAS')['ANNOTATION'].replace('.gtf','_edger.gtf'))
#     output: cts  = "COUNTS/Featurecounter_edger/{file}_mapped_sorted_unique.counts"
#     log:    "LOGS/{file}/featurecount_edger_unique.log"
#     conda:  "snakes/envs/"+COUNTENV+".yaml"
#     threads: MAXTHREAD
#     params: count  = COUNTBIN,
#             cpara  = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(wildcards.file, None ,config, "DAS")['OPTIONS'][0].items()),
#             paired = lambda x: '-p' if paired == 'paired' else '',
#             bins   = BINS,
#             stranded = lambda x: '-s 1' if stranded == 'fr' else '-s 2' if stranded == 'rf' else ''
#     shell:  "{params.count} -T {threads} {params.cpara} {params.paired} {params.stranded} -a <(zcat {input.countgtf}) -o {output.cts} {input.mapf} 2> {log}"
#
# rule prepare_count_table:
#     input:   cnd = expand(rules.featurecount_dexseq_unique.output.cts, file=samplecond(SAMPLES,config))
#     output:  tbl = "DAS/Tables/EDGER/RUN_DAS_Analysis.tbl.gz",
#              anno = "DAS/Tables/EDGER/RUN_DAS_Analysis.anno.gz"
#     log:     "LOGS/DAS/prepare_count_table.log"
#     conda:   "snakes/envs/"+DASENV+".yaml"
#     threads: 1
#     params:  dereps = lambda wildcards, input: get_reps(input.cnd,config,'DAS'),
#              bins = BINS
#     shell: "{params.bins}/Analysis/DEU/build_DEU_table.py {params.dereps} --table {output.tbl} --anno {output.anno} 2> {log}"
#
# rule run_edger:
#     input:  cnt = rules.prepare_count_table.output.tbl,
#             anno = rules.prepare_count_table.output.anno,
#             flat = rules.prepare_count_annotation.output.deugtf
#     output: rules.themall.input.all,
#             rules.themall.input.tbl,
#             rules.themall.input.plot,
#             rules.themall.input.bcv,
#             rules.themall.input.qld,
#             rules.themall.input.mds
#     log:    "LOGS/DAS/run_edger.log"
#     conda:  "snakes/envs/"+DASENV+".yaml"
#     threads: int(MAXTHREAD-1) if int(MAXTHREAD-1) >= 1 else 1
#     params: bins   = str.join(os.sep,[BINS,DASBIN]),
#             outdir = outdir,
#             compare = comparison,
#     shell: "Rscript --no-environ --no-restore --no-save {params.bins} {input.anno} {input.cnt} {params.flat} {params.outdir} {params.compare} {threads} 2> {log} "


onsuccess:
    print("Workflow finished, no error")
onerror:
	print("ERROR: "+str({log}))
