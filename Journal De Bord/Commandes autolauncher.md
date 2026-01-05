Supprimer le `-v -t` en prod (-v : verbose, -t : test, config de dev)
- concat
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif  -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/tests/concat --concat
```
- organize
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/incoming/organize/dijen2201 --organize
```
- infofile
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/test_infofile --infofile
```
- analysis 
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/tests/analyse --analysis
```
- check
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/tests/analyse --check
```

Déplacé :
/work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif

[umw040ir@login-1 quark]$ ls

[[2025-11-18]] : ajout de `pipeline_test`
- organize
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/pipeline_test/incoming --organize
```
- infofile
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/test_infofile --infofile
```
- analysis 
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/tests/analyse --analysis
```
- check
```bash
/soft/spack/opt/spack/linux-rocky8-skylake_avx512/gcc-13.1.0/singularityce-3.11.3-7ovyljuvwvlt642r2xkfvht6kivarhkl/bin/singularity run -e --bind /work/ /work/work/shared/s-neomics/soft/singularity_images/python/quark_autolauncher.sif -t -v -d /work/work/shared/s-neomics/data/sandbox/quark/tests/analyse --check
```