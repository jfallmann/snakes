DEUBIN, DEUENV = env_bin_from_config3(config,'DEU')
COUNTBIN, COUNTENV = ['featureCounts','countreads_de']#env_bin_from_config3(config,'COUNTING') ##PINNING subreads package to version 1.6.4 due to changes in 2.0.1 gene_id length cutoff that interfers

comparison = comparable_as_string2(config,'DEU')
compstr = [i.split(":")[0] for i in comparison.split(",")]

rule themall:
    input:  session = expand("DEU/{combo}/DEU_DEXSEQ_{scombo}_SESSION.gz", combo=combo, scombo=scombo),
            html    = expand("DEU/{combo}/DEXSeqReport_{scombo}_{comparison}/DEXSeq_{scombo}_{comparison}.html", combo=combo, scombo=scombo, comparison=compstr),
            plot    = expand("DEU/{combo}/Figures/DEU_DEXSEQ_{scombo}_{comparison}_figure_DispEsts.png", combo=combo, scombo=scombo, comparison=compstr),
            plotMA  = expand("DEU/{combo}/Figures/DEU_DEXSEQ_{scombo}_{comparison}_figure_plotMA.png", combo=combo, scombo=scombo, comparison=compstr),
            siglist = expand("DEU/{combo}/Figures/DEU_DEXSEQ_{scombo}_{comparison}_list_sigGroupsFigures.png", combo=combo, scombo=scombo, comparison=compstr),
            tbl     = expand("DEU/{combo}/Tables/DEU_DEXSEQ_{scombo}_{comparison}_table_results.tsv.gz", combo=combo, scombo=scombo, comparison=compstr),
            sig     = expand("DEU/{combo}/Tables/Sig_DEU_DEXSEQ_{scombo}_{comparison}_tabel_results.tsv.gz", combo=combo, comparison=compstr, scombo=scombo),
            sig_d   = expand("DEU/{combo}/Tables/SigDOWN_DEU_DEXSEQ_{scombo}_{comparison}_tabel_results.tsv.gz", combo=combo, comparison=compstr, scombo=scombo),
            sig_u   = expand("DEU/{combo}/Tables/SigUP_DEU_DEXSEQ_{scombo}_{comparison}_tabel_results.tsv.gz", combo=combo, comparison=compstr, scombo=scombo),
            Rmd     = expand("REPORTS/SUMMARY/RmdSnippets/SUM_DEU_{scombo}_DEXSEQ.Rmd", scombo=scombo)

rule prepare_deu_annotation:
    input:  anno = ANNOTATION
    output: countgtf = expand("{countanno}",         countanno=ANNOTATION.replace('.gtf','_fc_dexseq.gtf')),
            deugtf   = expand("{deuanno}", deuanno=ANNOTATION.replace('.gtf','_dexseq.gtf'))
    log:    expand("LOGS/DEU/{combo}/featurecount_dexseq_annotation.log", combo=combo)
    conda:  "nextsnakes/envs/"+COUNTENV+".yaml"
    threads: MAXTHREAD
    params: bins = BINS,
            countstrand = lambda x: '-s' if stranded == 'fr' or stranded == 'rf' else ''
    shell:  "{params.bins}/Analysis/DEU/prepare_deu_annotation2.py -f {output.countgtf} {params.countstrand} {input.anno} {output.deugtf} 2>> {log}"

rule featurecount_unique:
    input:  reads = expand("MAPPED/{scombo}/{{file}}_mapped_sorted_unique.bam", scombo=scombo),
            countgtf = expand(rules.prepare_deu_annotation.output.countgtf, countanno=ANNOTATION.replace('.gtf','_fc_dexseq.gtf')),
            deugtf = expand(rules.prepare_deu_annotation.output.deugtf, deuanno=ANNOTATION.replace('.gtf','_dexseq.gtf'))
    output: tmp   = temp("DEU/{combo}/Featurecounts_DEU_dexseq/{file}_tmp.counts"),
            cts   = "DEU/Featurecounts_DEU_dexseq_{combo}/{file}_mapped_sorted_unique.counts"
    log:    "LOGS/DEU/{combo}/{file}_featurecounts_dexseq_unique.log"
    conda:  "nextsnakes/envs/"+COUNTENV+".yaml"
    threads: MAXTHREAD
    params: countb  = COUNTBIN,
            cpara  = lambda wildcards: ' '.join("{!s} {!s}".format(key, val) for (key, val) in tool_params(wildcards.file, None , config, "DEU", DEUENV.split("_")[0])['OPTIONS'][0].items()),
            paired = lambda x: '-p' if paired == 'paired' else '',
            bins   = BINS,
            stranded = lambda x: '-s 1' if stranded == 'fr' else '-s 2' if stranded == 'rf' else ''
    shell:  "{params.countb} -T {threads} {params.cpara} {params.paired} {params.stranded} -a <(zcat {input.countgtf}) -o {output.tmp} {input.reads} 2> {log} && head -n2 {output.tmp} > {output.cts} && export LC_ALL=C; tail -n+3 {output.tmp}|sort --parallel={threads} -S 25% -T TMP -k2,2 -k3,3n -k4,4n -k1,1 -u >> {output.cts} && mv {output.tmp}.summary {output.cts}.summary"

