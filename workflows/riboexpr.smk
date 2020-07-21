RIBOBIN, RIBOENV = env_bin_from_config3(config,'RIBO')

outdir="RiboSeq/HRIBO/"
comparison=comparable_as_string2(config,'RIBO')
compstr = [i.split(":")[0] for i in comparison.split(",")]

rule themall:
    input:
        csv=expand("{outdir}/{comparison}.csv", comparison=compstr),
        fc=expand("{outdir}/fc_{comparison}.pdf", outdir=outdir),
        r=expand("{outdir}/r_{comparison}.pdf", outdir=outdir)

rule xtail:
    input:
        cnt = rules.prepare_count_table.output.tbl,
        samples="{samples}"
        comparsions="{comparisons}"
    output:
        rules.themall.input.csv,
        rules.themall.input.fc,
        rules.themall.input.r
    conda:
        "../riboexpr.yaml"
    threads: 1
    shell:
        """
        xtail.R -c {input.comparsion} -t {input.samples} -r {input.cnt} -x {output.csv} -f {output.fc} -p {output.r}
        """
