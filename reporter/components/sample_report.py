import dash_html_components as html
import dash_core_components as dcc
import dash_table as dt
from components.images import list_of_images
from components.table import html_table, html_td_percentage
import components.import_data as import_data
import components.global_vars as global_vars
import components.admin as admin
import plotly.graph_objs as go
import pandas as pd
import math
import json

def check_test(test_name, sample):
    test_path = "properties.stamper.summary." + test_name
    if test_path not in sample or pd.isnull(sample[test_path]):
        return "" # show nothing
        #return "test-missing"
    if sample.get(test_path, "").startswith("pass"):
        return "test-pass"
    elif sample.get(test_path, "").startswith("fail"):
        return "test-fail"
    else:
        return "test-warning"

def get_species_img(sample_data):
    genus = str(sample_data.get("whats_my_species.name_classified_species_1")).split()[
        0].lower()
    if "{}.svg".format(genus) in list_of_images:
        img = html.Img(
            src="/assets/img/" + genus + ".svg",
            className="svg_bact"
        )
    else:
        img = None
    return img


def generate_sample_report(sample, n_sample, reporter_json):
    img = get_species_img(sample)
    if img is not None:
        img_div = html.Div(img, className="box-title bact grey-border")
    else:
        img_div = None
    return (
        html.Div(
            [
                html.A(id="sample-" + sample["name"]),
                html.H5(
                    sample["name"],
                    className="box-title"
                ),
                img_div,
                html_sample_tables(sample, reporter_json, className="row"),
                admin.sample_radio_feedback(sample, n_sample)
            ],
            className="border-box"
        )
    )


def html_species_report(dataframe, species, row_index, reporter_json, **kwargs):
    report = []
    for index, sample in \
            dataframe.loc[dataframe["properties.species_detection.summary.species"] == species].iterrows():
        report.append(generate_sample_report(sample,
                                             row_index, reporter_json[sample["_id"]]))
        row_index += 1
    return (html.Div(report, **kwargs), row_index)


def html_organisms_table(sample_data, **kwargs):
    percentages = [
        sample_data.get(
            "properties.species_detection.summary.percent_classified_species_1", math.nan),
        sample_data.get(
            "properties.species_detection.summary.percent_classified_species_2", math.nan),
        sample_data.get(
            "properties.species_detection.summary.percent_unclassified", math.nan)
    ]

    color_0 = "#b3ccc1"
    color_1 = "#b3ccc1" #Green

    color_2 = "#f3bbd3"  # Default

#   color_u = COLOR_DICT.get("", "#fee1cd")  # Default
    color_u = "#fee1cd"  # Default

    return html.Div([
        html.Table([
            html.Tr([
                html.Td(
                    [html.I(sample_data.get("properties.species_detection.summary.name_classified_species_1", "No data")), " + Unclassified"], className="cell"),
                html_td_percentage(percentages[0] + percentages[2], color_0)
            ], className=check_test("test__species_detection__main_species_level", sample_data) + " trow"),
            html.Tr([
                html.Td(
                    html.I(sample_data.get("properties.species_detection.summary.name_classified_species_1", "No data")), className="cell"),
                html_td_percentage(percentages[0], color_1)
            ], className="trow"),
            html.Tr([
                html.Td(
                    html.I(sample_data.get("properties.species_detection.summary.name_classified_species_2", "No data")), className="cell"),
                html_td_percentage(percentages[1], color_2)
            ], className="trow"),
            html.Tr([
                html.Td("Unclassified", className="cell"),
                html_td_percentage(percentages[2], color_u)
            ], className=check_test("test__species_detection__unclassified_level", sample_data) + " trow")
        ])
    ], **kwargs)

def html_test_tables(sample_data, **kwargs):
    stamps_to_check = ["ssi_stamper", "supplying_lab_check"]
    rows = []
    for key, value in sample_data.items():
        if key.startswith("properties.stamper.whats_my_species") \
                or key.startswith("properties.stamper.assemblatron"):
            if pd.isnull(value):
                value = "nan"
            name_v = key.split(":")
            values = value.split(':')
            if len(values) == 3:
                if values[0] != "pass":
                    rows.append([name_v[1].capitalize(), values[1]])
            if (key.endswith(".action")):
                rows.append(["QC Action", value])

    stamp_rows = []
    for stamp in stamps_to_check:
        stamp_key = "stamps.{}.value".format(stamp)
        if stamp_key in sample_data and not pd.isnull(sample_data[stamp_key]):
            if str(sample_data[stamp_key]).startswith("pass"):
                stamp_class = "test-pass"
            elif str(sample_data[stamp_key]).startswith("fail"):
                stamp_class = "test-fail"
            else:
                stamp_class = ""
            stamp_rows.append({
                "list": [stamp, sample_data[stamp_key]],
                "className": stamp_class
            })

    if len(rows):
        test_table = html_table(rows)
    else:
        test_table = html.P("No failed tests.")
    
    if len(stamp_rows):
        stamp_table = html_table(stamp_rows)
    else:
        stamp_table = html.P("No stamps.")

    return html.Div([
        html.Div([
            html.H6("QC stamps", className="table-header"),
            stamp_table
        ], className="six columns"),
        html.Div([
            html.H6("Failed QC tests", className="table-header"),
            test_table
        ], className="six columns"),
    ], **kwargs)