rule prepare_count_table:
    input:   cnd  = expand(rules.featurecount_unique.output.cts, combo=combo, file=samplecond(SAMPLES, config))
    output:  tbl  = "DEU/{combo}/Tables/{scombo}_COUNTS.gz",
             anno = "DEU/{combo}/Tables/{scombo}_ANNOTATION.gz"
    log:     "LOGS/DEU/{combo}/{scombo}_prepare_count_table.log"
    conda:   "nextsnakes/envs/"+DEUENV+".yaml"
    threads: 1
    params:  dereps = lambda wildcards, input: get_reps(input.cnd, config, 'DE'),
             bins = BINS
    shell: "{params.bins}/Analysis/build_count_table.py {params.dereps} --table {output.tbl} --anno {output.anno} --loglevel DEBUG 2> {log}"

rule run_dexseq:
    input:  cnt  = expand(rules.prepare_count_table.output.tbl, combo=combo, scombo=scombo),
            anno = expand(rules.prepare_count_table.output.anno, combo=combo, scombo=scombo),
            flat = rules.prepare_deu_annotation.output.deugtf
    output: html    = rules.themall.input.html,
            plot    = rules.themall.input.plot,
            plotMA  = rules.themall.input.plotMA,
            siglist = rules.themall.input.siglist,
            tbl     = rules.themall.input.tbl,
            session = rules.themall.input.session
    log:    expand("LOGS/DE/{combo}_{scombo}_{comparison}/run_dexseq.log", combo=combo, comparison=compstr, scombo=scombo)
    conda:  "nextsnakes/envs/"+DEUENV+".yaml"
    threads: int(MAXTHREAD-1) if int(MAXTHREAD-1) >= 1 else 1
    params: bins   = str.join(os.sep,[BINS, DEUBIN]),
            outdir = 'DEU/'+combo,
            compare = comparison,
            scombo = scombo,
            ref = ANNOTATION
    shell:  "Rscript --no-environ --no-restore --no-save {params.bins} {input.anno} {input.cnt} {params.ref} {input.flat} {params.outdir} {params.scombo} {params.compare} {threads} 2> {log}"

rule filter_significant:
    input:  tbl = rules.run_dexseq.output.tbl
    output: sig = rules.themall.input.sig,
            sig_d = rules.themall.input.sig_d,
            sig_u = rules.themall.input.sig_u
    log:    expand("LOGS/DE/{combo}_{scombo}_{comparison}/filter_dexseq.log", combo=combo, comparison=compstr, scombo=scombo)
    conda:  "nextsnakes/envs/"+DEUENV+".yaml"
    threads: 1
    params: pv_cut = get_cutoff_as_string(config, 'DEU', 'pval'),
            lfc_cut = get_cutoff_as_string(config, 'DEU', 'lfc')
    shell: "set +o pipefail; for i in DEU/{combo}/DEU_DEXSEQ_*results.tsv.gz;do fn=\"${{i##*/}}\"; if [[ -s \"$i\" ]];then zcat $i| tail -n+2 |grep -v -w 'NA'|perl -F\'\\t\' -wlane 'next if (!$F[6] || !$F[9]);if ($F[6] < {params.pv_cut} && ($F[9] <= -{params.lfc_cut} ||$F[9] >= {params.lfc_cut}) ){{print}}' |gzip > DEU/{combo}/Sig_$fn && zcat $i| tail -n+2 |grep -v -w 'NA'|perl -F\'\\t\' -wlane 'next if (!$F[6] || !$F[9]);if ($F[6] < {params.pv_cut} && ($F[9] >= {params.lfc_cut}) ){{print}}' |gzip > DEU/{combo}/SigUP_$fn && zcat $i| tail -n+2 |grep -v -w 'NA'|perl -F\'\\t\' -wlane 'next if (!$F[6] || !$F[9]);if ($F[6] < {params.pv_cut} && ($F[9] <= -{params.lfc_cut}) ){{print}}' |gzip > DEU/{combo}/SigDOWN_$fn;else touch DEU/{combo}/Sig_$fn DEU/{combo}/SigUP_$fn DEU/{combo}/SigDOWN_$fn; fi;done 2> {log}"

rule create_summary_snippet:
    input:  rules.run_dexseq.output.plot,
            rules.run_dexseq.output.tbl,
            rules.run_dexseq.output.siglist,
            rules.run_dexseq.output.plotMA,
            rules.filter_significant.output.sig,
            rules.filter_significant.output.sig_d,
            rules.filter_significant.output.sig_u
    output: rules.themall.input.Rmd
    log:    expand("LOGS/DEU/{combo}/create_summary_snippet.log" ,combo=combo)
    conda:  "nextsnakes/envs/"+DEUENV+".yaml"
    threads: int(MAXTHREAD-1) if int(MAXTHREAD-1) >= 1 else 1
    params: bins = BINS
    shell:  "python3 {params.bins}/Analysis/RmdCreator.py --files {input} --output {output} --loglevel DEBUG 2> {log}"
