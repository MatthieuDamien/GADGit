```sh
#!/bin/bash

### GAD PIPELINE ###
## gs_solo_nbs.sh
## Description : process analysis for genome data : from fastq to annotated vcf
## Usage : 
## Output : no standard output .
## Requirements : Require all pipeline scripts

## Author : yannis.duffourd@u-bourgogne.fr ; emilie.tisserant@u-bourgogne.fr ; anthony.auclair@u-bourgogne.fr ; valentin.vautrot@u-bourgogne.fr
## Creation Date : 20240219
## Last revision date : 20250506
## Known bugs : None.

#SBATCH --qos=qos_neomics
#SBATCH -n 1 
#SBATCH -p nompi 
#SBATCH --mem=4G
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=gad-astreinte-bioinfo@u-bourgogne.fr


# usefull function
function sqn {
    code=$(squeue -o "%A %j" | grep -v "JOBID" | grep -w $1 | cut -f 1 -d " ")
    if [ "${code}" == "" ]
    then 
        echo 1
    else 
        echo ${code}
    fi
}


# logging parameters.
# log file
logbasename=$(date +"%F_%H-%M-%S")
vcfbasename=$(date +"%F")
if [ -z ${LOGFILE} ]
then
    LOGFILE=gs_solo_nbs.$(date +"%F_%H-%M-%S").log
fi
exec 1>> $LOGFILE 2>&1

# mandatory arguments
if [ -z ${ANALYSISDIR} ]
then
    echo "ANALYSISDIR was not defined : execution stopped"
    exit 1
fi

# Check MODE option
if [ -z ${MODE} ]
then
    MODE="TEST"
fi

# Verify the config file has been passed. Otherwise : stop the script.
if [ -z ${CONFIGFILE+x} ]
then
    echo "Config file not provided by the user. You need it to run this script. Stopping execution."
    exit
fi

# usefull variables
TEMPORARY_DIR=`grep temporary_dir ${CONFIGFILE} | cut -f2`
DBSNP=`grep dbsnp ${CONFIGFILE} | cut -f2`
REF=`grep reference ${CONFIGFILE} | cut -f2`
REFDIR=`grep refdir ${CONFIGFILE} | cut -f2`
GATKBASE=`grep GATKbase ${CONFIGFILE} | cut -f2`
JAVACMD=`grep javacmd ${CONFIGFILE} | cut -f2`
PYTHONBIN=`grep pythonbin ${CONFIGFILE} | cut -f2`
PIPELINEBASE=`grep pipelinebase ${CONFIGFILE} | cut -f2`
TARGETPATH=`grep targetlist ${CONFIGFILE} | cut -f2`
REFSEQLIST=`grep refseqlist ${CONFIGFILE} | cut -f2`
REFSEQGENELIST=`grep refseqgenelist ${CONFIGFILE} | cut -f2`
CNVCONTROLDIR=`grep cnvcontroldir ${CONFIGFILE} | cut -f2`
CNVCALLERCONTROLDIR=`grep cnvcallercontroldir ${CONFIGFILE} | cut -f2`
CHUNKMAP=`grep chunk_map_grch38 ${CONFIGFILE} | cut -f2`
REPDIR=$(basename ${ANALYSISDIR})
SNPLIST=`grep identitoSNPlist ${CONFIGFILE} | cut -f2`
NBSLISTA=$(grep NBSlistA ${CONFIGFILE} | cut -f2)
NBSLISTB=$(grep NBSlistB ${CONFIGFILE} | cut -f2)
PGC1INCLUDE=`grep PGC1include ${CONFIGFILE} | cut -f2`
PGC1EXCLUDE=`grep PGC1exclude ${CONFIGFILE} | cut -f2`
IDENTITOSNPVCF=`grep identitoSNPvcf ${CONFIGFILE} | cut -f2`
SNPLIST=`grep identitoSNPlist ${CONFIGFILE} | cut -f2`
TABIXBIN=`grep tabixpath ${CONFIGFILE} | cut -f2`

# sample list
samples=$(find ${ANALYSISDIR} -maxdepth 1 -mindepth 1 -type d -exec basename {} \; | grep -vw "logs")



# copy PGC1 interval_list and transmission files
echo "### copy PGC1 files ###"
echo "Start : $(date)"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -p nompi -n 1 \
    -J copy_pgc1_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.info,ANALYSISDIR=${ANALYSISDIR}/${currentSample}/,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/copy_pgc1.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/copy_pgc1.sh"
    
    sbatch -p nompi -n 1 \
    -J copy_pgc1_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.info,ANALYSISDIR=${ANALYSISDIR}/${currentSample}/,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/copy_pgc1.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/copy_pgc1.sh
done
echo "End : $(date)"

# run fastq md5sum
echo "### fastq files md5sum ###"
echo "Start : $(date)"
for currentSample in ${samples}
do
    echo "Command :
    sbatch -p nompi -n 1 \
    -J run_md5_fastq_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILEONE=${ANALYSISDIR}/${currentSample}/${currentSample}.R1.fastq.gz,INPUTFILETWO=${ANALYSISDIR}/${currentSample}/${currentSample}.R2.fastq.gz,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.md5,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/run_md5_fastq.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/fastq/run_md5_fastq.sh"
    
    sbatch -p nompi -n 1 \
    -J run_md5_fastq_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILEONE=${ANALYSISDIR}/${currentSample}/${currentSample}.R1.fastq.gz,INPUTFILETWO=${ANALYSISDIR}/${currentSample}/${currentSample}.R2.fastq.gz,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.md5,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/run_md5_fastq.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/fastq/run_md5_fastq.sh
done
echo "End : $(date)"

# first pass fastqc
echo "### First pass fastqc ###"
echo "Start : $(date)"
for currentSample in ${samples}
do
    echo "FP fastqc for sample : ${currentSample}"
    echo "Command : 
    sbatch -n 48 \
    -J fastqc_FP_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=SAMPLE=${currentSample},ANALYSISDIR=${ANALYSISDIR},OUTDIR=${ANALYSISDIR}/${currentSample}/QC,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/process_fastqc.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/fastq/process_fastqc_slurm.sh"
    
    sbatch -n 48 \
    -J fastqc_FP_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=SAMPLE=${currentSample},ANALYSISDIR=${ANALYSISDIR},OUTDIR=${ANALYSISDIR}/${currentSample}/QC,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/process_fastqc.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/fastq/process_fastqc_slurm.sh
done
echo "End : $(date)"

# fq2vcf gpu pipeline
echo "### Computing fq2vcf on gpu ###"
echo "Start : $(date)"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch --gres=gpu:2 --ntasks=48 --partition=gpu \
    -J fq2vcf_gpu_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=SAMPLE=${currentSample},ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/fq2vcf.$(date +"%F_%H-%M-%S").log,PIPELINEBASE=${PIPELINEBASE} ${PIPELINEBASE}/common/fastq/fq2vcf_gpu.sh" 
    
    sbatch --gres=gpu:2 --ntasks=48 --partition=gpu \
    -J fq2vcf_gpu_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=SAMPLE=${currentSample},ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/fq2vcf.$(date +"%F_%H-%M-%S").log,PIPELINEBASE=${PIPELINEBASE} ${PIPELINEBASE}/common/fastq/fq2vcf_gpu.sh
done
echo "End : $(date)"

# bam to cram
echo "### Converting bam into cram for archiving  ###"
echo "Start : $(date)"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -n 48 -p mpi2 \
    -J bam_to_cram_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.cram,REF=${REF},CONFIGFILE=${CONFIGFILE},CLUSTER=slurm,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/bam_to_cram.$(date +"%F_%H-%M-%S").log \
    ${PIPELINEBASE}/common/bam/bam_to_cram.sh"
    
    sbatch -n 48 -p mpi2 \
    -J bam_to_cram_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.cram,REF=${REF},CONFIGFILE=${CONFIGFILE},CLUSTER=slurm,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/bam_to_cram.$(date +"%F_%H-%M-%S").log \
    ${PIPELINEBASE}/common/bam/bam_to_cram.sh
done
echo "End : $(date)"

# SMN detection
echo "### SMN Detection ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command :     
    sbatch -n 48 \
    -J SMN_caller_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=SAMPLE=${currentSample},ANALYSISDIR=${ANALYSISDIR},INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/SMN_caller.$(date +"%F_%H-%M-%S").log,PIPELINEBASE=${PIPELINEBASE} ${PIPELINEBASE}/common/bam/SMN_caller.sh"
    
    sbatch -n 48 \
    -J SMN_caller_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=SAMPLE=${currentSample},ANALYSISDIR=${ANALYSISDIR},INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/SMN_caller.$(date +"%F_%H-%M-%S").log,PIPELINEBASE=${PIPELINEBASE} ${PIPELINEBASE}/common/bam/SMN_caller.sh
done
echo "End : $(date +"%F_%H-%M-%S")"



# Variant filtering step
echo "### Variant filtering ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -n 1 \
    --partition nompi  \
    -J filter_varcall_nbs_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=SAMPLE=${currentSample},INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.interval_filtered.vcf,NBSLIST=${ANALYSISDIR}/${currentSample}/PGC1.interval_list,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/filter_varcall_nbs.${currentSample}.$(date +"%F_%H-%M-%S").log,ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE},currentSample=${currentSample} \
    ${PIPELINEBASE}/common/vcf/filter_varcall_nbs.sh"
    
    sbatch -n 1 \
    --partition nompi  \
    -J filter_varcall_nbs_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=SAMPLE=${currentSample},INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.interval_filtered.vcf,NBSLIST=${ANALYSISDIR}/${currentSample}/PGC1.interval_list,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/filter_varcall_nbs.${currentSample}.$(date +"%F_%H-%M-%S").log,ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE},currentSample=${currentSample} \
    ${PIPELINEBASE}/common/vcf/filter_varcall_nbs.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

# Variant Snpeff annotation step
echo "### Variant Snpeff annotation ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -n 1 -p nompi \
    -J annotate_variants_snpeff_wgs_${currentSample} \
    --dependency=afterok:$(sqn filter_varcall_nbs_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.interval_filtered.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.snpeff.vcf,LOGFILENEW=${ANALYSISDIR}/${currentSample}/logs/annotate_variants_snpeff.${currentSample}.$(date +"%F_%H-%M-%S").log,ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/annotate_variants_snpeff_wgs.sh"
    
    sbatch -n 1 -p nompi \
    -J annotate_variants_snpeff_wgs_${currentSample} \
    --dependency=afterok:$(sqn filter_varcall_nbs_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.interval_filtered.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.snpeff.vcf,LOGFILENEW=${ANALYSISDIR}/${currentSample}/logs/annotate_variants_snpeff.${currentSample}.$(date +"%F_%H-%M-%S").log,ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/annotate_variants_snpeff_wgs.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

# Variant Spip annotation step #######
echo "### Variant Spip annotation ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -p mpi2 -n 48 \
    -J annotate_variants_spip_${currentSample} \
    --dependency=afterok:$(sqn annotate_variants_snpeff_wgs_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.snpeff.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.spip.vcf,LOGFILENEW=${ANALYSISDIR}/${currentSample}/logs/annotate_variants_spip.${currentSample}.$(date +"%F_%H-%M-%S").log,CLUSTER=slurm,ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE},casindex_sample=${currentSample} \
    ${PIPELINEBASE}/common/vcf/wrapper_annotate_spip.sh"

    sbatch -p mpi2 -n 48 \
    -J annotate_variants_spip_${currentSample} \
    --dependency=afterok:$(sqn annotate_variants_snpeff_wgs_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.snpeff.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.spip.vcf,LOGFILENEW=${ANALYSISDIR}/${currentSample}/logs/annotate_variants_spip.${currentSample}.$(date +"%F_%H-%M-%S").log,CLUSTER=slurm,ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE},casindex_sample=${currentSample} \
    ${PIPELINEBASE}/common/vcf/wrapper_annotate_spip.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

# Variant annotation step
echo "### Variant annotation ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command: sbatch -p nompi -n 1 \
    -J annotate_variants_${currentSample} \
    --dependency=afterok:$(sqn annotate_variants_spip_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.spip.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.annotate_variants.vcf,LOGFILENEW=${ANALYSISDIR}/${currentSample}/logs/annotate_variants.${currentSample}.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE},ANALYSISDIR=${ANALYSISDIR},casindex_sample=${currentSample} \
    ${PIPELINEBASE}/common/vcf/wrapper_annotate_variants_wgs.sh"

    sbatch -p nompi -n 1 \
    -J annotate_variants_${currentSample} \
    --dependency=afterok:$(sqn annotate_variants_spip_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.spip.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.annotate_variants.vcf,LOGFILENEW=${ANALYSISDIR}/${currentSample}/logs/annotate_variants.${currentSample}.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE},ANALYSISDIR=${ANALYSISDIR},casindex_sample=${currentSample} \
    ${PIPELINEBASE}/common/vcf/wrapper_annotate_variants_wgs.sh
done
echo "End : $(date +"%F_%H-%M-%S")"    


######################### CNV analysis ########################

echo "### ControlFreeC step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -n 48 \
    -J process_controlfreec_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/process_controlfreec.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/intervals/process_controlfreec.sh"

    sbatch -n 48 \
    -J process_controlfreec_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,EXCLUDE=${REFDIR}/grch38_decoy.masked.bed,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/process_controlfreec.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/intervals/process_controlfreec.sh
done
echo "End : $(date +"%F_%H-%M-%S")"


echo "### lumpy step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -n 48 \
    -J process_lumpy_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/process_lumpy.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/intervals/process_smoove.sh"

    sbatch -n 48 \
    -J process_lumpy_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/process_lumpy.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/intervals/process_smoove.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

echo "### ControlFreeC formating step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch --partition nompi -n 1 \
    -J format_controlfreec_result_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn process_controlfreec_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam_CNVs,VCFFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.vcf,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/wrapper_format_CNV_ControlFreec.$(date +"%F_%H-%M-%S").log,FILETYPE=controlfreec,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.controlfreec.vcf ${PIPELINEBASE}/common/intervals/wrapper_format_CNV.sh"

    sbatch --partition nompi -n 1 \
    -J format_controlfreec_result_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn process_controlfreec_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam_CNVs,VCFFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.vcf,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/wrapper_format_CNV_ControlFreec.$(date +"%F_%H-%M-%S").log,FILETYPE=controlfreec,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.controlfreec.vcf ${PIPELINEBASE}/common/intervals/wrapper_format_CNV.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

echo "### lumpy formating step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch --partition nompi -n 1 \
    -J format_lumpy_result_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn process_lumpy_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.vcf,VCFFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.vcf,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/wrapper_format_CNV_Lumpy.$(date +"%F_%H-%M-%S").log,FILETYPE=lumpy,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.InvBnd.vcf ${PIPELINEBASE}/common/intervals/wrapper_format_CNV.sh"
    
    sbatch --partition nompi -n 1 \
    -J format_lumpy_result_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn process_lumpy_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.vcf,VCFFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.vcf,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/wrapper_format_CNV_Lumpy.$(date +"%F_%H-%M-%S").log,FILETYPE=lumpy,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.InvBnd.vcf ${PIPELINEBASE}/common/intervals/wrapper_format_CNV.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

echo "### Concatenation and merging step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch --partition nompi -n 1 \
    -J merge_intervals_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn format_controlfreec_result_${currentSample}):$(sqn format_lumpy_result_${currentSample}) \
    --export=LUMPYFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.InvBnd.vcf,CONTROLFREECFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.controlfreec.vcf,DICTFILE=${REFDICT},CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/concamerge.$(date +"%F_%H-%M-%S").log,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.vcf ${PIPELINEBASE}/common/intervals/wrapper_merge_intervals.sh"
    
    sbatch --partition nompi -n 1 \
    -J merge_intervals_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn format_controlfreec_result_${currentSample}):$(sqn format_lumpy_result_${currentSample}) \
    --export=LUMPYFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.lumpy.InvBnd.vcf,CONTROLFREECFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.controlfreec.vcf,DICTFILE=${REFDICT},CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/concamerge.$(date +"%F_%H-%M-%S").log,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.vcf ${PIPELINEBASE}/common/intervals/wrapper_merge_intervals.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

echo "### BED for Intersect step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
	echo "Command : 
    sbatch -n 1 \
    -J bed4Interesect_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn merge_intervals_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.vcf,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/bed4Interesect.$(date +"%F_%H-%M-%S").log,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.intersect.bed ${PIPELINEBASE}/common/SV/wrapper_create_bed4intersect.sh"

    sbatch -n 1 \
    -J bed4Interesect_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn merge_intervals_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.vcf,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/bed4Interesect.$(date +"%F_%H-%M-%S").log,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.intersect.bed ${PIPELINEBASE}/common/SV/wrapper_create_bed4intersect.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

echo "### Intersect step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -n 1 \
    -J ProcessInteresect_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn bed4Interesect_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.intersect.bed,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/intersect.$(date +"%F_%H-%M-%S").log,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.intersect ${PIPELINEBASE}/common/SV/process_intersect.sh"

    sbatch -n 1 \
    -J ProcessInteresect_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn bed4Interesect_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.intersect.bed,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/intersect.$(date +"%F_%H-%M-%S").log,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.intersect ${PIPELINEBASE}/common/SV/process_intersect.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

dependency=""
# sample list
if [ -e "${ANALYSISDIR}/sample.cnv.list" ]
then
    rm ${ANALYSISDIR}/sample.cnv.list
fi
for currentSample in ${samples}
do
    # Construct hold dependency
    dependency=${dependency}:$(sqn merge_intervals_${currentSample})
    # Create a list of cnv file to compare
    echo "${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.vcf" >> ${ANALYSISDIR}/sample.cnv.list
done

# CNV Control sample list
if [ -e ${ANALYSISDIR}/cnvcontrol.list ]
then
   rm ${ANALYSISDIR}/cnvcontrol.list
fi
cnvcontrolfiles=`find ${CNVCONTROLDIR} -maxdepth 1 -mindepth 1 -exec basename {} \;`
for cnvcontrol in ${cnvcontrolfiles}
do
        if grep -q ${cnvcontrol} ${ANALYSISDIR}/sample.cnv.list
        then
       echo "${cnvcontrol} belongs to control dataset"
        else
                echo ${CNVCONTROLDIR}/${cnvcontrol} >> ${ANALYSISDIR}/cnvcontrol.list
        fi
done

echo "Start : $(date +"%F_%H-%M-%S")"
echo "Command : 
sbatch -n 1 \
    -J compare_cnv_${REPDIR} \
    --output ${ANALYSISDIR}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/logs/%x.%J.log \
    --dependency=afterok:${dependency#:} \
    --export=SAMPLELIST=${ANALYSISDIR}/sample.cnv.list,CONTROLLIST=${ANALYSISDIR}/cnvcontrol.list,LENGTH=0,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/logs/compare_c.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/SV/wrapper_compare_c.sh"

sbatch -n 1 \
    -J compare_cnv_${REPDIR} \
    --output ${ANALYSISDIR}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/logs/%x.%J.log \
    --dependency=afterok:${dependency#:} \
    --export=SAMPLELIST=${ANALYSISDIR}/sample.cnv.list,CONTROLLIST=${ANALYSISDIR}/cnvcontrol.list,LENGTH=0,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/logs/compare_c.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/SV/wrapper_compare_c.sh
echo "End : $(date +"%F_%H-%M-%S")"

# CNV/SV NBS filtering
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
	echo "Command : 
    sbatch -n 1 \
    -J filter_varcall_cnv_nbs_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn compare_cnv_${REPDIR}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.count.vcf,GENELIST=${ANALYSISDIR}/${currentSample}/PGC1.interval_list,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.interval_filtered.vcf,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/filter_varcall_cnv_nbs.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/vcf/wrapper_filter_varcall_cnv_nbs.sh"

	sbatch -n 1 \
    -J filter_varcall_cnv_nbs_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn compare_cnv_${REPDIR}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.count.vcf,GENELIST=${ANALYSISDIR}/${currentSample}/PGC1.interval_list,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.interval_filtered.vcf,CONFIGFILE=${CONFIGFILE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/filter_varcall_cnv_nbs.$(date +"%F_%H-%M-%S").log ${PIPELINEBASE}/common/vcf/wrapper_filter_varcall_cnv_nbs.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

echo "### Annotation step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch --partition mpi2 -n 48 \
    -J annotate_cnv_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn filter_varcall_cnv_nbs_${currentSample}):$(sqn ProcessInteresect_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.interval_filtered.vcf,INTERSECTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.intersect,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.annot.vcf,CYTOBANDS=T,REFSEQ=T,OMIM=T,DGV=T,CNVMAP=T,CLINGEN=T,ISCABEN=T,ISCAPATH=T,DDCONTROL=T,DDCASE=T,GNOMAD=T,OVERLAP=0.7,REGULOME=T,BLACKLIST=T,MAPABILITY=T,REPEATMASKER=T,VCF=T,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/annotate_cnv.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE}  ${PIPELINEBASE}/common/SV/wrapper_annotate_cnv.sh"

    sbatch --partition mpi2  -n 48 \
    -J annotate_cnv_${currentSample} \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --dependency=afterok:$(sqn filter_varcall_cnv_nbs_${currentSample}):$(sqn ProcessInteresect_${currentSample}) \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.interval_filtered.vcf,INTERSECTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.raw.cnv.merged.intersect,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.annot.vcf,CYTOBANDS=T,REFSEQ=T,OMIM=T,DGV=T,CNVMAP=T,CLINGEN=T,ISCABEN=T,ISCAPATH=T,DDCONTROL=T,DDCASE=T,GNOMAD=T,OVERLAP=0.7,REGULOME=T,BLACKLIST=T,MAPABILITY=T,REPEATMASKER=T,VCF=T,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/annotate_cnv.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/SV/wrapper_annotate_cnv.sh
done
echo "End : $(date +"%F_%H-%M-%S")"


# Variant filtration regarding SNV inclusion exclusion 
echo "### Variant filtering on SNV ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch -n 1 \
    -J filter_snv_from_list_${currentSample} \
    --dependency=afterok:$(sqn annotate_variants_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.annotate_variants.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.snv_filtered.vcf,EXCLUDEFILE=${PGC1EXCLUDE},INCLUDEFILE=${PGC1INCLUDE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/filter_snv_from_list.${currentSample}.$(date +"%F_%H-%M-%S").log,ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/wrapper_filter_snv_from_list.sh"

    sbatch -n 1 \
    -J filter_snv_from_list_${currentSample} \
    --dependency=afterok:$(sqn annotate_variants_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.annotate_variants.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.snv_filtered.vcf,EXCLUDEFILE=${PGC1EXCLUDE},INCLUDEFILE=${PGC1INCLUDE},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/filter_snv_from_list.${currentSample}.$(date +"%F_%H-%M-%S").log,ANALYSISDIR=${ANALYSISDIR},CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/wrapper_filter_snv_from_list.sh
done
echo "End : $(date +"%F_%H-%M-%S")"



############### QC ##################
# extract bam pgc1 region
echo "### Extract bam ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command :
    sbatch -p mpi2 \
    --ntasks 48 \
    -J extract_bam_regions_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.bam,BEDFILE=${ANALYSISDIR}/${currentSample}/PGC1.bed,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/extract_bam_regions.${logbasename}.log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/bam/extract_bam_regions.sh"

    sbatch -p mpi2 \
    --ntasks 48 \
    -J extract_bam_regions_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.bam,BEDFILE=${ANALYSISDIR}/${currentSample}/PGC1.bed,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/extract_bam_regions.${logbasename}.log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/bam/extract_bam_regions.sh
done 


# collect metrics
echo "### Collect metrics ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command :
    sbatch -p nompi --ntasks 1 \
    -J collect_metrics_${currentSample} \
    --dependency=afterok:$(sqn extract_bam_regions_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.bam,OUTPUTNAME=${ANALYSISDIR}/${currentSample}/QC/${currentSample},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/collect_metrics.${logbasename}.log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/bam/collect_metrics.sh"

    sbatch -p nompi --ntasks 1 \
    -J collect_metrics_${currentSample} \
    --dependency=afterok:$(sqn extract_bam_regions_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.bam,OUTPUTNAME=${ANALYSISDIR}/${currentSample}/QC/${currentSample},LOGFILE=${ANALYSISDIR}/${currentSample}/logs/collect_metrics.${logbasename}.log,CONFIGFILE=${CONFIGFILE} \
    ${PIPELINEBASE}/common/bam/collect_metrics.sh

    holdDependency=$(printf "${holdDependency}:$(sqn collect_metrics_${currentSample})")
done
echo "End : $(date +"%F_%H-%M-%S")"

# process depth of coverage for refseq
echo "### Process depth of coverage for refseq ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command :
    sbatch -p nompi --ntasks 1 \
    -J process_doc_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,TARGET=${ANALYSISDIR}/${currentSample}/PGC1.interval_list,OBO=-omitBaseOutput,DELS=-dels,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.doc.refseq,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/process_doc.${logbasename}.log,CONFIGFILE=${CONFIGFILE},CLUSTER=slurm,ANALYSISTYPE=nbs \
    ${PIPELINEBASE}/common/bam/process_doc.sh"
    
    sbatch -p nompi --ntasks 1 \
    -J process_doc_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,TARGET=${ANALYSISDIR}/${currentSample}/PGC1.interval_list,OBO=-omitBaseOutput,DELS=-dels,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.doc.refseq,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/process_doc.${logbasename}.log,CONFIGFILE=${CONFIGFILE},CLUSTER=slurm,ANALYSISTYPE=nbs \
    ${PIPELINEBASE}/common/bam/process_doc.sh
    
    holdDependency=$(printf "${holdDependency}:$(sqn process_doc_${currentSample})")
done
echo "End : $(date +"%F_%H-%M-%S")"

# process QC summary
echo "### Process QC summary ###"
echo "Start : $(date +"%F_%H-%M-%S")"

holdDependency=${holdDependency#:}

echo "Command :
sbatch -p nompi --ntasks 1 \
-J summarize_QC_${REPDIR} \
--dependency=afterok:${holdDependency} \
--output ${ANALYSISDIR}/logs/%x.%J.out \
--error ${ANALYSISDIR}/logs/%x.%J.log \
--export INPUTDIR=${ANALYSISDIR}/,OUTPUTFILE=${ANALYSISDIR}/QC.summary.tsv,TECHNOLOGY=wgs,LOGFILE=${ANALYSISDIR}/logs/summarize_QC.${logbasename}.log,CONFIGFILE=${CONFIGFILE} \
${PIPELINEBASE}/common/bam/wrapper_summarize_QC.sh"

sbatch -p nompi --ntasks 1 \
-J summarize_QC_${REPDIR} \
--dependency=afterok:${holdDependency} \
--output ${ANALYSISDIR}/logs/%x.%J.out \
--error ${ANALYSISDIR}/logs/%x.%J.log \
--export INPUTDIR=${ANALYSISDIR}/,OUTPUTFILE=${ANALYSISDIR}/QC.summary.tsv,TECHNOLOGY=wgs,LOGFILE=${ANALYSISDIR}/logs/summarize_QC.${logbasename}.log,CONFIGFILE=${CONFIGFILE} \
${PIPELINEBASE}/common/bam/wrapper_summarize_QC.sh

compile_dependency=$(printf "${compile_dependency}:$(sqn summarize_QC_${REPDIR})")
echo "End : $(date +"%F_%H-%M-%S")"

# annotate depth of coverage interval summary output with gene names
echo "### Process depth of coverage interval summary annotation ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command :
    sbatch -p nompi --ntasks 1 \
    -J annotate_sample_interval_summary_${currentSample} \
    --dependency=afterok:$(sqn process_doc_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.doc.refseq.sample_interval_summary,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.doc.refseq.with_genes.sample_interval_summary,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/annotate_sample_interval_summary.${logbasename}.log,CONFIGFILE=${CONFIGFILE} \
    ${PIPELINEBASE}/common/intervals/wrapper_annotate_sample_interval_summary.sh"

    sbatch -p nompi --ntasks 1 \
    -J annotate_sample_interval_summary_${currentSample} \
    --dependency=afterok:$(sqn process_doc_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export INPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.doc.refseq.sample_interval_summary,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.doc.refseq.with_genes.sample_interval_summary,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/annotate_sample_interval_summary.${logbasename}.log,CONFIGFILE=${CONFIGFILE} \
    ${PIPELINEBASE}/common/intervals/wrapper_annotate_sample_interval_summary.sh
done
echo "End : $(date +"%F_%H-%M-%S")"


# process variant calling for SNP identity control
echo "### varcall for SNP identity control ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command :
    sbatch -p nompi -n 1 \
    -J process_varcall_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.identito.raw.g.vcf.gz,TARGET=${IDENTITOSNPVCF},CONFIGFILE=${CONFIGFILE},LOGFILENEW=${ANALYSISDIR}/${currentSample}/logs/process_varcall.$(date +"%F_%H-%M-%S").log \
    ${PIPELINEBASE}/common/vcf/process_varcall.sh"
    
    sbatch -p nompi -n 1 \
    -J process_varcall_${currentSample} \
    --dependency=afterok:$(sqn fq2vcf_gpu_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.identito.raw.g.vcf.gz,TARGET=${IDENTITOSNPVCF},CONFIGFILE=${CONFIGFILE},LOGFILENEW=${ANALYSISDIR}/${currentSample}/logs/process_varcall.$(date +"%F_%H-%M-%S").log \
    ${PIPELINEBASE}/common/vcf/process_varcall.sh
done
echo "End : $(date +"%F_%H-%M-%S")"


# process the GT extraction for SNP identity control
echo "### Process GT extraction for SNP identity control ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
   echo "Command :
     sbatch -p nompi -n 1 \
     -J extract_GT_${currentSample} \
     --dependency=afterok:$(sqn process_varcall_${currentSample}) \
     --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
     --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
     --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.identito.raw.g.vcf.gz,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.CTRL_SNP.GT.tsv,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/extract_GT.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE},SAMPLE=${currentSample},POSLIST=${SNPLIST},TABIX=${TABIXBIN} \
     ${PIPELINEBASE}/common/vcf/wrapper_extract_GT_from_gvcf.sh"
   
     sbatch -p nompi -n 1 \
     -J extract_GT_${currentSample} \
     --dependency=afterok:$(sqn process_varcall_${currentSample}) \
     --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
     --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
     --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.identito.raw.g.vcf.gz,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.CTRL_SNP.GT.tsv,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/extract_GT.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE},SAMPLE=${currentSample},POSLIST=${SNPLIST},TABIX=${TABIXBIN} \
     ${PIPELINEBASE}/common/vcf/wrapper_extract_GT_from_gvcf.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

# check the sex data
echo "### Checking sex ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
   echo "Command :
   sbatch -p nompi -n 1 \
   -J check_sex_${currentSample} \
   --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
   --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
   --dependency=afterok:$(sqn extract_GT_${currentSample}) \
   --export=INFO=${ANALYSISDIR}/${currentSample}/${currentSample}.info,GT=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.CTRL_SNP.GT.tsv,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.sex.report.tsv,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/check_sex.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/check_sex.sh"   
   
   sbatch -p nompi -n 1 \
   -J check_sex_${currentSample} \
   --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
   --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
   --dependency=afterok:$(sqn extract_GT_${currentSample}) \
   --export=INFO=${ANALYSISDIR}/${currentSample}/${currentSample}.info,GT=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.CTRL_SNP.GT.tsv,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.sex.report.tsv,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/check_sex.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/check_sex.sh
done
echo "End : $(date +"%F_%H-%M-%S")"



# NBS variants filtering
echo "### NBS variants filtering step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command : 
    sbatch --partition nompi -n 1 \
    -J nbs_variants_filtering_${currentSample} \
    --dependency=afterok:$(sqn filter_snv_from_list_${currentSample}):$(sqn annotate_cnv_${currentSample}):$(sqn extract_GT__${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.snv_filtered.vcf,SAMPLE=${currentSample},OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.transmission_filtered.vcf,CNVFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.annot.vcf,CNVOUTPUT=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.transmission_filtered.vcf,GENELIST=${ANALYSISDIR}/${currentSample}/PGC1_transmission,INFO=${ANALYSISDIR}/${currentSample}/${currentSample}.info,GT=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.CTRL_SNP.GT.tsv,PASS="--pass",MINDP=5,MINALTDP=3,MINALTFRAC=0.1,FREQGNOMADGE=0.01,MAXLOEUF=0.6,MAXCNVCOUNT=3,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/nbs_variants_filtering.${currentSample}.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/wrapper_nbs_variants_filtering.sh"

    sbatch --partition nompi -n 1 \
    -J nbs_variants_filtering_${currentSample} \
    --dependency=afterok:$(sqn filter_snv_from_list_${currentSample}):$(sqn annotate_cnv_${currentSample}):$(sqn extract_GT__${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.snv_filtered.vcf,SAMPLE=${currentSample},OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.transmission_filtered.vcf,CNVFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.annot.vcf,CNVOUTPUT=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.transmission_filtered.vcf,GENELIST=${ANALYSISDIR}/${currentSample}/PGC1_transmission,INFO=${ANALYSISDIR}/${currentSample}/${currentSample}.info,GT=${ANALYSISDIR}/${currentSample}/QC/${currentSample}.CTRL_SNP.GT.tsv,PASS="--pass",MINDP=5,MINALTDP=3,MINALTFRAC=0.1,FREQGNOMADGE=0.01,MAXLOEUF=0.6,MAXCNVCOUNT=3,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/nbs_variants_filtering.${currentSample}.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/wrapper_nbs_variants_filtering.sh
done
echo "End : $(date +"%F_%H-%M-%S")"


# Report SV/CNV
echo "### Report cnv step ###"
echo "Start : $(date +"%F_%H-%M-%S")"
for currentSample in ${samples}
do
    echo "Command :
    sbatch --partition nompi -n 1 \
    -J report_cnv_${currentSample} \
    --dependency=afterok:$(sqn nbs_variants_filtering_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.transmission_filtered.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.${vcfbasename}.cnv.report.tsv,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/report_cnv.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/SV/wrapper_report_cnv.sh"
    
    sbatch --partition nompi -n 1 \
    -J report_cnv_${currentSample} \
    --dependency=afterok:$(sqn nbs_variants_filtering_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.cnv.transmission_filtered.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.${vcfbasename}.cnv.report.tsv,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/report_cnv.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/SV/wrapper_report_cnv.sh
done
echo "End : $(date +"%F_%H-%M-%S")"

    
# Report SNV
echo "### Report snv step ###"
echo "Start : $(date +"%F_%H-%M-%S")"

for currentSample in ${samples}
do
    echo "Command :    
    sbatch --partition nompi -n 1 \
    -J report_vcf_wgs_${currentSample} \
    --dependency=afterok:$(sqn nbs_variants_filtering_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.transmission_filtered.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.${vcfbasename}.snv.report.tsv,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/report_vcf_wgs.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/wrapper_report_vcf_wgs.sh"
    
    sbatch --partition nompi -n 1 \
    -J report_vcf_wgs_${currentSample} \
    --dependency=afterok:$(sqn nbs_variants_filtering_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.transmission_filtered.vcf,OUTPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.${vcfbasename}.snv.report.tsv,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/report_vcf_wgs.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/wrapper_report_vcf_wgs.sh    
done
echo "End : $(date +"%F_%H-%M-%S")"    
 
echo "### Plot cnv step ###"
echo "Start : $(date +"%F_%H-%M-%S")"

for currentSample in ${samples}
do
    casindex=`basename ${currentSample%%.*}`
    echo "Command :
    sbatch --partition nompi -n 1 \
    -J plot_cnv_${currentSample} \
    --dependency=afterok:$(sqn report_cnv_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.${vcfbasename}.cnv.report.tsv,RATIOFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam_ratio.txt,OUTPUTDIR=${ANALYSISDIR}/${currentSample}/,CASINDEX=${casindex},FRAC=1.,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/plot_cnv_wgs.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} \
    ${PIPELINEBASE}/common/SV/wrapper_plot_cnv_wgs.sh"  
    
    sbatch --partition nompi -n 1 \
    -J plot_cnv_${currentSample} \
    --dependency=afterok:$(sqn report_cnv_${currentSample}) \
    --output ${ANALYSISDIR}/${currentSample}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/${currentSample}/logs/%x.%J.log \
    --export=INPUTFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.pgc1.${vcfbasename}.cnv.report.tsv,RATIOFILE=${ANALYSISDIR}/${currentSample}/${currentSample}.bam_ratio.txt,OUTPUTDIR=${ANALYSISDIR}/${currentSample}/,CASINDEX=${casindex},FRAC=1.,LOGFILE=${ANALYSISDIR}/${currentSample}/logs/plot_cnv_wgs.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} \
    ${PIPELINEBASE}/common/SV/wrapper_plot_cnv_wgs.sh   
    
    compile_dependency=$(printf "${compile_dependency}:$(sqn plot_cnv_${currentSample})")
done
echo "End : $(date +"%F_%H-%M-%S")"    





# uploading QC to labkey

echo "### QC TO LABKEY ###"
echo "Start : $(date +"%F_%H-%M-%S")"
compile_dependency=${compile_dependency#:}
echo "Command : 
sbatch -p nompi -n 1 --requeue \
-J qc_to_labkey_${REPDIR} \
--output ${ANALYSISDIR}/logs/%x.%J.out \
--error ${ANALYSISDIR}/logs/%x.%J.log \
--dependency=afterok:${compile_dependency} \
--export=INPUTDIR=${ANALYSISDIR},LOGFILE=${ANALYSISDIR}/logs/qc_to_labkey.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/wrapper_qc_to_labkey.sh"
   
sbatch -p nompi -n 1 --requeue \
-J qc_to_labkey_${REPDIR} \
--output ${ANALYSISDIR}/logs/%x.%J.out \
--error ${ANALYSISDIR}/logs/%x.%J.log \
--dependency=afterok:${compile_dependency} \
--export=INPUTDIR=${ANALYSISDIR},LOGFILE=${ANALYSISDIR}/logs/qc_to_labkey.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/vcf/wrapper_qc_to_labkey.sh
  
compile_dependency=$(printf "${compile_dependency}:$(sqn qc_to_labkey_${REPDIR})") 
echo "End : $(date +"%F_%H-%M-%S")"



# Get exit code.
echo "### Compiling exit codes ###"
echo "Start : $(date)"


echo "Command :  
sbatch -p nompi -n 1 \
-J get_exit_code_${REPDIR} \
--output ${ANALYSISDIR}/logs/%x.%J.out \
--error ${ANALYSISDIR}/logs/%x.%J.log \
--dependency=afterok:$(sqn qc_to_labkey_${REPDIR}) \
--export=ANALYSISDIR=${ANALYSISDIR},JSON=${PIPELINEBASE}/wgs_pipeline/gs_solo_nbs.json,OUTPUTFILE=${ANALYSISDIR}/status.tsv,LOGFILE=${ANALYSISDIR}/logs/get_exit_code.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/wrapper_get_exit_code.sh"
   
sbatch -p nompi -n 1 \
-J get_exit_code_${REPDIR} \
--output ${ANALYSISDIR}/logs/%x.%J.out \
--error ${ANALYSISDIR}/logs/%x.%J.log \
--dependency=afterok:$(sqn qc_to_labkey_${REPDIR}) \
--export=ANALYSISDIR=${ANALYSISDIR},JSON=${PIPELINEBASE}/wgs_pipeline/gs_solo_nbs.json,OUTPUTFILE=${ANALYSISDIR}/status.tsv,LOGFILE=${ANALYSISDIR}/logs/get_exit_code.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/wrapper_get_exit_code.sh
echo "End : $(date)"


# Archiving data and update labkey rows
if [ "$MODE" = "PROD" ]
then
    echo "### Archiving data and update labkey rows ###"
    echo "Start : $(date +"%F_%H-%M-%S")"

    echo "Command : 
    sbatch -p nompi -n 1 \
    -J upload_labkey_nbs_${REPDIR} \
    --output ${ANALYSISDIR}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/logs/%x.%J.log \
    --dependency=afterok:$(sqn get_exit_code_${REPDIR}) \
    --export ANALYSISDIR=${ANALYSISDIR},LOGFILE=${ANALYSISDIR}/logs/upload_labkey_nbs.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/wrapper_upload_labkey_nbs.sh"
    
    sbatch -p nompi -n 1 \
    -J upload_labkey_nbs_${REPDIR} \
    --output ${ANALYSISDIR}/logs/%x.%J.out \
    --error ${ANALYSISDIR}/logs/%x.%J.log \
    --dependency=afterok:$(sqn get_exit_code_${REPDIR}) \
    --export ANALYSISDIR=${ANALYSISDIR},LOGFILE=${ANALYSISDIR}/logs/upload_labkey_nbs.$(date +"%F_%H-%M-%S").log,CONFIGFILE=${CONFIGFILE} ${PIPELINEBASE}/common/wrapper_upload_labkey_nbs.sh
    
    echo "End : $(date +"%F_%H-%M-%S")"
fi

echo "### END of pipeline execution with success but analysis jobs are still running ###"
echo "END OF PIPELINE : $(date)"
```