def html_sample_tables(sample_data, reporter_json, **kwargs):
    """Generate the tables for each sample containing submitter information,
       detected organisms etc. """

    if "sample_sheet.sample_name" in sample_data:
        if "sample_sheet.emails" in sample_data and type(sample_data["sample_sheet.emails"]) is str:
            n_emails = len(sample_data["sample_sheet.emails"].split(";"))
            if (n_emails > 1):
                emails = ", ".join(
                    sample_data["sample_sheet.emails"].split(";")[:2])
                if (n_emails > 2):
                    emails += ", ..."
            else:
                emails = sample_data["sample_sheet.emails"]
        else:
            emails = ""
        sample_sheet_table = html_table([
                    ["Supplied name", sample_data.get("sample_sheet.sample_name","")],
                    ["User Comments", sample_data.get("sample_sheet.Comments","")],
                    ["Supplying lab", sample_data.get("sample_sheet.group", "")],
                    ["Submitter emails", emails],
                    {
                        "list": ["Provided species", html.I(
                            sample_data.get("sample_sheet.provided_species"))],
                        "className": check_test("whats_my_species:detectedspeciesmismatch", sample_data)
                    },
                    {
                        "list": ["Read file", 
                            str(sample_data["reads.R1"]).split("/")[-1]],
                        "className": check_test("base:readspresent", sample_data)
                    }
                ])
    else:
        sample_sheet_table = html_table([])

    title = "Assemblatron Results"
    table = html.Div([
        html_table([
            {
                "list": [
                    "Number of filtered reads",
                    "{:,.0f}".format(
                        sample_data.get("properties.denovo_assembly.summary.filtered_reads_num", math.nan))
                ],
                "className": check_test("test__denovo_assembly__minimum_read_number", sample_data)
            },
            [
                "Number of contigs (1x cov.)",
                "{:,.0f}".format(
                    sample_data.get("properties.denovo_assembly.summary.bin_contigs_at_1x", math.nan))
            ],
            [
                "Number of contigs (10x cov.)",
                "{:,.0f}".format(
                    sample_data.get("properties.denovo_assembly.summary.bin_contigs_at_10x", math.nan))
            ],
            [
                "N50",
                "{:,}".format(sample_data.get(
                    "properties.denovo_assembly.summary.N50", math.nan))
            ],
            {
                "list": [
                    "Average coverage (1x)",
                    "{:,.2f}".format(
                        sample_data.get("properties.denovo_assembly.summary.bin_coverage_at_1x", math.nan))
                ],
                "className": check_test("test__denovo_assembly__genome_average_coverage", sample_data)
            },
            {
                "list": [
                    "Genome size at 1x depth",
                    "{:,.0f}".format(
                        sample_data.get("properties.denovo_assembly.summary.bin_length_at_1x", math.nan))
                ],
                "className": check_test("test__denovo_assembly__genome_size_at_1x", sample_data)
            },
            {
                "list": [
                    "Genome size at 10x depth",
                    "{:,.0f}".format(
                        sample_data.get("properties.denovo_assembly.summary.bin_length_at_10x", math.nan))
                ],
                "className": check_test("test__denovo_assembly__genome_size_at_10x", sample_data)
            },
            {
                "list": [
                    "Genome size 1x - 10x diff",
                    "{:,.0f}".format(
                        sample_data.get(
                            "properties.denovo_assembly.summary.bin_length_at_1x", math.nan)
                        - sample_data.get("properties.denovo_assembly.summary.bin_length_at_10x", math.nan)
                    )
                ],
                "className": check_test("test__denovo_assembly__genome_size_difference_1x_10x", sample_data)
            },
            [
                "Genome size at 25x depth",
                "{:,.0f}".format(
                    sample_data.get("properties.denovo_assembly.summary.bin_length_at_25x", math.nan))
            ],
            [
                "Ambiguous sites",
                "{:,.0f}".format(
                    sample_data.get("properties.denovo_assembly.summary.snp_filter_10x_10%", math.nan))
            ] 
        ])
    ])
    expected_results = global_vars.expected_results
    any_results = False
    results = []
    for entry in expected_results:
        if entry in reporter_json:
            any_results = True
            results.append(html.Div([
                html.H6(reporter_json[entry]["title"], className="table-header"),
                html.Div(
                    dt.DataTable(
                        style_table={
                            'overflowX': 'scroll',
                            'overflowY': 'scroll',
                            'maxHeight': '480'
                        },

                        columns=reporter_json[entry]["columns"],
                        data=reporter_json[entry]["data"],
                        page_action='none'
                    ), className="grey-border")
            ], className="six columns"))
        else:
            results.append(html.Div([
                html.H6("{} not run".format(entry.capitalize()), className="table-header")
            ], className="six columns"))


    # mlst_db = sample_data.get("ariba_mlst.mlst_db", "")

    # Replace with the ariba_res, ariba_plas and ariba_vir when migrating to them
    if (sample_data.get("ariba_resfinder.status", "") == "Success" or
        sample_data.get("ariba_plasmidfinder.status", "") == "Success" or
        sample_data.get("ariba_mlst.status", "") == "Success" or
        sample_data.get("ariba_virulencefinder.status", "") == "Success"):
        res_analysis_not_run = False
    else:
        res_analysis_not_run = True

    if any_results:
        res_div = html.Details([
            html.Summary("ResFinder/PlasmidFinder/VirulenceFinder/MLST (click to show)"),
            html.Div([
                html.Div(results, className="row"),
            ])
        ])
    else:
        res_div = html.Div(
            html.P("Resfinder, plasmidfinder, MLST and virulencefinder were not run."))

    mlst_type = "ND"
    if "ariba_mlst.mlst_report" in sample_data and sample_data["ariba_mlst.mlst_report"] is not None:
        mlst_report_string = sample_data["ariba_mlst.mlst_report"]
        if "," in mlst_report_string:
            mlst_text_split = mlst_report_string.split(",", 1)
            mlst_type = mlst_text_split[0].split(":",1)[1]


    return html.Div([
        html.Div([
            html.Div([
                html.H6("Sample Sheet", className="table-header"),
                sample_sheet_table,
                html.H6("Detected Organisms", className="table-header"),
                html_organisms_table(sample_data)
            ], className="six columns"),
            html.Div([
                html.H6(title, className="table-header"),
                table,
                html.H6("MLST type: {}".format(mlst_type), className="table-header"),
            ], className="six columns")
        ], className="row"),
        html_test_tables(sample_data, className="row"),
        res_div
    ], **kwargs)


