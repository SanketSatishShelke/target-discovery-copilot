// Open Targets — fetch disease-target association scores
// Dataset: association_overall_direct (direct target-disease associations)
// Docs: https://platform.opentargets.org/downloads

params.ot_version  = "26.03"
params.output_dir  = "/mnt/data/target-discovery-copilot/raw/open_targets"
params.filename    = "part-00000-938e9416-f471-4b70-ad7a-2bf763e65ff4-c000.snappy.parquet"
params.base_url    = "http://ftp.ebi.ac.uk/pub/databases/opentargets/platform/${params.ot_version}/output/association_overall_direct"

process FETCH_ASSOCIATIONS {
    publishDir params.output_dir, mode: 'copy'

    output:
    path "*.parquet"

    script:
    """
    wget -q --show-progress \
        "${params.base_url}/${params.filename}" \
        -O "${params.filename}"
    """
}

process VALIDATE_FILE {
    input:
    path parquet_file

    output:
    path parquet_file

    script:
    """
    echo "Validating: ${parquet_file}"
    [ -s "${parquet_file}" ] && echo "OK: file is non-empty" || (echo "FAIL: file is empty or missing" && exit 1)
    """
}

workflow {
    FETCH_ASSOCIATIONS()
    VALIDATE_FILE(FETCH_ASSOCIATIONS.out)
}