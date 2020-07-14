rule ribotishQualityRIBO:
    input:
        fp="{input}.bam",
        genome="genome.fa",
        annotation="annotation.gff",
        bamindex="maplink/RIBO/{condition}-{replicate}.bam.bai"
    output:
        reportpdf="ribotish/{output}-qual.pdf",
        reporttxt=report("ribotish/{output}-qual.txt"),
        offsetdone="maplink/RIBO/{output}.qualdone"
    params:
        offsetparameters="maplink/RIBO/{input}.bam.para.py"
    threads: 10
    log:
        "logs/{input}_ribotishquality.log"
    shell:
        "mkdir -p ribotish; ribotish quality -v -p {threads} -b {input.fp} -g {input.annotation} -o {params.reporttxt} -f {params.reportpdf} 2> {log} || true; if grep -q \"offdict = {{'m0': {{}}}}\" {params.offsetparameters}; then mv {params.offsetparameters} {params.offsetparameters}.unused; fi; touch {output.offsetdone}"


rule ribotish:
    input:
        fp= lambda wildcards: expand("maplink/RIBO/{input}.bam", zip, replicate=samples.loc[(samples["method"] == "RIBO") & (samples["condition"] == wildcards.condition), "replicate"]),
        genome="genome.fa",
        annotation="annotation.gff",
        bamindex= lambda wildcards: expand("maplink/RIBO/{input}.bam.bai", zip, replicate=samples.loc[(samples["method"] == "RIBO") & (samples["condition"] == wildcards.condition), "replicate"]),
        #offsetparameters= lambda wildcards: expand("maplink/RIBO/{input}.qualdone", zip, replicate=samples.loc[(samples["method"] == "RIBO") & (samples["condition"] == wildcards.condition), "replicate"])
    output:
        report="ribotish/{output}-newORFs.tsv_all.txt",
        filtered="ribotish/{output}-newORFs.tsv"
    params:
        fplist= lambda wildcards, input: ','.join(list(set(input.fp))),
        codons= lambda wildcards: ("" if not CODONS else (" --alt --altcodons " + CODONS)),
    conda:
        "../envs/ribotish.yaml"
    threads: 10
    log:
        "logs/{output}_ribotish.log"
    shell:
        "mkdir -p ribotish; ribotish predict -v {params.codons} -p {threads} -b {params.fplist} -g {input.annotation} -f {input.genome} -o {output.filtered} 2> {log}"