def children_sample_list_report(filtered_df, reporter_json):
    report = []
    result_index = 0
    for species in filtered_df["properties.species_detection.summary.species"].unique():
        species_report_div, result_index = html_species_report(
            filtered_df, species, result_index, reporter_json)
        report.append(html.Div([
            html.A(id="species-cat-" + str(species).replace(" ", "-")),
            html.H4(html.I(str(species))),
            species_report_div
        ]))
    return report

def generate_sample_folder(sample_ids):
    """Generates a script string """
    samples = import_data.get_samples(sample_ids)
    # Access samples by their id
    samples_by_ids = { str(s["_id"]) : s for s in samples }
    assemblies = import_data.get_assemblies_paths(sample_ids)
    reads_script = "mkdir samples\ncd samples\n"
    assemblies_script = "mkdir assemblies\ncd assemblies\n"
    reads_errors = []
    assemblies_errors = []
    for assembly in assemblies:
        sample = samples_by_ids[str(assembly["sample"]["_id"])]
        try:
            assemblies_script += "#{}\nln -s {} {}\n".format(
                sample["name"],
                assembly["path"] + "/contigs.fasta",
                sample["name"] + "_contigs.fasta")
        except KeyError as e:
            assemblies_errors.append("Missing data for sample: {} - {}. In database:\n{}".format(
                sample.get("name", "None"),
                assembly["_id"],
                assembly.get("path", "No data")
            ))
    
    if len(assemblies_errors):
        assemblies_html = [
            html.H5(
                "Use this script to generate a folder with all the assemblies linked in it."),
            "A few errors occurred locating the contigs. If you need more info, " +
            "please contact an admin.",
            html.Pre("\n".join(assemblies_errors), className="error-pre"),
            html.Pre(assemblies_script, className="folder-pre")
        ]
    else:
        assemblies_html = [
            html.H5(
                "Use this script to generate a folder with all the assemblies linked in it."),
            html.Pre(assemblies_script, className="folder-pre")
        ]

    for sample in samples:
        try:
            reads_script += "#{}\nln -s {} .\nln -s {} .\n".format(
                sample["name"],
                sample["reads"]["R1"],
                sample["reads"]["R2"])
        except KeyError as e:
            reads_errors.append("Missing data for sample: {} - {}. In database:\n{}".format(
                sample.get("name", "None"),
                sample["_id"],
                sample.get("reads", "No data")
                ))
    if len(reads_errors):
        reads_html = [
            html.H5("Use this script to generate a folder with all the sample reads linked in it."),
            "A few errors occurred locating the read paths. If you need more info, " +
            "please contact an admin.",
            html.Pre("\n".join(reads_errors), className="error-pre"),
            html.Pre(reads_script, className="folder-pre")
        ]
    else:
        reads_html = [
            html.H5("Use this script to generate a folder with all the sample reads linked in it."),
            html.Pre(reads_script, className="folder-pre")
            ]
    return html.Div([html.Div(assemblies_html), html.Div(reads_html)])

