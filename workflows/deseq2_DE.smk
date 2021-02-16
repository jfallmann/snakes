DEBIN, DEENV = env_bin_from_config3(config,'DE')
COUNTBIN, COUNTENV = ['featureCounts','countreads_de']#env_bin_from_config3(config,'COUNTING') ##PINNING subreads package to version 1.6.4 due to changes in 2.0.1 gene_id length cutoff that interfers

combi = "COMBINATION"

outdir = "DE/DESEQ2"
comparison = comparable_as_string2(config,'DE')
compstr = [i.split(":")[0] for i in comparison.split(",")]

rule themall:
    input:  session = expand("{outdir}/DE_DESEQ2_{combi}_SESSION.gz", outdir=outdir, combi=combi),
            Rmd = "REPORTS/SUMMARY/RmdSnippets/SUM_DE_DESEQ2.Rmd"

# rule featurecount_unique:
#     input:  reads = "MAPPED/{scombo}{file}_mapped_sorted_unique.bam"
#     output: tmp   = temp(expand("{outdir}/Featurecounts_DE_deseq/{{scombo}}{{file}}_tmp.counts", outdir=outdir)),
#             cts   = "DE/Featurecounts_DE/{scombo}{file}_mapped_sorted_unique.counts"
#     log:    "LOGS/{scombo}{file}/featurecounts_deseq2_unique.log"
#     conda:  "nextsnakes/envs/"+COUNTENV+".yaml"
#     threads: MAXTHREAD
#     params: countb = COUNTBIN,
#             anno = ANNOTATION,
#             cpara = lambda wildcards: ' '.join("{!s} {!s}".format(key, val) for (key, val) in tool_params(wildcards.file, None , config, "DE", DEENV)['OPTIONS'][0].items()),
#             paired   = lambda x: '-p' if paired == 'paired' else '',
#             stranded = lambda x: '-s 1' if stranded == 'fr' else '-s 2' if stranded == 'rf' else ''
#     shell:  "{params.countb} -T {threads} {params.cpara} {params.paired} {params.stranded} -a <(zcat {params.anno}) -o {output.tmp} {input.reads} 2> {log} && head -n2 {output.tmp} > {output.cts} && export LC_ALL=C; tail -n+3 {output.tmp}|sort --parallel={threads} -S 25% -T TMP -k1,1 -k2,2n -k3,3n -u >> {output.cts} && mv {output.tmp}.summary {output.cts}.summary"
#
# rule prepare_count_table:
#     input:   cnd  = expand(rules.featurecount_unique.output.cts, scombo=scombo, file=samplecond(SAMPLES, config))
#     output:  tbl  = "{outdir}/Tables/{scombo}_COUNTS.gz",
#              anno = "{outdir}/Tables/{scombo}_ANNOTATION.gz"
#     log:     "LOGS/{outdir}/{scombo}prepare_count_table.log"
#     conda:   "nextsnakes/envs/"+DEENV+".yaml"
#     threads: 1
#     params:  dereps = lambda wildcards, input: get_reps(input.cnd, config,'DE'),
#              bins = BINS,
#     shell: "{params.bins}/Analysis/build_count_table.py {params.dereps} --table {output.tbl} --anno {output.anno} --loglevel DEBUG 2> {log}"

rule run_deseq2:
    input:  cnt  = expand("{outdir}/Tables/{combi}_COUNTS.gz", outdir=outdir, combi=combi),
            anno = expand("{outdir}/Tables/{combi}_ANNOTATION.gz", outdir=outdir, combi=combi)
    # input:  cnt  = rules.prepare_count_table.output.tbl,
    #         anno = rules.prepare_count_table.output.anno,
    output: session = rules.themall.input.session,
            pca  = expand("{outdir}/Figures/DE_DESEQ2_{combi}_DataSet_figure_PCA.png", outdir=outdir, combi=combi),
            rld  = expand("{outdir}/Tables/DE_DESEQ2_{combi}_DataSet_table_rld.tsv.gz", outdir=outdir, combi=combi),
            vsd  = expand("{outdir}/Tables/DE_DESEQ2_{combi}_DataSet_table_vsd.tsv.gz", outdir=outdir, combi=combi),
            tbl  = expand("{outdir}/Tables/DE_DESEQ2_{combi}_{comparison}_table_results.tsv.gz", outdir=outdir, comparison=compstr, combi=combi),
            plot = expand("{outdir}/Figures/DE_DESEQ2_{combi}_{comparison}_figure_MA.png", outdir=outdir, comparison=compstr, combi=combi),
            vst  = expand("{outdir}/Figures/DE_DESEQ2_{combi}_DataSet_figure_VST-and-log2.png", outdir=outdir, combi=combi),
            heat = expand("{outdir}/Figures/DE_DESEQ2_{combi}_DataSet_figure_heatmap{i}.png", outdir=outdir,i=[1,2,3,"-samplebysample"], combi=combi),
            heats = expand("{outdir}/Figures/DE_DESEQ2_{combi}_DataSet_figure_heatmap-samplebysample.png", outdir=outdir,i=[1,2,3,"-samplebysample"], combi=combi)
    log:    expand("LOGS/{outdir}/run_deseq2.log",outdir=outdir)
    conda:  "nextsnakes/envs/"+DEENV+".yaml"
    threads: int(MAXTHREAD-1) if int(MAXTHREAD-1) >= 1 else 1
    params: bins   = str.join(os.sep,[BINS, DEBIN]),
            outdir = outdir,
            compare = comparison,
            combi = combi
    shell:  "Rscript --no-environ --no-restore --no-save {params.bins} {input.anno} {input.cnt} {params.outdir} {params.compare} {params.combi} {threads} 2> {log}"

