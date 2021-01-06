MAPPERBIN, MAPPERENV = env_bin_from_config3(config,'MAPPING')

rule generate_index:
    input:  fa = REFERENCE
    output: idx = INDEX,
            uidx = expand("{refd}/INDICES/{mape}/{unikey}.idx", refd=REFDIR, mape=MAPPERENV, unikey=get_dict_hash(tool_params(SAMPLES[0], None, config, 'MAPPING', MAPPERENV)['OPTIONS'][0]))
    log:    expand("LOGS/{sets}/{mape}.idx.log", sets=SETS, mape=MAPPERENV)
    conda:  "nextsnakes/envs/"+MAPPERENV+".yaml"
    threads: MAXTHREAD
    params: indexer=MAPPERBIN,
            ipara = lambda wildcards, input: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(SAMPLES[0], None, config, 'MAPPING', MAPPERENV)['OPTIONS'][0].items()),
            linkidx = lambda wildcards, output: str(os.path.abspath(output.uidx[0]))
    shell: "{params.indexer} -t {threads} -d {output.uidx} {params.ipara} {input.fa} 2> {log} && ln -s {params.linkidx} {output.idx}"

if paired == 'paired':
    rule mapping:
        input:  q1 = "TRIMMED_FASTQ/{combo}{file}_R1_trimmed.fastq.gz",
                q2 = "TRIMMED_FASTQ/{combo}{file}_R2_trimmed.fastq.gz",
                index = rules.generate_index.output.idx
        output: mapped = temp(report("MAPPED/{combo}{file}_mapped.sam", category="MAPPING")),
                unmapped = "UNMAPPED/{combo}{file}_unmapped.fastq.gz"
        log:    "LOGS/{combo}{file}/mapping.log"
        conda:  "nextsnakes/envs/"+MAPPERENV+".yaml"
        threads: MAXTHREAD
        params: mpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(wildcards.file, None, config, 'MAPPING', MAPPERENV)['OPTIONS'][1].items()),
                mapp=MAPPERBIN
        shell: "{params.mapp} -t {threads} {params.mpara} {input.index} {input.q1} {input.q2}| tee >(samtools view -h -F 4 > {output.mapped}) >(samtools view -h -f 4 |samtools fastq -n - | pigz > {output.unmapped}) 1>/dev/null 2>> {log} && touch {output.unmapped}"

else:
    rule mapping:
        input:  query = "TRIMMED_FASTQ/{combo}{file}_trimmed.fastq.gz",
                index = rules.generate_index.output.idx
        output: mapped = temp(report("MAPPED/{combo}{file}_mapped.sam", category="MAPPING")),
                unmapped = "UNMAPPED/{combo}{file}_unmapped.fastq.gz"
        log:    "LOGS/{combo}{file}/mapping.log"
        conda:  "nextsnakes/envs/"+MAPPERENV+".yaml"
        threads: MAXTHREAD
        params: mpara = lambda wildcards: ' '.join("{!s} {!s}".format(key,val) for (key,val) in tool_params(wildcards.file, None, config, 'MAPPING', MAPPERENV)['OPTIONS'][1].items()),
                mapp=MAPPERBIN
        shell: "{params.mapp} -t {threads} {params.mpara} {input.index} {input.query} | tee >(samtools view -h -F 4 > {output.mapped}) >(samtools view -h -f 4 |samtools fastq -n - | pigz > {output.unmapped}) 1>/dev/null 2>> {log} && touch {output.unmapped}"
