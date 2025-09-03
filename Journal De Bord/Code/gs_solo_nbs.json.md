```json
[	
	{
		"name":"gs_solo_nbs",
		"tree":
		{			
			"copy_pgc1":
			{
				"parent": ["None"],
				"logname": "copy_pgc1.$(date).log",
				"sge_name": "copy_pgc1_$(sample)",
				"log_type": "sample"
			}, 
			"run_md5_fastq":
			{
				"parent": ["copy_pgc1"],
				"logname": "run_md5_fastq.$(date).log",
				"sge_name": "run_md5_fastq_$(sample)",
				"log_type": "sample"
			}, 
			"fastq_fp":
			{
				"parent": ["run_md5_fastq"],
				"logname": "process_fastqc.$(date).log",
				"sge_name": "fastqc_FP_$(sample)",
				"log_type": "sample"
			}, 			
			"fq2vcf":
			{
				"parent": ["fastq_fp"],
				"logname": "fq2vcf.$(date).log",
				"sge_name": "fq2vcf_gpu_$(sample)",
				"log_type": "sample"
			}, 				
			"bam_to_cram":
			{
				"parent": ["fq2vcf"],
				"logname": "bam_to_cram.$(date).log",
				"sge_name": "bam_to_cram_$(sample)",
				"log_type": "sample"
			}, 				
			"SMN_caller":
			{
				"parent": ["fq2vcf"],
				"logname": "SMN_caller.$(date).log",
				"sge_name": "SMN_caller_$(sample)",
				"log_type": "sample"
			}, 	
			"filter_varcall_nbs":
			{
				"parent": ["fq2vcf"],
				"logname": "filter_varcall_nbs.$(sample).$(date).log",
				"sge_name": "filter_varcall_nbs_$(sample)",
				"log_type": "sample"
			}, 
			"annotate_variants_snpeff":
			{
				"parent": ["filter_varcall_nbs"],
				"logname": "annotate_variants_snpeff.$(sample).$(date).log",
				"sge_name": "annotate_variants_snpeff_wgs_$(sample)",
				"log_type": "sample"
			}, 
			"annotate_variants_spip":
			{
				"parent": ["annotate_variants_snpeff"],
				"logname": "annotate_variants_spip.$(sample).$(date).log",
				"sge_name": "annotate_variants_spip_$(sample)",
				"log_type": "sample"
			}, 
			"annotate_variants":
			{
				"parent": ["annotate_variants_spip"],
				"logname": "annotate_variants.$(sample).$(date).log",
				"sge_name": "annotate_variants_$(sample)",
				"log_type": "sample"
			}, 		
			"process_controlfreec":
			{
				"parent": ["fq2vcf"],
				"logname": "process_controlfreec.$(date).log",
				"sge_name": "process_controlfreec_$(sample)",
				"log_type": "sample"
			}, 
			"process_lumpy":
			{
				"parent": ["fq2vcf"],
				"logname": "process_lumpy.$(date).log",
				"sge_name": "process_lumpy_$(sample)",
				"log_type": "sample"
			}, 
			"format_controlfreec":
			{
				"parent": ["process_controlfreec", "process_lumpy"],
				"logname": "wrapper_format_CNV_ControlFreec.$(date).log",
				"sge_name": "format_controlfreec_result_$(sample)",
				"log_type": "sample"
			}, 
			"format_lumpy":
			{
				"parent": ["process_controlfreec", "process_lumpy"],
				"logname": "wrapper_format_CNV_Lumpy.$(date).log",
				"sge_name": "format_lumpy_result_$(sample)",
				"log_type": "sample"
			}, 
 			"merge_intervals":
			{
				"parent": ["format_controlfreec", "format_lumpy"],
				"logname": "concamerge.$(date).log",
				"sge_name": "merge_intervals_$(sample)",
				"log_type": "sample"
			}, 
			"bed4Interesect":
			{
				"parent":["merge_intervals"],
				"logname": "bed4Interesect.$(date).log",
				"sge_name": "bed4Interesect_$(sample)",
				"log_type": "sample"
			},	 
 			"process_interesect":
			{
				"parent":["bed4Interesect"],
				"logname": "intersect.$(date).log",
				"sge_name": "ProcessInteresect_$(sample)",
				"log_type": "sample"
			},	
			"compare_cnv":
			{
				"parent":["merge_intervals"],
				"logname": "compare_c.$(date).log",
				"sge_name": "compare_cnv_$(directory)",
				"log_type": "general"
			},
			"filter_varcall_cnv_nbs":
			{
				"parent":["compare_cnv"],
				"logname": "filter_varcall_cnv_nbs.$(date).log",
				"sge_name": "filter_varcall_cnv_nbs_$(directory)",
				"log_type": "sample"
			},
			"annotate_cnv":
			{
				"parent":["filter_varcall_cnv_nbs", "process_interesect"],
				"logname": "annotate_cnv.$(date).log",
				"sge_name": "annotate_cnv_$(sample)",
				"log_type": "sample"
			},			
			"filter_snv_from_list":
			{
				"parent":["annotate_variants"],
				"logname": "filter_snv_from_list.$(sample).$(date).log",
				"sge_name": "filter_snv_from_list_$(sample)",
				"log_type": "sample"
			},			
			"nbs_variants_filtering":
			{
				"parent":["filter_snv_from_list","annotate_cnv"],
				"logname": "nbs_variants_filtering.$(sample).$(date).log",
				"sge_name": "nbs_variants_filtering_$(sample)",
				"log_type": "sample"
			},				
			"report_snv":
			{
				"parent":["nbs_variants_filtering"],
				"logname": "report_vcf_wgs.$(date).log",
				"sge_name": "report_vcf_wgs.$(sample)",
				"log_type": "sample"
			},
			"report_cnv":
			{
				"parent":["nbs_variants_filtering"],
				"logname": "report_cnv.$(date).log",
				"sge_name": "report_cnv_$(sample)",
				"log_type": "sample"
			},
			"plot_cnv":
			{
				"parent":["report_cnv"],
				"logname": "plot_cnv_wgs.$(date).log",
				"sge_name": "plot_cnv_$(sample)",
				"log_type": "sample"
			},
			"extract_bam_regions":
			{
				"parent":["fq2vcf"],
				"logname": "extract_bam_regions.$(date).log",
				"sge_name": "extract_bam_regions_$(sample)",
				"log_type": "sample"
			},
			"collect_metrics":
			{
				"parent":["extract_bam_regions"],
				"logname": "collect_metrics.$(date).log",
				"sge_name": "collect_metrics_$(sample)",
				"log_type": "sample"
			},
			"process_doc":
			{
				"parent":["fq2vcf"],
				"logname": "process_doc.$(date).log",
				"sge_name": "process_doc_$(sample)",
				"log_type": "sample"
			},
			"summarize_QC":
			{
				"parent":["collect_metrics","process_doc"],
				"logname": "summarize_QC.$(date).log",
				"sge_name": "summarize_QC_$(directory)",
				"log_type": "general"
			},		
			"annotate_sample_interval_summary":
			{
				"parent":["summarize_QC"],
				"logname": "annotate_sample_interval_summary.$(date).log",
				"sge_name": "annotate_sample_interval_summary_$(sample)",
				"log_type": "sample"
			},		
			"process_varcall":
			{
				"parent":["fq2vcf"],
				"logname": "process_varcall.$(date).log",
				"sge_name": "process_varcall_$(sample)",
				"log_type": "sample"
			},			
			"extract_GT":
			{
				"parent":["process_varcall"],
				"logname": "extract_GT.$(date).log",
				"sge_name": "extract_GT_$(sample)",
				"log_type": "sample"
			},
			"check_sex":
			{
				"parent":["extract_GT"],
				"logname": "check_sex.$(date).log",
				"sge_name": "check_sex_$(sample)",
				"log_type": "sample"
			},
			"qc_to_labkey":
			{
				"parent":["summarize_QC", "plot_cnv"],
				"logname": "qc_to_labkey.$(date).log",
				"sge_name": "qc_to_labkey_$(directory)",
				"log_type": "general"
			}
		}
	}
]
```