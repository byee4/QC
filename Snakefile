SAMPLES = ["4226_CLIP1_downsampled", "4226_CLIP2_downsampled"]
DB = "/projects/ps-yeolab3/bay001/annotations/nr/nt"

rule all:
    input:
        expand("{sample}.blast_results.tsv", sample=SAMPLES)


rule fastq_to_fasta:
    input:
        fastq="inputs/{sample}.fastq"
    output:
        fasta="inputs/{sample}.fasta"
    conda:
        "envs/ucsctools.yaml"
    shell:
        "fastqToFa {input.fastq} {output.fasta}"
        
        
rule blast:
    input:
        fasta="inputs/{sample}.fasta",
    output:
        blast_output="{sample}.blast_results.tsv"
    params:
        num_threads=8
    conda:
        "envs/blast.yaml"
    shell:
        """
        blastn -db {DB} -query {input.fasta} -out {output.blast_output} -outfmt 6 -max_target_seqs 5 -num_threads {params.num_threads};
        """