include: "header.smk"

rule all:
    input:  expand("COUNTS/{file}/Counts",file=samplecond(SAMPLES,config)),
            expand("COUNTS/{rawfile}/Counts",rawfile=SAMPLES),
            "COUNTS/DONE"

if config['MAPPING'] is 'paired':
    rule count_fastq:
        input:  "FASTQ/{rawfile}_r1.fastq.gz",
                "FASTQ/{rawfile}_r2.fastq.gz",
                "TRIMMED_FASTQ/{rawfile}_r1_trimmed.fastq.gz",
                "TRIMMED_FASTQ/{rawfile}_r2_trimmed.fastq.gz"
        output: "COUNTS/{file}_raw_r1_fq.count",
                "COUNTS/{file}_raw_r2_fq.count",
                "COUNTS/{file}_trimmed_r1_fq.count",
                "COUNTS/{file}_trimmed_r2_fq.count"
        conda:  "snakes/envs/base.yaml"
        threads: 1
        shell:  "arr=({input}); alen=${{#arr[@]}}; orr=({output}); for i in \"${{!arr[@]}}\";do a=$(zcat ${{arr[$i]}}|wc -l ); echo $((a/4)) > ${{orr[$i]}};done"

    else:
        rule count_fastq:
            input:  "FASTQ/{rawfile}.fastq.gz",
                    "TRIMMED_FASTQ/{rawfile}_trimmed.fastq.gz",
                    "FILTERED/{file}_filtered.fastq.gz"
            output: "COUNTS/{file}_raw_fq.count",
                    "COUNTS/{file}_trimmed_fq.count",
                    "COUNTS/{file}_filtered_fq.count"
            conda:  "snakes/envs/base.yaml"
            threads: 1
            shell:  "arr=({input}); alen=${{#arr[@]}}; orr=({output}); for i in \"${{!arr[@]}}\";do a=$(zcat ${{arr[$i]}}|wc -l ); echo $((a/4)) > ${{orr[$i]}};done"

rule count_mappers:
    input:  "SORTED_MAPPED/{file}_mapped_sorted.bam",
            "UNIQUE_MAPPED/{file}_mapped_sorted_unique.bam"
    output: "COUNTS/{file}_mapped.count",
            "COUNTS/{file}_mapped_unique.count"
    conda:  "snakes/envs/samtools.yaml"
    threads: MAXTHREAD
    shell:  "export LC_ALL=C; arr=({input}); alen=${{#arr[@]}}; orr=({output}); for i in \"${{!arr[@]}}\";do samtools view -F 260 ${{arr[$i]}} | cut -d$'\t' -f1|sort --parallel={threads} -S 25% -T SORTTMP -u |wc -l > ${{orr[$i]}};done"

rule summarize_counts:
    input:  "COUNTS/{file}_mapped.count",
            "COUNTS/{file}_mapped_unique.count",
            "COUNTS/{file}_mapped_phased.count",
            "COUNTS/{rawfile}_raw_fq.count"),
            "COUNTS/{rawfile}_trimmed_fq.count")
    output: "COUNTS/{file}/Counts",
            "COUNTS/{rawfile}/Counts"
    conda:  "snakes/envs/base.yaml"
    threads: 1
    params: current = lambda w,input: w.input
    shell:  "arr=({input}); alen=${{#arr[@]}}; for i in \"${{!arr[@]}}\";do echo -ne \"${{arr[$i]}}\t\" >> COUNTS/{params.current}/Counts && if [[ -s ${{arr[$i]}} ]]; then cat ${{arr[$i]}} >> COUNTS/{params.current}/Counts; else echo '0' >> COUNTS/{params.current}/Counts;fi;done"

rule themall:
    input:  rules.summarize_counts.output
    output: "COUNTS/DONE"
    conda:  "snakes/envs/base.yaml"
    threads: 1
    params: bins = BINS
    shell:  "touch {output}"
