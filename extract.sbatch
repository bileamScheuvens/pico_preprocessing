#!/bin/bash

#SBATCH -J extract_pico # Job name
#SBATCH --ntasks=1                 # Number of tasks
#SBATCH --cpus-per-task=16          # Number of CPU cores per task
#SBATCH --nodes=1                  # Ensure that all cores are on the same machine with nodes=1
#SBATCH --partition=cpu-galvani   # Which partition will run your job
#SBATCH --time=3-00:00             # Allowed runtime in D-HH:MM
#SBATCH --gres=gpu:0               # (optional) Requesting type and number of GPUs
#SBATCH --mem=20G                  # Total memory pool for all cores (see also --mem-per-cpu); exceeding this number will cause your job to fail.
#SBATCH --output=logs/extract-%j.out       # File to which STDOUT will be written - make sure this is not on $HOME
#SBATCH --error=logs/extract-%j.err        # File to which STDERR will be written - make sure this is not on $HOME
#SBATCH --mail-type=ALL            # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=bileam.scheuvens@student.uni-tuebingen.de   # Email to which notifications will be sent

# Diagnostic and Analysis Phase - please leave these in.
scontrol show job $SLURM_JOB_ID
pwd

# Setup Phase
# add possibly other setup code here, e.g.
# - copy singularity images or datasets to local on-compute-node storage like /scratch_local
# - loads virtual envs, like with anaconda
# - set environment variables
# - determine commandline arguments for `srun` calls

# Compute Phase

cd "$SLURM_SUBMIT_DIR"

set -a
source .env
set +a
source .venv/bin/activate

srun python extract_pico.py
