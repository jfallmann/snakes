RIBOBIN, RIBOENV = env_bin_from_config3(config,'RIBO')

outdir="RiboSeq/HRIBO/"
comparison=comparable_as_string2(config,'RIBO')
compstr = [i.split(":")[0] for i in comparison.split(",")]

rule themall:
    input:  expand("{outdir}ribotish/{file}-qual.pdf, file=samplecond(SAMPLES,config)),
            expand("{outdir}ribotish/{file}-qual.txt", file=samplecond(SAMPLES,config))

rule ribotishQualityRIBO:
    input:
        fp = "UNIQUE_MAPPED/{file}_mapped_sorted_unique.bam",
        fpi = "UNIQUE_MAPPED/{file}_mapped_sorted_unique.bam.bai"
    output:
        reportpdf="{outdir}ribotish/{file}-qual.pdf",
        reporttxt=report("{outdir}ribotish/{file}-qual.txt"),
    log:    "LOGS/{file}_ribotishquality.log"
    conda:  "nextsnakes/envs/"+RIBOENV+".yaml"
    threads: 10
    params:
        offsetparameters="maplink/RIBO/{input}.bam.para.py", #was tut des? Kann ma des so machen wie drunter?
        offsetparameters=lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(wildcards.file, None ,config, "RIBO")['OPTIONS'][0].items())+' -t '+wildcards.feat+' -g '+config['RIBO']['FEATURES'][wildcards.feat],
        anno  = lambda wildcards: str.join(os.sep,[config["REFERENCE"],os.path.dirname(genomepath(wildcards.file, config)),tool_params(wildcards.file, None, config, 'RIBO')['ANNOTATION']])
    shell:
        "mkdir -p ribotish; ribotish quality -v -p {threads} -b {input.fp} -g {params.anno} -o {params.reporttxt} -f {params.reportpdf} 2> {log} || true; if grep -q \"offdict = {{'m0': {{}}}}\" {params.offsetparameters}; then mv {params.offsetparameters} {params.offsetparameters}.unused; fi; touch {output.offsetdone}" #output.offsetdone seh i da gar net

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
