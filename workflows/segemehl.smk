MAPPERBIN, MAPPERENV = env_bin_from_config2(SAMPLES,config,'MAPPING')

rule generate_index:
    input:  fa = expand("{ref}/{{dir}}/{{gen}}{{name}}.fa.gz", ref=REFERENCE)
    output: idx = expand("{ref}/{{dir}}/{map}/{{src}}/{{gen}}{{name}}_{map}.idx", ref=REFERENCE, map=MAPPERBIN)
    log:    expand("LOGS/{{src}}/{{dir}}/{{gen}}{{name}}_{map}.idx.log", map=MAPPERBIN)
    conda:  "snakes/envs/"+MAPPERENV+".yaml"
    threads: MAXTHREAD
    params:  indexer = MAPPERBIN,
            ipara = lambda wildcards, input: ' '.join("{!s} {!s}".format(key,val) for (key,val) in index_params(str.join(os.sep,[wildcards.dir,wildcards.src]), config, 'MAPPING')['OPTIONS'][0].items())
    shell: "{params.indexer} --threads {threads} {params.ipara} -d {input.fa} -x {output.idx} 2> {log}"

if paired == 'paired':
	rule mapping:
	    input:  r1 = "TRIMMED_FASTQ/{file}_r1_trimmed.fastq.gz",
	            r2 = "TRIMMED_FASTQ/{file}_r2_trimmed.fastq.gz",
	            index = lambda wildcards: expand(rules.generate_index.output.idx, ref=REFERENCE, dir=source_from_sample(wildcards.file).split(os.sep)[0], src=str.join(os.sep, source_from_sample(wildcards.file).split(os.sep)[1:]), gen =genome(wildcards.file, config), name=namefromfile(wildcards.file, config), map=MAPPERBIN),
	            ref = lambda wildcards: expand(rules.generate_index.input.fa, ref=REFERENCE, dir = source_from_sample(wildcards.file).split(os.sep)[0], gen =genome(wildcards.file, config), name=namefromfile(wildcards.file, config))
	    output: mapped = report("MAPPED/{file}_mapped.sam", category="MAPPING"),
	            unmapped = "UNMAPPED/{file}_unmapped.fastq.gz",
	    log:    "LOGS/{file}/mapping.log"
	    conda:  "snakes/envs/"+MAPPERENV+".yaml"
	    threads: MAXTHREAD
	    params: mpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(wildcards.file, None ,config, 'MAPPING')['OPTIONS'][1].items()),
	            mapp=MAPPERBIN
	    shell: "{params.mapp} {params.mpara} -d {input.ref} -i {input.index} -q {input.r1} -p {input.r2} --threads {threads} -o {output.mapped} -u {output.unmapped} 2> {log}"

else:
	rule mapping:
	    input:  query = "TRIMMED_FASTQ/{file}_trimmed.fastq.gz",
	            index = lambda wildcards: expand(rules.generate_index.output.idx, ref=REFERENCE, dir=source_from_sample(wildcards.file).split(os.sep)[0], src=str.join(os.sep, source_from_sample(wildcards.file).split(os.sep)[1:]), gen =genome(wildcards.file, config), name=namefromfile(wildcards.file, config), map=MAPPERBIN),
	            ref = lambda wildcards: expand(rules.generate_index.input.fa, ref=REFERENCE, dir = source_from_sample(wildcards.file).split(os.sep)[0], gen =genome(wildcards.file, config), name=namefromfile(wildcards.file, config))
	    output: mapped = report("MAPPED/{file}_mapped.sam", category="MAPPING"),
	            unmapped = "UNMAPPED/{file}_unmapped.fastq.gz",
	    log:    "LOGS/{file}/mapping.log"
	    conda:  "snakes/envs/"+MAPPERENV+".yaml"
	    threads: MAXTHREAD
	    params:  mpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(wildcards.file, None ,config, 'MAPPING')['OPTIONS'][1].items()),
	            mapp=MAPPERBIN
	    shell: "{params.mapp} {params.mpara} -d {input.ref} -i {input.index} -q {input.query} --threads {threads} -o {output.mapped} -u {output.unmapped} 2> {log}"
