#!/bin/bash

conda remove -y --name clip-seq --all;

conda create -y --name clip-seq python=2.7;
source activate clip-seq;

### conda rollback fixes a gcc link issue with conda (#1392) ###
CONDA_ROLLBACK_ENABLED=false conda install -y gcc;

### add this repo to path ###
export PATH=${PWD}/bin/:$PATH;
export PATH=${PWD}/cwl/:$PATH;
export PATH=${PWD}/wf:$PATH;

### R channel ###
conda install -y -c r r-essentials;

### bioconda channel ###
conda install -y -c bioconda \
samtools=1.7 \
bedtools=2.25.0 \
pysam \
pybedtools \
pybigwig \
fastqc=0.11.5 \
star=2.4.0 \
cutadapt=1.14 \
rna-seqc \
picard \
perl-statistics-basic \
perl-statistics-r \
perl-statistics-distributions \
fastq-tools=0.8 \
umi_tools \
ucsc-bedgraphtobigwig=357 \
ucsc-bedsort=357;

### anaconda channel ###
conda install -y -c anaconda \
cython \
pycrypto \
pytest \
pandas \
numpy \
zlib=1.2;

### se-CLIP specific UMI tools ###
conda install -y -c https://conda.anaconda.org/toms umi_tools;

### Install CWL and helpers ###
pip install --ignore-installed six;
pip install cwlref-runner;
pip install cwltool==1.0.20180306140409;

### required by toil source ###
pip install cwltest;
pip install galaxy-lib==17.9.3;

### use development branch of toil, latest stable has some bugs with torque resource alloc ###
# pip install toil[all];
cd ${PWD}/bin;
git clone https://github.com/byee4/toil; # frozen fork of master
cd toil;
python setup.py install;
cd ../;

# install this script for demultiplexing paired-end reads
git clone https://github.com/byee4/eclipdemux;
cd eclipdemux;
export PATH=$PATH:${PWD}/bin
# python setup.py install;
cd ..;

### Yeolab helpful packages and peak caller ###
git clone https://github.com/yeolab/gscripts;
cd gscripts;
python setup.py install;
cd ..;

git clone https://github.com/YeoLab/clipper;
cd clipper;
python setup.py install;
cd ..;

git clone https://github.com/YeoLab/makebigwigfiles;
cd makebigwigfiles;
export PATH=$PATH:${PWD}/makebigwigfiles
python setup.py install;
cd ..;

### softlink the following to env conda lib ###
# ln -s /lib64/libtinfo.so.5 libtinfow.so.5 # fixes issue with samtools
# ln -s libstdc++.so.6.0.24 libstdc++.so.6  # fixes issue with node/scipy???