rule filter_significant_deseq2:
    input:  tbl = rules.run_deseq2.output.tbl
    output: sig = expand("{outdir}/Tables/Sig_DE_DRIMSEQ2_{combi}_{comparison}_tabel_results.tsv.gz", outdir=outdir, comparison=compstr, combi=combi),
            sig_d = expand("{outdir}/Tables/SigDOWN_DE_DRIMSEQ2_{combi}_{comparison}_tabel_results.tsv.gz", outdir=outdir, comparison=compstr, combi=combi),
            sig_u = expand("{outdir}/Tables/SigUP_DE_DRIMSEQ2_{combi}_{comparison}_tabel_results.tsv.gz", outdir=outdir, comparison=compstr, combi=combi)
    log:    expand("LOGS/{outdir}/filter_deseq2.log",outdir=outdir)
    conda:  "nextsnakes/envs/"+DEENV+".yaml"
    threads: 1
    params: pv_cut = get_cutoff_as_string(config, 'DE', 'pvalue'),
            lfc_cut = get_cutoff_as_string(config, 'DE', 'lfc')
    shell: "set +o pipefail; for i in {outdir}/DE_DESEQ2*results.tsv.gz;do fn=\"${{i##*/}}\"; if [[ -s \"$i\" ]];then zcat $i| tail -n+2 |grep -v -w 'NA'|perl -F\'\\t\' -wlane 'next if (!$F[2] || !$F[6]);if ($F[6] < {params.pvcut} && ($F[2] <= -{params.lfc_cut} ||$F[2] >= {params.lfc_cut}) ){{print}}' |gzip > {outdir}/Sig_$fn && zcat $i| tail -n+2 |grep -v -w 'NA'|perl -F\'\\t\' -wlane 'next if (!$F[2] || !$F[6]);if ($F[6] < {params.pv_cut} && ($F[2] >= {params.lfc_cut}) ){{print}}' |gzip > {outdir}/SigUP_$fn && zcat $i| tail -n+2 |grep -v -w 'NA'|perl -F\'\\t\' -wlane 'next if (!$F[2] || !$F[6]);if ($F[6] < {params.pv_cut} && ($F[2] <= -{params.lfc_cut}) ){{print}}' |gzip > {outdir}/SigDOWN_$fn; else touch {outdir}/Sig_$fn {outdir}/SigUP_$fn {outdir}/SigDOWN_$fn; fi;done 2> {log}"

rule create_summary_snippet:
    input:  rules.run_deseq2.output.pca,
            rules.run_deseq2.output.rld,
            rules.run_deseq2.output.vsd,
            rules.run_deseq2.output.tbl,
            rules.run_deseq2.output.plot,
            rules.run_deseq2.output.vst,
            rules.run_deseq2.output.heat,
            rules.run_deseq2.output.heats
            # rules.filter_significant.output.sig,
            # rules.filter_significant.output.sig_d,
            # rules.filter_significant.output.sig_u,
    output: rules.themall.input.Rmd
    log:    expand("LOGS/{outdir}/create_summary_snippet.log",outdir=outdir)
    conda:  "nextsnakes/envs/"+DEENV+".yaml"
    threads: int(MAXTHREAD-1) if int(MAXTHREAD-1) >= 1 else 1
    params: bins = BINS
    shell:  "python3 {params.bins}/Analysis/RmdCreator.py --files {input} --output {output} --loglevel DEBUG 2> {log}"
